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
        self.assertEqual(leitos["99"]["laboratorio_anterior"], l["laboratorio"])  # sem a linha CLCR do motor
        self.assertEqual(leitos["99"]["peso"], l["peso"])  # o peso passa de um dia para o outro com fonte e data

    def test_peso_da_linha_do_bloco(self):
        texto = """LEITO 11 — FULANA
Sinais vitais + balanço 24 h:
Peso: 66,5 kg (balança, leito, 30/10/2026) | Altura: 153 cm | Peso predito: 46 kg (VC 6 - 8 ml/kg: 276 - 368 ml)
LEITO 12 — BELTRANA
Peso: 70 kg
"""
        leitos, _ = EA.ler(texto.splitlines())
        self.assertEqual(leitos["11"]["peso"], {"kg": 66.5, "altura_cm": 153, "fonte": "balança, leito",
                                                "data": "30/10/2026"})
        self.assertNotIn("peso", leitos["12"])  # sem fonte e data não passa adiante

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

    def test_txt_salvo_no_windows_nao_derruba(self):  # PENDENTE §2, conferido em 11/11/2026
        with tempfile.TemporaryDirectory() as tmp:
            arq = Path(tmp) / "evolucao.txt"
            arq.write_bytes("LEITO 05\nExame físico:\nBEG, corado, hidratado\n".encode("cp1252"))
            linhas = EA.linhas_do_arquivo(arq)
        self.assertIn("Exame físico:", linhas)

    def test_txt_utf8_com_bom_do_bloco_de_notas_le_o_primeiro_leito(self):
        with tempfile.TemporaryDirectory() as tmp:
            arq = Path(tmp) / "evolucao.txt"
            arq.write_bytes("LEITO 05\nExame físico:\nBEG\n".encode("utf-8-sig"))
            linhas = EA.linhas_do_arquivo(arq)
        self.assertEqual(linhas[0], "LEITO 05")


if __name__ == "__main__":
    unittest.main()
