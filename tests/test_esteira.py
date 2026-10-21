# -*- coding: utf-8 -*-
"""Testes da esteira (etapa 3): leitura com a API (simulada), montagem do JSON, ficha e devolução ao Airtable.
Rodar: python3 -m unittest discover -s tests"""
import contextlib
import copy
import datetime as dt
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

RAIZ = Path(__file__).resolve().parents[1]
for p in ("esteira", "gerador", "skills/sasi-ingest-export/scripts"):
    sys.path.insert(0, str(RAIZ / p))
import build_passagem as motor  # noqa: E402
import leitura  # noqa: E402
import montar  # noqa: E402
import validar  # noqa: E402

LEITURAS = json.loads((RAIZ / "tests" / "fixtures" / "leitura-ficticia.json").read_text(encoding="utf-8"))
LABS = {"identificacao": dict(LEITURAS["prescricao"]["identificacao"]), "pendencias": [],
        "exames": [{"sigla": "HB", "valor": "10,8"}, {"sigla": "LEUCO", "valor": "18.400"},
                   {"sigla": "CR", "valor": "1,7"}, {"sigla": "K", "valor": "4,8"}, {"sigla": "LACTATO", "valor": "3,1"}]}
CONTEXTO = {"turno": "diurno", "hoje": dt.date(2026, 1, 1)}
TEM_PDF = bool(shutil.which("soffice") and shutil.which("pdfinfo") and shutil.which("pdftoppm"))
TEM_POPPLER = bool(shutil.which("pdfinfo") and shutil.which("pdftoppm") and shutil.which("pdftotext"))


def leituras(mudar=None):
    d = copy.deepcopy(LEITURAS)
    d["labs"] = copy.deepcopy(LABS)
    if mudar:
        mudar(d)
    return d


def pdf_minimo(caminho, paginas=1):
    """PDF de páginas A4 em branco (a API é simulada: o conteúdo da imagem não importa)."""
    objs = ["<< /Type /Catalog /Pages 2 0 R >>",
            f"<< /Type /Pages /Kids [{' '.join(f'{3 + i} 0 R' for i in range(paginas))}] /Count {paginas} >>"]
    objs += ["<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] >>"] * paginas
    out, offs = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += f"{i} 0 obj\n{o}\nendobj\n".encode()
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += "".join(f"{o:010d} 00000 n \n" for o in offs).encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    Path(caminho).write_bytes(out)
    return Path(caminho)


def mensagem(dados=None, stop="end_turn", content=None, detalhe=None):
    blocos = content if content is not None else [SimpleNamespace(type="thinking"),
                                                  SimpleNamespace(type="text", text=json.dumps(dados))]
    return SimpleNamespace(stop_reason=stop, content=blocos, stop_details=detalhe)


class ClienteFalso:
    """Imita client.beta.messages.stream(...): responde pelo schema pedido e guarda os pedidos."""

    def __init__(self, respostas):
        self.respostas, self.pedidos = respostas, []
        self.beta = SimpleNamespace(messages=self)

    def stream(self, **kw):
        self.pedidos.append(kw)
        tipo = next(t for t, s in leitura.SCHEMA.items() if s is kw["output_config"]["format"]["schema"])
        resp = self.respostas[tipo]
        if isinstance(resp, Exception):
            raise resp
        if isinstance(resp, dict):
            resp = mensagem(resp)

        @contextlib.contextmanager
        def ctx():
            yield SimpleNamespace(get_final_message=lambda: resp, request_id="req_teste")
        return ctx()


def paginas_falsas(tmp, n, por_pagina=3):
    img = Path(tmp) / "x.jpg"
    img.write_bytes(b"\xff\xd8\xff\xe0jpeg")
    return [(p, [img] * por_pagina) for p in range(1, n + 1)]


# ── leitura.py ──────────────────────────────────────────────────────────────────────────────────────────────
class Schema(unittest.TestCase):
    def test_todo_objeto_fechado_e_toda_chave_obrigatoria(self):
        def andar(no, onde):
            if isinstance(no, dict):
                self.assertFalse({"minimum", "maximum", "minLength", "maxLength", "minItems"} & set(no), onde)
                self.assertNotIn("anyOf", no, onde)  # a API limita os campos de tipo união por pedido
                self.assertNotEqual(no.get("type"), "null", onde)
                if no.get("type") == "object":
                    self.assertIs(no.get("additionalProperties"), False, onde)
                    self.assertEqual(sorted(no["required"]), sorted(no["properties"]), onde)
                for k, v in no.items():
                    andar(v, f"{onde}.{k}")
            elif isinstance(no, list):
                for i, v in enumerate(no):
                    andar(v, f"{onde}[{i}]")
        for tipo, s in leitura.SCHEMA.items():
            andar(s, tipo)

    def test_colunas_da_folha_caem_no_lado_certo_do_motor(self):
        self.assertEqual(set(montar.COLUNA), set(leitura.COLUNAS))
        for coluna, (canon, lado) in montar.COLUNA.items():
            if canon:
                self.assertEqual(motor.classify(canon), lado[:-1], coluna)

    def test_doutrina_e_o_trecho_entre_as_linhas(self):
        d = leitura.doutrina()
        self.assertTrue(d.startswith("Você transcreve documentos de UTI adulto"))
        self.assertNotIn("Tudo que vier entre as linhas", d)


class Chamada(unittest.TestCase):
    def test_pedido(self):
        with tempfile.TemporaryDirectory() as tmp:
            cli = ClienteFalso({"prescricao": LEITURAS["prescricao"]})
            dados, rid = leitura.ler(cli, "prescricao", paginas_falsas(tmp, 2))
        self.assertEqual(dados, LEITURAS["prescricao"])
        self.assertEqual(rid, "req_teste")
        kw = cli.pedidos[0]
        self.assertEqual(kw["model"], "claude-opus-5-5")
        self.assertEqual((kw["betas"], kw["fallbacks"], kw["max_tokens"]),
                         (["server-side-fallback-2026-07-01"], "default", 64000))
        self.assertEqual(kw["output_config"]["effort"], "high")
        self.assertEqual(kw["output_config"]["format"]["type"], "json_schema")
        self.assertEqual(kw["system"], leitura.doutrina())
        imagens = [b for b in kw["messages"][0]["content"] if b["type"] == "image"]
        self.assertEqual(len(imagens), 6)
        self.assertEqual(imagens[0]["source"]["media_type"], "image/jpeg")
        self.assertNotIn("thinking", kw)  # sempre ligado no modelo; mandar "disabled" dá 400

    def test_argumentos_existem_no_sdk(self):
        try:
            import anthropic
        except ImportError:
            self.skipTest("SDK anthropic não instalado")
        import inspect
        aceitos = inspect.signature(anthropic.resources.beta.messages.Messages.stream).parameters
        for k in ("model", "max_tokens", "betas", "fallbacks", "system", "output_config", "messages"):
            self.assertIn(k, aceitos)

    def test_recusa_e_corte_viram_falha(self):
        for msg, trecho in ((mensagem(stop="refusal", content=[], detalhe=SimpleNamespace(category="bio")), "(bio)"),
                            (mensagem(stop="refusal", content=[]), "recusa"),
                            (mensagem({"x": 1}, stop="max_tokens"), "max_tokens")):
            with self.assertRaises(leitura.LeituraFalhou) as c:
                leitura.resposta(msg)
            self.assertIn(trecho, str(c.exception))

    def test_com_fallback_vale_o_texto_depois_do_ultimo_bloco_fallback(self):
        msg = mensagem(content=[SimpleNamespace(type="thinking"), SimpleNamespace(type="text", text='{"parcial'),
                                SimpleNamespace(type="fallback"), SimpleNamespace(type="text", text='{"ok": 1}')])
        self.assertEqual(leitura.resposta(msg), {"ok": 1})

    def test_fallback_no_meio_continua_o_texto_parcial(self):
        msg = mensagem(content=[SimpleNamespace(type="text", text='{"leito": "0'), SimpleNamespace(type="fallback"),
                                SimpleNamespace(type="thinking"), SimpleNamespace(type="text", text='7", "ok": 1}')])
        self.assertEqual(leitura.resposta(msg), {"leito": "07", "ok": 1})
        with self.assertRaises(leitura.LeituraFalhou):
            leitura.resposta(mensagem(content=[SimpleNamespace(type="fallback"),
                                               SimpleNamespace(type="text", text='{"cortado')]))

    def test_erro_da_api_vira_falha(self):
        erro = RuntimeError("sobrecarga"); erro.status_code = 529
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(leitura.LeituraFalhou) as c:
                leitura.ler(ClienteFalso({"labs": erro}), "labs", paginas_falsas(tmp, 1))
        self.assertIn("RuntimeError 529", str(c.exception))

    def test_mais_de_20_imagens(self):
        with tempfile.TemporaryDirectory() as tmp:
            blocos = leitura.conteudo(paginas_falsas(tmp, 7), "prescricao")  # 21 → sem as visões gerais
            self.assertEqual(sum(b["type"] == "image" for b in blocos), 14)
            with self.assertRaises(leitura.LeituraFalhou):
                leitura.conteudo(paginas_falsas(tmp, 11), "prescricao")

    def test_sem_chave_nao_ha_cliente(self):
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": " "}):
            self.assertIsNone(leitura.cliente())


# ── montar.py ───────────────────────────────────────────────────────────────────────────────────────────────
class Montar(unittest.TestCase):
    def montado(self, mudar=None, **contexto):
        pl, erros = montar.montar(leituras(mudar), dict(CONTEXTO, **contexto))
        return pl, pl["leitos"][0], erros

    def test_fixture_passa_no_validar(self):
        pl, l, erros = self.montado()
        self.assertEqual(erros, [])
        prep, _ = motor.preparar(pl)
        e, _ = validar.validar(prep)
        self.assertEqual(e, [])
        self.assertEqual(pl["meta"], {"unidade": "UTI 2", "data": "01/01/2026", "turno": "diurno", "janela": "24 h",
                                      "data_prescricao": "01/01"})
        self.assertEqual((l["leito"], l["idade_sexo"], l["dia_uti"]), ("07", "68M", "D? UTI"))

    def test_vazio_vale_como_ausente(self):
        def vazio(no):
            if isinstance(no, dict):
                return {k: ("" if v is None else vazio(v)) for k, v in no.items()}
            return [vazio(v) for v in no] if isinstance(no, list) else no
        pl, erros = montar.montar(vazio(leituras()), dict(CONTEXTO))
        self.assertEqual((pl, erros), montar.montar(leituras(), dict(CONTEXTO)))

    def test_conta_e_do_motor(self):
        pl, l, _ = self.montado()
        txt, avisos = motor.build(pl)
        self.assertIn("Ingesta hídrica: 836 ml", txt)  # 12 × 50 + 12 × 3 + 2 × 100
        self.assertIn("Diurese: 720 ml", txt)  # dreno (penrose) não entra na diurese
        self.assertIn("Dreno penrose: 20 ml", txt)
        self.assertTrue(any("CONFERÊNCIA — Ganhos: folha diz 1.036, células somam 836" in a for a in avisos))
        self.assertFalse(any("CONFERÊNCIA — Diurese" in a for a in avisos))
        self.assertEqual(l["conferencia_enfermagem"], {"ganhos": 1036, "perdas": 740, "diurese": 720, "bh": 296})

    def test_duas_leituras_na_mesma_hora_viram_lista(self):
        _, l, _ = self.montado()
        self.assertEqual(l["vitais"]["PAS"]["09"], [128, 120])
        self.assertEqual(l["vitais"]["SpO2"]["23"], "?")
        self.assertEqual(l["vitais"]["TAX"]["09"], 38.2)

    def test_coluna_outra_desconhecida_barra_a_ficha(self):
        def mudar(d):
            d["controles"]["balanco"].append({"coluna": "outra (perda)", "rotulo": "xyz", "celulas": [
                {"hora": "7", "ml": "10"}]})
        pl, _, _ = self.montado(mudar)
        erros, _ = validar.validar(motor.preparar(pl)[0])
        self.assertTrue(any("\"xyz\" fora do dicionário" in e for e in erros), erros)

    def test_rotulo_que_mudaria_o_lado_fica_fora_do_nome(self):
        def mudar(d):
            d["controles"]["balanco"].append({"coluna": "Endovenoso", "rotulo": "diurético", "celulas": [
                {"hora": "7", "ml": "5"}]})
        _, l, _ = self.montado(mudar)
        self.assertIn({"nome": "EV", "serie": {"07": 5}}, l["ganhos"])
        self.assertTrue(any("mudaria o lado da conta" in a for a in l["avisos"]))

    def test_limpeza_do_texto(self):
        av = []
        self.assertEqual(montar.limpar("**Tazocin** 06–12—18 → 24 (revisar)", av, "x"), "Tazocin 06-12-18 -> 24")
        self.assertTrue(av)
        _, l, _ = self.montado()
        self.assertIn("Tazocin 4,5 g EV 6/6 h (I: 30/12) => 06-12-18-24", l["ficha"]["infusoes"][1][1])
        self.assertIn("Paracetamol 750 mg VO 6/6 h => 10-16-22-04", l["ficha"]["sistemas"][0][1])

    def test_rodape(self):
        self.assertEqual([montar.volume(x) for x in ("1.036", "+ 296", "-300", "150", "?", "", "abc")],
                         [1036, 296, -300, 150, "?", None, False])
        av = []
        self.assertEqual(montar.rodape({"ganhos_24h": "?", "bh_24h": "+ 40"}, av), {"bh": 40})
        self.assertTrue(av)

    def test_cabecalho_sem_fonte_vira_interrogacao(self):
        def mudar(d):
            d["prescricao"]["diagnostico"] = None; d["prescricao"]["dispositivos"] = None
        _, l, _ = self.montado(mudar)
        self.assertEqual((l["diagnostico"], l["dispositivos"]), ("?", "?"))

    def test_colirio_sai_da_ficha(self):
        _, l, _ = self.montado()
        self.assertNotIn("Lacrima", json.dumps(l["ficha"], ensure_ascii=False))
        self.assertTrue(any("fora da ficha-cola: Lacrima" in a for a in l["avisos"]))

    def test_pendencias_so_as_ordens_da_prescricao(self):
        _, l, _ = self.montado()
        self.assertEqual(l["ficha"]["vigiar"], ["Hemoculturas 2 amostras", "Lactato de controle em 6 h",
                                                "Cabeceira 30°"])

    def test_identidade_diferente_e_erro(self):
        _, _, erros = self.montado(lambda d: d["controles"]["identificacao"].__setitem__("leito", "8"))
        self.assertTrue(any("leito diferente" in e for e in erros), erros)
        _, _, erros = self.montado(lambda d: d["labs"]["identificacao"].__setitem__("nome", "OUTRA PESSOA QUALQUER"))
        self.assertTrue(any("nome do paciente diferente entre" in e for e in erros), erros)

    def test_evolucao_anterior(self):
        outra = "LEITO 09 — X\nExame físico:\n- SNC: vígil\nPlano terapêutico:\n1. Resp: manter\n"
        _, l, _ = self.montado(evolucao_anterior=outra)
        self.assertNotIn("exame_fisico", l)
        self.assertTrue(any("sem o leito 07" in a for a in l["avisos"]))
        _, l, _ = self.montado(evolucao_anterior=outra.replace("09", "07"))
        self.assertEqual(l["exame_fisico"], ["- SNC: vígil"])

    def test_atb_com_inicio_o_motor_escreve_o_d(self):
        pl, _, _ = self.montado()
        prep, avisos = motor.preparar(pl)
        self.assertIn("Tazocin 4,5 g EV 6/6 h (D2, I: 30/12) => 06-12-18-24",
                      prep["leitos"][0]["ficha"]["infusoes"][1][1])
        self.assertTrue(any('"D?" sem data de início' in a and "Azitromicina" in a for a in avisos), avisos)

    def test_laboratorio_lido_e_da_ficha(self):
        _, l, _ = self.montado()
        self.assertEqual(l["laboratorio"], ["HB: 10,8 g/dl", "LEUCO: 18.400 /mm3", "CR: 1,7 mg/dl", "K: 4,8",
                                            "Gaso: Lactato 3,1"])
        self.assertEqual(l["ficha"]["lab"], ["Hb 10,8 | Leuco 18.400", "Cr 1,7", "K 4,8", "Lactato 3,1"])
        exemplo = json.loads((RAIZ / "gerador" / "exemplo" / "plantao-exemplo.json").read_text(encoding="utf-8"))
        curto = montar.lab_curto(exemplo["leitos"][0]["laboratorio"])
        self.assertEqual(curto[0], "Hb 11,2 -> 10,8 | Leuco 16.200 -> 18.400 | Plaq 210.000 -> 180.000")
        _, av = validar.validar(dict(exemplo, leitos=[dict(exemplo["leitos"][0], ficha=dict(
            exemplo["leitos"][0]["ficha"], lab=curto))]))
        self.assertFalse(any("lab da ficha" in a for a in av), av)

    def test_laudo_de_outro_leito_nao_e_usado(self):
        def mudar(d):
            d["labs"] = None
            d["labs_texto"] = (RAIZ / "tests" / "fixtures" / "laudo-ficticio.txt").read_text(encoding="utf-8")
        _, l, _ = self.montado(mudar)
        self.assertNotIn("laboratorio", l)
        self.assertTrue(any("laudo cita o(s) leito(s) 99" in a for a in l["avisos"]))

    def test_data_do_plantao(self):
        pl, _, _ = self.montado(data="02/01/2026")
        self.assertEqual(pl["meta"]["data"], "02/01/2026")

        def so_folha(d):
            d["prescricao"]["identificacao"]["data"] = None; d["labs"]["identificacao"]["data"] = None
        pl, l, _ = self.montado(so_folha)
        self.assertEqual(pl["meta"]["data"], "01/01/2026")  # folha de 31/12 + 1 dia
        self.assertTrue(any("deduzida da folha" in a for a in l["avisos"]))


class MontarRevisaoDe21Out(unittest.TestCase):
    """Achados da revisão adversarial final (21/10/2026)."""

    def montado(self, mudar=None, **contexto):
        pl, erros = montar.montar(leituras(mudar), dict(CONTEXTO, **contexto))
        return pl["leitos"][0], erros

    def test_conectivo_nao_casa_nomes_diferentes(self):
        def mudar(d):
            for k, nome in (("prescricao", "ANTONIO DOS SANTOS"), ("controles", "MARIA DOS ANJOS"),
                            ("labs", "ANTONIO DOS SANTOS")):
                d[k]["identificacao"]["nome"] = nome
        _, erros = self.montado(mudar)
        self.assertIn("nome do paciente diferente entre controles e prescricao", erros)

    def test_documento_sem_identificacao_e_erro(self):
        def mudar(d):
            d["labs"]["identificacao"].update(leito=None, nome=None)
        _, erros = self.montado(mudar)
        self.assertTrue(any("labs: sem leito nem nome legível" in e for e in erros), erros)

    def test_laudo_de_outro_paciente_nao_e_usado(self):
        def mudar(d):
            d["labs"] = None
            d["labs_texto"] = "Paciente: OUTRA PESSOA QUALQUER   Leito: 07\nData: 01/01/2026\nHemoglobina 10,8 g/dL\n"
        l, _ = self.montado(mudar)
        self.assertNotIn("laboratorio", l)
        self.assertIn("labs: o laudo é de outro paciente: não usado, ler no chat", l["avisos"])

    def test_idade_com_meses(self):
        l, _ = self.montado(lambda d: d["prescricao"]["identificacao"].__setitem__("idade", "68a 3m"))
        self.assertEqual(l["idade_sexo"], "68M")

    def test_simbolo_da_legenda_vira_ml(self):
        def mudar(d):
            d["controles"]["balanco"].append({"coluna": "Infus. Rápida", "rotulo": None, "celulas": [
                {"hora": "9", "ml": "△"}, {"hora": "11", "ml": "▲"}, {"hora": "13", "ml": "+"}]})
        l, _ = self.montado(mudar)
        self.assertIn({"nome": "infusão rápida", "serie": {"09": 100, "11": 250, "13": 10}}, l["ganhos"])

    def test_coluna_outra_do_lado_errado_e_erro(self):
        def mudar(d):
            d["controles"]["balanco"].append({"coluna": "outra (ganho)", "rotulo": "diurese", "celulas": [
                {"hora": "9", "ml": "100"}]})
        _, erros = self.montado(mudar)
        self.assertTrue(any("motor soma do outro lado" in e for e in erros), erros)

    def test_evolucao_anterior_de_outro_paciente_nao_e_copiada(self):
        outra = "LEITO 07 — JOSE PEREIRA\nExame físico:\n- SNC: vígil\nPlano terapêutico:\n1. Resp: manter\n"
        l, _ = self.montado(evolucao_anterior=outra)
        self.assertNotIn("exame_fisico", l)
        self.assertTrue(any("é de outro paciente" in a for a in l["avisos"]))

    def test_data_informada_invalida_e_erro(self):
        _, erros = self.montado(data="31/02/2026")
        self.assertIn("data informada no disparo inválida (31/02/2026)", erros)

    def test_duvida_fora_do_texto_da_ficha_vai_para_o_conferir(self):
        def mudar(d):
            d["prescricao"]["itens"][1]["inicio"] = "30/12 (confirmar)"
            d["prescricao"]["dieta"] = "Enteral 50 ml/h (confirmar)"
            d["prescricao"]["identificacao"]["idade"] = "68 (revisar)"
        l, _ = self.montado(mudar)
        self.assertIn("Tazocin 4,5 g EV 6/6 h (D?) => 06-12-18-24", l["ficha"]["infusoes"][1][1])
        self.assertEqual(l["dieta"], "Enteral 50 ml/h")
        for trecho in ("início do ATB: dúvida", "prescrição: dúvida de leitura tirada do texto: Enteral",
                       "prescricao: dúvida de leitura em idade"):
            self.assertTrue(any(trecho in a for a in l["avisos"]), (trecho, l["avisos"]))

    def test_pagina_de_outro_paciente_e_erro(self):
        _, erros = self.montado(lambda d: d["controles"]["pendencias"].append(
            "página 2 é de outro paciente, leito 08"))
        self.assertIn("controles: a leitura achou página de outro paciente: conferir os anexos", erros)

    def test_laudo_antigo_avisa_e_titulo_tem_a_data_do_laudo(self):
        def mudar(d):
            d["labs"]["identificacao"]["data"] = "28/12/2025"
        l, _ = self.montado(mudar)
        self.assertEqual(l["ficha"]["lab_titulo"], "LABORATÓRIO 28/12")
        self.assertTrue(any("laudo de 28/12, 4 dias antes" in a for a in l["avisos"]), l["avisos"])


# ── ficha e esteira inteira ────────────────────────────────────────────────────────────────────────────────
@unittest.skipUnless(TEM_PDF, "sem LibreOffice/poppler")
class Ficha(unittest.TestCase):
    def test_uma_folha_e_conferencia_limpa(self):
        import processar
        pl, erros = montar.montar(leituras(), CONTEXTO)
        self.assertEqual(erros, [])
        with tempfile.TemporaryDirectory() as tmp:
            with contextlib.redirect_stderr(io.StringIO()):
                arquivos, erros, avisos = processar.gerar_ficha(pl, Path(tmp))
            self.assertEqual(erros, [])
            self.assertEqual([a.suffix for a in arquivos], [".docx", ".pdf"])
            self.assertRegex(arquivos[0].name, r"^01-01-26-uti2-ficha-cola-diurno-leito07-\d{4}\.docx$")
        self.assertTrue(any("CONFERÊNCIA — Ganhos" in a for a in avisos))


@unittest.skipUnless(TEM_PDF and TEM_POPPLER, "sem LibreOffice/poppler")
class Esteira(unittest.TestCase):
    """processar.main() com o Airtable e a API simulados."""

    def rodar(self, respostas, chave="sk-teste", campos_extra=None, campo="fld" + "B" * 14):
        import processar
        gravados, enviados = [], []
        campos = {processar.CAMPO[k]: [{"url": f"https://x/{k}", "filename": f"{k}.pdf", "size": None}]
                  for k in processar.ANEXOS}
        campos.update(campos_extra or {})

        def airtable(metodo, record_id, token, corpo=None):
            if metodo == "PATCH":
                gravados.append(corpo["fields"])
            return {"fields": campos}

        def baixar(url, destino):
            destino.parent.mkdir(parents=True, exist_ok=True)
            return pdf_minimo(destino, 2 if "controles" in url else 1).stat().st_size

        env = {"RECORD_ID": "rec" + "A" * 14, "AIRTABLE_TOKEN": "pat", "AIRTABLE_CAMPO_SAIDA": campo,
               "ANTHROPIC_API_KEY": chave, "DATA_PLANTAO": "", "TURNO": "diurno"}
        saida = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, dict(env, RUNNER_TEMP=tmp)), \
                mock.patch.object(processar, "airtable", airtable), mock.patch.object(processar, "baixar", baixar), \
                mock.patch.object(processar, "enviar_anexo", lambda r, t, c, arq: enviados.append(
                    (c, arq.suffix, arq.stat().st_size))), \
                mock.patch.object(leitura, "cliente", lambda: ClienteFalso(respostas) if chave else None), \
                contextlib.redirect_stdout(saida), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as fim:
                processar.main()
        return fim.exception.code, gravados, enviados, saida.getvalue()

    def respostas(self, mudar=None):
        d = leituras(mudar)
        return {"controles": d["controles"], "prescricao": d["prescricao"], "labs": d["labs"]}

    def test_le_monta_gera_e_devolve(self):
        codigo, gravados, enviados, log = self.rodar(self.respostas())
        final = gravados[-1]
        self.assertEqual((codigo, gravados[0]), (0, {"fldMKAeMcwDEIYrWP": "lendo"}))
        self.assertEqual(final["fldMKAeMcwDEIYrWP"], "pronto", final["fldyWHVHultgXHW9Z"])
        self.assertEqual([e[1] for e in enviados], [".docx", ".pdf", ".json"])
        self.assertTrue(all(c == "fld" + "B" * 14 for c, _, _ in enviados))
        self.assertIn("Ficha-cola: gerada, 1 folha", final["fldyWHVHultgXHW9Z"])
        self.assertIn("CONFERÊNCIA — Ganhos", final["fldyWHVHultgXHW9Z"])
        self.assertNotIn("FICTICIO", log)  # log do Actions é público
        self.assertNotIn(".pdf", log)

    def test_identificacao_diferente_devolve_so_o_rascunho(self):
        resp = self.respostas(lambda d: d["controles"]["identificacao"].__setitem__("leito", "8"))
        codigo, gravados, enviados, _ = self.rodar(resp)
        self.assertEqual(codigo, 1)
        self.assertEqual(gravados[-1]["fldMKAeMcwDEIYrWP"], "falhou")
        self.assertIn("leito diferente", gravados[-1]["fldyWHVHultgXHW9Z"])
        self.assertEqual([e[1] for e in enviados], [".json"])

    def test_leitura_recusada_e_falha_com_motivo(self):
        resp = self.respostas()
        resp["prescricao"] = mensagem(stop="refusal", content=[])
        codigo, gravados, enviados, _ = self.rodar(resp)
        self.assertEqual(codigo, 1)
        self.assertIn("prescricao: não lido (recusa do modelo)", gravados[-1]["fldyWHVHultgXHW9Z"])
        self.assertEqual([e[1] for e in enviados], [".json"])

    def test_sem_campo_de_saida_nao_le(self):
        resp = self.respostas()
        codigo, gravados, enviados, _ = self.rodar(resp, campo="")
        self.assertEqual(codigo, 1)
        self.assertIn("falta a variável AIRTABLE_CAMPO_SAIDA", gravados[-1]["fldyWHVHultgXHW9Z"])
        self.assertEqual(enviados, [])

    def test_ficha_reprovada_nao_volta(self):
        import processar
        reprovada = lambda pl, pasta: ([pdf_minimo(pasta / "f.docx"), pdf_minimo(pasta / "f.pdf")],
                                       ["ficha-cola com 2 página(s): tem de ser 1 folha"], [])
        with mock.patch.object(processar, "gerar_ficha", reprovada):
            codigo, gravados, enviados, _ = self.rodar(self.respostas())
        self.assertEqual((codigo, gravados[-1]["fldMKAeMcwDEIYrWP"]), (1, "falhou"))
        self.assertIn("2 página(s)", gravados[-1]["fldyWHVHultgXHW9Z"])
        self.assertEqual([e[1] for e in enviados], [".json"])

    def test_ficha_que_quebra_devolve_o_rascunho(self):
        import processar
        with mock.patch.object(processar, "gerar_ficha", mock.Mock(side_effect=OSError("soffice"))):
            codigo, gravados, enviados, _ = self.rodar(self.respostas())
        self.assertEqual(codigo, 1)
        self.assertIn("ficha não gerada (OSError: soffice)", gravados[-1]["fldyWHVHultgXHW9Z"])
        self.assertEqual([e[1] for e in enviados], [".json"])

    def test_pdf_que_nao_recorta_nao_derruba_os_outros(self):
        import preparar
        original = preparar.recortes_para_leitura

        def recortes(pdf, destino, *a, **k):
            if "prescricao" in str(pdf):
                raise RuntimeError("pdftoppm")
            return original(pdf, destino, *a, **k)
        with mock.patch.object(preparar, "recortes_para_leitura", recortes):
            codigo, gravados, enviados, _ = self.rodar(self.respostas())
        self.assertEqual(codigo, 1)
        self.assertIn("prescricao: PDF não recortado (RuntimeError): não lido", gravados[-1]["fldyWHVHultgXHW9Z"])
        self.assertEqual([e[1] for e in enviados], [".json"])

    def test_foto_no_lugar_do_pdf_nao_sai_como_pronta(self):
        import processar
        foto = {processar.CAMPO["controles"]: [{"url": "https://x/controles", "filename": "folha.jpg", "size": None}]}
        codigo, gravados, enviados, _ = self.rodar(self.respostas(), campos_extra=foto)
        self.assertEqual((codigo, gravados[-1]["fldMKAeMcwDEIYrWP"]), (1, "falhou"))
        self.assertIn("controles: 1 anexo(s) que não são PDF não foram lidos", gravados[-1]["fldyWHVHultgXHW9Z"])
        self.assertIn("controles: sem anexo em PDF: ficha não gerada", gravados[-1]["fldyWHVHultgXHW9Z"])
        self.assertNotIn(".pdf", [e[1] for e in enviados])

    def test_job_cancelado_termina_em_falhou(self):
        import processar
        with mock.patch.object(processar, "etapa3", mock.Mock(side_effect=KeyboardInterrupt)):
            codigo, gravados, enviados, _ = self.rodar(self.respostas())
        self.assertEqual((codigo, gravados[-1]["fldMKAeMcwDEIYrWP"]), (1, "falhou"))
        self.assertIn("interrompido antes do fim", gravados[-1]["fldyWHVHultgXHW9Z"])

    def test_sem_chave_so_baixa(self):
        codigo, gravados, enviados, _ = self.rodar({}, chave="")
        self.assertEqual(codigo, 0)
        self.assertEqual(gravados[-1]["fldMKAeMcwDEIYrWP"], "pronto")
        self.assertIn("leitura automática desligada", gravados[-1]["fldyWHVHultgXHW9Z"])
        self.assertEqual(enviados, [])


if __name__ == "__main__":
    unittest.main()
