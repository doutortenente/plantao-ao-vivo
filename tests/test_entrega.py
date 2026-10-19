# -*- coding: utf-8 -*-
"""entrega.py: histórico, diff e rascunho do chat. Rodar: python3 -m unittest discover -s tests"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "gerador"))
import entrega  # noqa: E402

EXEMPLO = json.loads((RAIZ / "gerador" / "exemplo" / "plantao-exemplo.json").read_text(encoding="utf-8"))
AVISOS = ["L99: ALERTA: alergia a Dipirona e dipirona prescrito (dipirona)",
          "L99: SpO2: 1 aferição(ões) ilegível(is) fora do Máx - Mín (23 h)"]


class Mensagem(unittest.TestCase):
    def test_formato(self):
        txt = entrega.mensagem(EXEMPLO, AVISOS, [Path("a.docx"), Path("b.docx")])
        primeira = txt.splitlines()[0]
        self.assertTrue(primeira.startswith("Saíram a evolução e a ficha-cola de 1 leito (a.docx, b.docx)"))
        self.assertIn("1 item para conferir", primeira)
        self.assertIn("- L99: alergia a Dipirona e dipirona prescrito (dipirona)", txt)
        self.assertIn("**Conferir**\n- L99: SpO2", txt)
        self.assertIn("- L99 Hemodinâmico: Noradrenalina para meta PAM >= 65 mmHg", txt)
        self.assertNotIn("Infeccioso", txt.split("**Conduta (metas)**")[1])  # sem meta numérica

    def test_erro_de_conferencia_vem_antes(self):
        txt = entrega.mensagem(EXEMPLO, [], [Path("a.docx")], ["ficha-cola com 2 página(s) para 1 leito(s)"])
        self.assertIn("**Não entregar ainda", txt)

    def test_alerta_nao_se_repete_na_reentrega(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "mensagem.md").write_text(entrega.mensagem(EXEMPLO, AVISOS, []), encoding="utf-8")
            txt = entrega.mensagem(EXEMPLO, AVISOS, [], historico=Path(tmp))
        self.assertNotIn("alergia a Dipirona e dipirona", txt)
        self.assertIn("3 alerta(s) já dado(s)", txt)


class Historico(unittest.TestCase):
    def test_guarda_e_compara(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "x.docx").write_text("v1"); (Path(tmp) / "evolucoes.txt").write_text("LEITO 01 — A\nPAS: 1\n")
            h = entrega.guardar_anterior(tmp, ["x.docx", "evolucoes.txt", "nao-existe.pdf"])
            self.assertTrue((h / "x.docx").exists())
            self.assertFalse((Path(tmp) / "x.docx").exists())
            mudou = entrega.diff_por_leito((h / "evolucoes.txt").read_text(), "LEITO 01 — A\nPAS: 2\n")
        self.assertEqual(mudou, {"01": ["-PAS: 1", "+PAS: 2"]})

    def test_nada_para_guardar(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(entrega.guardar_anterior(tmp, ["x.docx"]))


if __name__ == "__main__":
    unittest.main()
