# -*- coding: utf-8 -*-
"""Formato de entrega pedido em 02/11/2026: bloco de sinais vitais + balanço numa linha só, sem "Ingesta hídrica",
séries com "=>", UR e CR seriais na linha dos eletrólitos (eletrólitos sem série) e, na ficha-cola, sem aferição
de glicemia nem escala de correção. Rodar: python3 -m unittest discover -s tests"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "gerador"))
sys.path.insert(0, str(RAIZ / "skills" / "sasi-ingest-export" / "scripts"))
import build_passagem as motor  # noqa: E402
import ficha_cola  # noqa: E402
import gerar_docx  # noqa: E402

EXEMPLO = json.loads((RAIZ / "gerador" / "exemplo" / "plantao-exemplo.json").read_text(encoding="utf-8"))


class BlocoCompacto(unittest.TestCase):
    def setUp(self):
        self.leito, self.meta = EXEMPLO["leitos"][0], EXEMPLO["meta"]

    def test_uma_linha_sem_ingesta(self):
        txt, _ = motor.render_leito(self.leito, self.meta)
        linhas = txt.split("\n")
        i = next(i for i, l in enumerate(linhas) if l.startswith("Sinais vitais + balanço"))
        self.assertEqual(linhas[i + 2], "")  # título, 1 linha, linha em branco
        bloco = linhas[i + 1]
        self.assertTrue(bloco.startswith("PAS: "))
        self.assertIn(" | PAD: ", bloco)
        self.assertIn(" | Dieta: enteral 50 ml/h | ", bloco)
        self.assertIn(" | BH: ", bloco)
        self.assertNotIn("Ingesta", txt)

    def test_motor_guarda_as_linhas_separadas(self):
        r = motor.compute_leito(self.leito, self.meta)  # a ficha-cola lê item a item
        self.assertGreater(len(r["secoes"][0][1]), 5)
        self.assertFalse(any("Ingesta" in l for l in r["secoes"][0][1]))

    def test_ficha_continua_com_ganhos_da_conta_do_motor(self):
        r = motor.compute_leito(self.leito, self.meta)
        _, bal = ficha_cola.linhas_controle(r, self.leito)
        self.assertEqual(bal[0], ("Ganhos", motor._fmt(r["balanco"]["ganho_total"])))

    def test_word_da_evolucao_tem_o_bloco_num_paragrafo(self):
        from docx import Document
        with tempfile.TemporaryDirectory() as tmp:
            caminho = Path(tmp) / "evo.docx"
            gerar_docx.gerar_evolucoes(EXEMPLO, caminho)
            pars = [p.text for p in Document(caminho).paragraphs]
        i = next(i for i, t in enumerate(pars) if t.startswith("Sinais vitais + balanço"))
        self.assertTrue(pars[i + 1].startswith("PAS: ") and " | BH: " in pars[i + 1])
        self.assertTrue(pars[i + 2].startswith("Laboratório"))

    def test_bomba_com_seta_nova(self):
        r = motor.compute_leito(self.leito, self.meta)
        nora = [l for l in r["secoes"][0][1] if l.startswith("Noradrenalina")]
        self.assertTrue(nora and "=>" in nora[0] and "->" not in nora[0], nora)

    def test_creatinina_com_as_duas_setas(self):
        import peso
        self.assertEqual(peso.creatinina(["UR: 58 => 72 mg/dl | CR: 1,3 => 1,7 mg/dl | NA: 138"]), (1.7, 1.3))
        self.assertEqual(peso.creatinina(["CR: 1,3 -> 1,7 mg/dl"]), (1.7, 1.3))  # evolução antiga


class FichaSemGlicemia(unittest.TestCase):
    def test_tira_aferição_e_correção(self):
        linhas = [["ENDÓCRINO", ["Synthroid (levotiroxina) 50 mcg => 05 · Humalog conforme Dx",
                                 "**G50% 4 amp EV se Dx < 70**"]],
                  ["SN", ["Dextrostix 6/6 h"]],
                  ["CV", ["AAS 100 mg => 13"]]]
        self.assertEqual(ficha_cola.sem_glicemia(linhas), [["ENDÓCRINO", ["Synthroid (levotiroxina) 50 mcg => 05"]],
                                                           ["CV", ["AAS 100 mg => 13"]]])

    def test_insulina_em_horário_fixo_fica(self):
        linhas = [["ENDÓCRINO", ["Lantus (glargina) 10 UI SC => 22", "Insulina regular em BIC 2 UI/h"]]]
        self.assertEqual(ficha_cola.sem_glicemia(linhas), linhas)


if __name__ == "__main__":
    unittest.main()
