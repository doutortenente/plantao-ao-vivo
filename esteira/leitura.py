# -*- coding: utf-8 -*-
"""
leitura.py — lê os scans de UM leito com a API do Claude (visão) e devolve o JSON cru: células e horas, sem conta.

Quem soma, conta flag e calcula dia é o motor (build_passagem.py); quem monta o JSON do plantão é o montar.py.
Prompt de sistema: esteira/doutrina-leitura.md (o teste de doutrina também o lê). Saída presa a um JSON schema
(structured outputs): a resposta sempre tem o formato pedido, e "?" / "" / "pendencias" carregam as dúvidas.

Chamada (conferida com a skill claude-api e o SDK anthropic 1.15.0):
  - modelo claude-opus-5-5 (MODELO_LEITURA sobrescreve), effort high, raciocínio sempre ligado no modelo;
  - fallbacks "default" no servidor (beta server-side-fallback-2026-07-01): recusa de política é refeita em outro
    modelo dentro da mesma chamada. No streaming, a recusa no meio da resposta guarda o texto parcial, marca o ponto
    com um bloco "fallback" e o outro modelo CONTINUA o texto: o JSON é a emenda dos blocos de texto; se a emenda
    não for JSON (o outro modelo recomeçou), vale o texto depois do último "fallback";
  - streaming (resposta longa), max_tokens 64000 (o raciocínio conta dentro dele);
  - recusa ou resposta cortada → LeituraFalhou: nada é inventado para tapar o buraco.
Imagens: preparar.recortes_para_leitura (JPEG, até 2576 px, 3,75 MP e 5 MB). Mais de 20 imagens num pedido baixam
o limite do lado para 2000 px na API: aí as visões gerais saem e, se ainda passar, o documento não é lido.
"""
import base64
import json
import os
from pathlib import Path

MODELO = os.environ.get("MODELO_LEITURA") or "claude-opus-5-5"
BETAS = ["server-side-fallback-2026-07-01"]
MAX_TOKENS = 64000
MAX_IMAGENS = 20
DOUTRINA = Path(__file__).resolve().parent / "doutrina-leitura.md"


class LeituraFalhou(Exception):
    pass


# ── schemas (structured outputs: todo objeto fechado, toda chave obrigatória, dúvida = "?", vazio = "") ───────
# Sem anyOf/null: a API limita os campos de tipo união por pedido, e só a folha de controle teria 22.
def _txt():
    return {"type": "string"}


def _lista(item):
    return {"type": "array", "items": item}


def _obj(**props):
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


def _enum(valores):
    return {"type": "string", "enum": list(valores)}


IDENTIFICACAO = _obj(leito=_txt(), nome=_txt(), idade=_txt(), sexo=_txt(), unidade=_txt(), data=_txt())

# colunas impressas do Mod. 0120-01 (página 2); o montar.py dá o nome que o motor conhece (CANON)
COLUNAS = ("VO", "Dieta", "SNE", "Água", "Med", "Endovenoso", "Infus. Rápida", "Dil.",
           "Diurese", "SNG/SNE", "Evacuação", "Resíduo Gástrico", "Dreno/SVD", "outra (ganho)", "outra (perda)")
GRUPOS = ("DVA", "SEDAÇÃO", "ATB", "VM", "O2", "DIETA", "NPT", "TRS", "NEURO", "CV", "RESP", "TGI", "RENAL",
          "ENDÓCRINO", "ANALGESIA", "PROFILAXIA", "SN", "OUTRO")
SIGLAS = ("HB", "HT", "PLAQ", "LEUCO", "SEG", "BAST", "UR", "CR", "NA", "K", "MG", "CAI", "P", "PH", "PCO2", "PO2",
          "HCO3", "BE", "SATO2", "LACTATO", "PCR", "TROPONINA", "INR")

SCHEMA = {
    "controles": _obj(
        identificacao=IDENTIFICACAO,
        afericoes=_lista(_obj(hora=_txt(), t=_txt(), fr=_txt(), fc=_txt(),
                              pa=_lista(_obj(pas=_txt(), pad=_txt(), pam=_txt())),
                              dx=_txt(), spo2=_txt(), suporte=_txt())),
        balanco=_lista(_obj(coluna=_enum(COLUNAS), rotulo=_txt(),
                            celulas=_lista(_obj(hora=_txt(), ml=_txt())))),
        rodape=_obj(ganhos_24h=_txt(), perdas_24h=_txt(), diurese_24h=_txt(), bh_24h=_txt()),
        evacuacao=_txt(), dieta=_txt(), pendencias=_lista(_txt())),
    "prescricao": _obj(
        identificacao=IDENTIFICACAO, diagnostico=_txt(), alergias=_txt(), dispositivos=_txt(), dieta=_txt(),
        itens=_lista(_obj(nome=_txt(), dose=_txt(), via=_txt(), frequencia=_txt(), horarios=_txt(),
                          grupo=_enum(GRUPOS), inicio=_txt())),
        suspensos=_lista(_txt()), ordens=_lista(_txt()), pendencias=_lista(_txt())),
    "labs": _obj(
        identificacao=IDENTIFICACAO,
        exames=_lista(_obj(sigla=_enum(SIGLAS), valor=_txt())), pendencias=_lista(_txt())),
}
PEDIDO = {
    "controles": "Documento: FOLHA DE CONTROLE do leito (página 1 sinais vitais, página 2 ganhos/perdas).",
    "prescricao": "Documento: PRESCRIÇÃO MÉDICA do leito.",
    "labs": "Documento: LABORATÓRIO do leito (laudo escaneado ou anotação à mão).",
}


def doutrina():
    """O texto entre as linhas '---' de doutrina-leitura.md."""
    partes = DOUTRINA.read_text(encoding="utf-8").split("\n---\n")
    return partes[1].strip()


# ── chamada ───────────────────────────────────────────────────────────────────────────────────────────────
def cliente():
    """Cliente da API, ou None sem ANTHROPIC_API_KEY (a esteira fica só no download)."""
    if not os.environ.get("ANTHROPIC_API_KEY", "").strip():
        return None
    import anthropic  # só aqui: os testes e o gerador não precisam do SDK
    return anthropic.Anthropic(max_retries=4)


def conteudo(paginas, tipo):
    """Blocos da mensagem: rótulo + imagem de cada recorte, e o pedido no fim."""
    imagens = [(pag, i, img) for pag, imgs in paginas for i, img in enumerate(imgs)]
    if len(imagens) > MAX_IMAGENS:
        imagens = [x for x in imagens if x[1] > 0]  # sem as visões gerais
    if len(imagens) > MAX_IMAGENS:
        raise LeituraFalhou(f"{len(paginas)} páginas: passa de {MAX_IMAGENS} imagens num pedido; ler no chat")
    blocos = []
    for pag, i, img in imagens:
        nome = Path(img).stem.split("-", 1)[-1]
        rotulo = "inteira, resolução baixa (só para orientação)" if i == 0 else f"metade de {nome}, alta resolução"
        blocos.append({"type": "text", "text": f"Página {pag}: {rotulo}"})
        blocos.append({"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                                    "data": base64.standard_b64encode(Path(img).read_bytes())
                                                    .decode("ascii")}})
    blocos.append({"type": "text", "text": PEDIDO[tipo] + " Responda com o JSON do formato pedido."})
    return blocos


def resposta(msg):
    """JSON da resposta. Com fallback: a emenda parcial + continuação; senão, o texto depois do último 'fallback'."""
    if msg.stop_reason == "refusal":
        det = getattr(msg, "stop_details", None)
        raise LeituraFalhou("recusa do modelo" + (f" ({det.category})" if det and getattr(det, "category", None)
                                                  else ""))
    if msg.stop_reason == "max_tokens":
        raise LeituraFalhou("resposta cortada (max_tokens)")
    blocos = list(msg.content)
    ult = max((i for i, b in enumerate(blocos) if b.type == "fallback"), default=-1)
    depois = [b.text for b in blocos[ult + 1:] if b.type == "text"]
    if not depois:
        raise LeituraFalhou("resposta sem texto")
    candidatos = ["".join(b.text for b in blocos if b.type == "text")] if ult >= 0 else []
    candidatos += ["".join(depois), depois[-1]]
    erro = None
    for txt in dict.fromkeys(candidatos):
        try:
            return json.loads(txt)
        except json.JSONDecodeError as e:
            erro = erro or e
    raise LeituraFalhou(f"resposta fora do JSON ({erro.msg})")


def ler(cli, tipo, paginas):
    """(dados, request_id) de um documento. `paginas` = [(nº, [geral, metade, metade])]."""
    blocos = conteudo(paginas, tipo)
    try:
        with cli.beta.messages.stream(
                model=MODELO, max_tokens=MAX_TOKENS, betas=BETAS, fallbacks="default", system=doutrina(),
                output_config={"effort": "high", "format": {"type": "json_schema", "schema": SCHEMA[tipo]}},
                messages=[{"role": "user", "content": blocos}]) as stream:
            msg = stream.get_final_message()
            request_id = getattr(stream, "request_id", None)
    except Exception as e:  # rede, limite, 5xx: o SDK já tentou de novo (max_retries)
        status = getattr(e, "status_code", None)
        raise LeituraFalhou(f"erro da API ({type(e).__name__}{f' {status}' if status else ''})") from e
    return resposta(msg), request_id
