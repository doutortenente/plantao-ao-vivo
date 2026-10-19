# -*- coding: utf-8 -*-
"""Testes do gerador (entrada e saída do gerar_docx.py). Rodar: python3 -m unittest discover -s tests"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
EXEMPLO = RAIZ / "gerador" / "exemplo" / "plantao-exemplo.json"


def rodar(plantao, *extra):
    with tempfile.TemporaryDirectory() as tmp:
        js = Path(tmp) / "plantao.json"
        js.write_text(json.dumps(plantao, ensure_ascii=False), encoding="utf-8")
        r = subprocess.run([sys.executable, str(RAIZ / "gerador" / "gerar_docx.py"), str(js),
                            "--saida", str(Path(tmp) / "saida"), *extra], capture_output=True, text=True)
        saidas = sorted(p.name for p in (Path(tmp) / "saida").glob("*")) if (Path(tmp) / "saida").exists() else []
        return r, saidas


class FichaObrigatoria(unittest.TestCase):
    def test_leito_sem_ficha_para_com_erro(self):
        dados = json.loads(EXEMPLO.read_text(encoding="utf-8"))
        del dados["leitos"][0]["ficha"]
        r, saidas = rodar(dados, "--sem-ajuste")
        self.assertEqual(r.returncode, 2)
        self.assertIn("leito(s) 99 sem o bloco `ficha`", r.stderr)
        self.assertEqual(saidas, [])  # nada sai no modelo rejeitado

    def test_sem_ajuste_gera_os_dois(self):
        dados = json.loads(EXEMPLO.read_text(encoding="utf-8"))
        r, saidas = rodar(dados, "--sem-ajuste")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("01-01-26-uti2-evolucoes-diurno.docx", saidas)
        self.assertIn("01-01-26-uti2-ficha-cola-diurno.docx", saidas)


if __name__ == "__main__":
    unittest.main()
