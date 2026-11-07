# -*- coding: utf-8 -*-
"""Ficha-cola, opção A (07/11/2026): faixas cinza, alerta em caixinha e EXAME FÍSICO no lugar da grade
CONTROLES DO PLANTÃO, sem a faixa de bundle. Rodar: python3 -m unittest discover -s tests"""
import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "gerador"))
import estilo as E  # noqa: E402
import ficha_cola  # noqa: E402
import office  # noqa: E402

from docx import Document  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402

EXEMPLO = json.loads((RAIZ / "gerador" / "exemplo" / "plantao-exemplo.json").read_text(encoding="utf-8"))
TEM_PDF = bool(shutil.which("soffice") and shutil.which("pdftotext"))


def ficha(dados=None):
    """Gera a ficha-cola do exemplo e devolve o corpo do Word."""
    with tempfile.TemporaryDirectory() as tmp:
        cola = Path(tmp) / "cola.docx"
        ficha_cola.gerar(copy.deepcopy(dados or EXEMPLO), cola, {})
        return Document(str(cola)).element.body


def texto(el):
    return "".join(t.text or "" for t in el.iter(qn("w:t")))


def paragrafo(corpo, comeco):
    for p in corpo.iter(qn("w:p")):
        if texto(p).strip().startswith(comeco):
            return p
    raise AssertionError(f"parágrafo {comeco!r} não achado")


def fundo(el):
    pr = el.find(qn("w:pPr") if el.tag == qn("w:p") else qn("w:tcPr"))
    shd = None if pr is None else pr.find(qn("w:shd"))
    return None if shd is None else shd.get(qn("w:fill"))


class ExameFisicoNoLugarDosControles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.txt = "\n".join(texto(p) for p in ficha().iter(qn("w:p")))

    def test_sai_a_grade_controles_do_plantao(self):
        self.assertNotIn("CONTROLES DO PLANTÃO", self.txt)

    def test_entra_o_exame_fisico_em_seis_quadros(self):
        self.assertIn("EXAME FÍSICO", self.txt)
        for quadro in ("NEURO", "RESPIRATÓRIO", "HEMODINÂMICA", "RENAL · METABÓLICO", "TGI · NUTRIÇÃO",
                       "INFECTO · PELE"):
            self.assertIn(quadro, self.txt)
        for campo in ("RASS", "CAM-ICU", "PEEP", "TEC", "Diurese", "Abdome", "LPP"):
            self.assertIn(campo, self.txt)

    def test_intercorrencias_continuam_embaixo(self):
        self.assertIn("INTERCORRÊNCIAS, CONDUTAS E PASSAGEM", self.txt)

    def test_sem_faixa_de_bundle(self):  # 07/11/2026: ele mandou tirar o FAST HUGS BID do pé dos quadros
        for termo in ("FAST HUGS", "despertar diário", "LAMG indicada", "retirar cateter", "descalonar"):
            self.assertNotIn(termo, self.txt)


class FaixasCinza(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpo = ficha()

    def test_titulo_em_faixa_cinza(self):
        for titulo in ("CONTROLES", "LABORATÓRIO", "PRESCRIÇÃO", "PENDÊNCIAS", "EXAMES", "EXAME FÍSICO",
                       "INTERCORRÊNCIAS"):
            self.assertEqual(fundo(paragrafo(self.corpo, titulo)), E.PAPEL_CINZA_FAIXA, titulo)

    def test_subtitulo_em_faixa_mais_clara(self):
        for titulo in ("BALANÇO", "INFUSÕES E TERAPIAS", "POR SISTEMAS"):
            self.assertEqual(fundo(paragrafo(self.corpo, titulo)), E.PAPEL_CINZA_SUB, titulo)

    def test_quadro_do_exame_com_cabecalho_cinza(self):
        cabecalhos = [tc for tc in self.corpo.iter(qn("w:tc")) if texto(tc) in ("NEURO", "RESPIRATÓRIO")]
        self.assertEqual(len(cabecalhos), 2)
        for tc in cabecalhos:
            self.assertEqual(fundo(tc), E.PAPEL_CINZA_SUB)

    def test_linha_sim_linha_nao(self):
        zebra = [tc for tc in self.corpo.iter(qn("w:tc")) if fundo(tc) == E.PAPEL_CINZA_ZEBRA]
        self.assertTrue(any(texto(tc) == "PAS" for tc in zebra))      # 1ª linha dos vitais
        self.assertFalse(any(texto(tc) == "PAD" for tc in zebra))     # 2ª linha fica branca
        self.assertTrue(any(texto(tc) == "ATB" for tc in zebra))      # rótulo da prescrição

    def test_texto_continua_preto(self):
        self.assertIsNone(self.corpo.find(".//" + qn("w:color")))


class AlertaEmCaixinha(unittest.TestCase):
    def test_flag_de_sinal_vital_em_caixinha(self):
        runs = [r for r in ficha().iter(qn("w:r")) if texto(r) == "1x<90"]
        self.assertTrue(runs)
        self.assertIsNotNone(runs[0].find(qn("w:rPr")).find(qn("w:bdr")))

    def test_alergia_em_caixa(self):
        bdr = paragrafo(ficha(), "ALERGIA:").find(qn("w:pPr")).find(qn("w:pBdr"))
        self.assertIsNotNone(bdr)
        for lado in ("top", "left", "bottom", "right"):
            self.assertIsNotNone(bdr.find(qn("w:" + lado)), lado)

    def test_sem_alergia_sem_caixa(self):
        dados = copy.deepcopy(EXEMPLO)
        dados["leitos"][0]["alergia"] = "nega"
        ppr = paragrafo(ficha(dados), "Alergia:").find(qn("w:pPr"))
        self.assertTrue(ppr is None or ppr.find(qn("w:pBdr")) is None)


def leito_pesado():
    """Leito fictício perto do limite: cabia em 1 folha (9,5 pt) com a grade CONTROLES DO PLANTÃO."""
    d = copy.deepcopy(EXEMPLO)
    f = d["leitos"][0]["ficha"]
    f["infusoes"] = [
        ["DVA", ["Noradrenalina 16 mg/250 ml 12 ml/h", "Vasopressina 20 UI/100 ml 6 ml/h"]],
        ["SEDAÇÃO", ["Fentanil 2.500 mcg/250 ml 10 ml/h", "Midazolam 150 mg/150 ml 8 ml/h"]],
        ["ATB", ["Meropenem 2 g EV 8/8 h (I: 30/12)", "Vancomicina 1 g EV 12/12 h (I: 30/12)",
                 "Fluconazol 400 mg EV 1x/dia (I: 31/12)"]],
        ["VM", ["PCV 18 cmH2O · PEEP 10 · FiO2 50 % · FR 22"]],
        ["DIETA", ["Fresubin HP Energy 60 ml/h SNE · Água 200 ml 6/6 h"]],
        ["TRS", ["CVVHDF 25 ml/kg/h · UF 100 ml/h"]]]
    f["sistemas"] = [
        ["NEURO", ["Fenitoína 100 mg EV 8/8 h", "Quetiapina 25 mg SNE 12/12 h"]],
        ["CV", ["Hidrocortisona 50 mg EV 6/6 h", "Amiodarona 600 mg/dia EV em BIC"]],
        ["RESP", ["Inalação com Berotec 10 gotas 6/6 h"]],
        ["TGI", ["Pantozol (pantoprazol) 40 mg EV 1x/dia", "Bromoprida 10 mg EV 8/8 h"]],
        ["ENDÓCRINO", ["Insulina regular em BIC conforme protocolo"]],
        ["ANALGESIA", ["Paracetamol 750 mg SNE 6/6 h", "Dipirona 1 g EV 6/6 h"]]]
    f["vigiar"] = ["Nora 12 ml/h: meta PAM ≥ 65", "Hemoculturas 2 amostras", "Lactato de controle em 6 h",
                   "Vanco: vale antes da 4ª dose", "TRE amanhã se FiO2 ≤ 40 %"]
    f["exames"] = ["RX tórax 31/12: consolidação em base D", "TC crânio 30/12: sem sangramento"]
    d["leitos"][0]["alergia"] = "nega"  # o exemplo é alérgico a dipirona; aqui só importa o tamanho
    return d


class AjusteComExameCompacto(unittest.TestCase):
    """Folha cheia: antes de baixar a fonte, o exame perde folga entre as linhas e as intercorrências
    descem para a altura dele (exame compacto)."""

    def ajustar_com(self, cabe):
        tentativas = []

        def gerar_falso(plantao, caminho, cfg=None, folga=0.0):
            tentativas.append(next(iter(cfg.values())))

        with mock.patch.object(ficha_cola, "gerar", gerar_falso), \
                mock.patch.object(ficha_cola, "n_paginas", lambda _: 1 if cabe(tentativas[-1]) else 2):
            return ficha_cola.ajustar(copy.deepcopy(EXEMPLO))

    def test_compacto_vem_antes_de_baixar_a_fonte(self):
        res, nao_coube = self.ajustar_com(lambda cfg: cfg[3])
        self.assertEqual(res, {"99": (14, ficha_cola.N_INTER_COMPACTO, 10, True)})
        self.assertEqual(nao_coube, [])

    def test_folha_que_cabe_fica_com_o_exame_normal(self):
        res, _ = self.ajustar_com(lambda cfg: True)
        self.assertEqual(res, {"99": (14, ficha_cola.N_INTER, 10, False)})

    def test_nada_cabe_sai_compacto_em_9_pt(self):
        res, nao_coube = self.ajustar_com(lambda cfg: False)
        self.assertEqual(res, {"99": (0, ficha_cola.N_INTER_COMPACTO, 9, True)})
        self.assertEqual(nao_coube, ["99"])


@unittest.skipUnless(TEM_PDF, "sem LibreOffice/pdftotext")
class LeitoPesadoEmUmaFolha(unittest.TestCase):
    def test_exame_compacto_poe_o_leito_pesado_em_1_folha(self):
        pl, _ = ficha_cola.motor.preparar(leito_pesado())
        with tempfile.TemporaryDirectory() as tmp:
            cola = Path(tmp) / "cola.docx"
            ficha_cola.gerar(pl, cola, {"99": (0, ficha_cola.N_INTER_COMPACTO, 9, True)}, folga=E.FOLGA_MEDICAO)
            self.assertEqual(ficha_cola.n_paginas(cola), 1)


@unittest.skipUnless(TEM_PDF, "sem LibreOffice/pdftotext")
class FaixaNumaLinhaSo(unittest.TestCase):
    def test_titulo_das_intercorrencias_nao_quebra(self):  # 225,8 pt de texto numa coluna de 8,4 cm
        with tempfile.TemporaryDirectory() as tmp:
            cola = Path(tmp) / "cola.docx"
            ficha_cola.gerar(copy.deepcopy(EXEMPLO), cola, {})
            pdf = office.para_pdf(cola)
            txt = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True).stdout
        self.assertIn("INTERCORRÊNCIAS, CONDUTAS E PASSAGEM", txt)


if __name__ == "__main__":
    unittest.main()
