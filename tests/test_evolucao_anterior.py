# -*- coding: utf-8 -*-
"""Leitor da evolução anterior. Rodar: python3 -m unittest discover -s tests"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "gerador"))
import evolucao_anterior as EA  # noqa: E402
import gerar_docx  # noqa: E402

EXEMPLO = json.loads((RAIZ / "gerador" / "exemplo" / "plantao-exemplo.json").read_text(encoding="utf-8"))


class LerEvolucao(unittest.TestCase):
    def test_le_o_word_que_o_proprio_gerador_faz(self):
        with tempfile.TemporaryDirectory() as tmp:
            evo = Path(tmp) / "evo.docx"
            gerar_docx.gerar_evolucoes(EXEMPLO, evo)
            leitos, avisos = EA.ler(EA.linhas_do_arquivo(evo))
        l = EXEMPLO["leitos"][0]
        self.assertEqual(avisos, [])
        self.assertEqual(leitos["99"]["exame_fisico"], l["exame_fisico"])
        self.assertEqual(leitos["99"]["plano_anterior"], l["conduta"])
        self.assertEqual(leitos["99"]["laboratorio_anterior"], l["laboratorio"])

    def test_formato_da_admissao_e_varios_leitos(self):
        texto = """02 - FULANO FICTÍCIO
ADMISSÃO UTI 2 - 10-10-26
Exame Físico Geral:
- Geral: REG, corado.
- Sistema Nervoso Central: ECG 15.
Plano terapêutico e Condutas:
1. Infeccioso:
- Suspendo Rocefin;
LEITO 03 — BELTRANO FICTÍCIO — D2 UTI
Exame físico:
Neurológico: RASS 0.
Impressão / Problemas ativos:
1. Pneumonia.
"""
        leitos, avisos = EA.ler(texto.splitlines())
        self.assertEqual(leitos["02"]["exame_fisico"], ["- Geral: REG, corado.", "- Sistema Nervoso Central: ECG 15."])
        self.assertEqual(leitos["02"]["plano_anterior"], ["1. Infeccioso:", "- Suspendo Rocefin;"])
        self.assertEqual(leitos["03"]["exame_fisico"], ["Neurológico: RASS 0."])  # Impressão fecha a seção
        self.assertTrue(any("L03: plano" in a for a in avisos))

    def test_nada_reconhecido(self):
        _, avisos = EA.ler(["texto solto"])
        self.assertTrue(any("nenhum leito" in a for a in avisos))


if __name__ == "__main__":
    unittest.main()
