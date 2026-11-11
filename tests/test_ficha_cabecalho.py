# -*- coding: utf-8 -*-
"""Cabeçalho da ficha-cola: Idade/Sexo/Peso/Altura/HD e balanço sem Ganhos."""
import copy
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

EXEMPLO = RAIZ / "gerador" / "exemplo" / "plantao-exemplo.json"


def texto_ficha(dados):
    from docx import Document
    with tempfile.TemporaryDirectory() as tmp:
        cola = Path(tmp) / "cola.docx"
        ficha_cola.gerar(dados, cola, {})
        return "\n".join(
            p.text for p in Document(str(cola)).element.body.iter() if hasattr(p, "text") and p.text)


class IdadeSexo(unittest.TestCase):
    def test_idade_sexo_ficha(self):
        self.assertEqual(ficha_cola.idade_sexo_ficha("76M"), ("76 anos", "masculino"))
        self.assertEqual(ficha_cola.idade_sexo_ficha("90F"), ("90 anos", "feminino"))
        self.assertEqual(ficha_cola.idade_sexo_ficha("?")[1], "?")


class CabecalhoDocx(unittest.TestCase):
    def test_rotulos_e_sem_ganhos_no_exemplo(self):
        dados = json.loads(EXEMPLO.read_text(encoding="utf-8"))
        txt = texto_ficha(dados)
        for pedaco in ("Idade:  60 anos", "Sexo:  masculino", "Peso:  70 kg", "Altura:  172 cm",
                       "HD:", "Pneumonia comunitária", "Disp.:"):
            self.assertIn(pedaco, txt, msg=pedaco)
        self.assertNotIn("balança", txt)
        self.assertNotIn("Ganhos", txt)
        self.assertNotIn("60M", txt)
        self.assertNotIn("90F", txt)

    def test_peso_sem_altura_mostra_interrogacao(self):
        dados = json.loads(EXEMPLO.read_text(encoding="utf-8"))
        l = copy.deepcopy(dados["leitos"][0])
        l["peso"] = {"kg": 70, "fonte": "leito", "data": "01/01/2026"}
        txt = texto_ficha({"meta": dados["meta"], "leitos": [l]})
        self.assertIn("Peso:  70 kg", txt)
        self.assertIn("Altura:  ?", txt)

    def test_sem_bloco_peso_mostra_interrogacao_nas_duas_linhas(self):
        dados = json.loads(EXEMPLO.read_text(encoding="utf-8"))
        l = copy.deepcopy(dados["leitos"][0])
        l.pop("peso", None)
        txt = texto_ficha({"meta": dados["meta"], "leitos": [l]})
        self.assertIn("Peso:  ?", txt)
        self.assertIn("Altura:  ?", txt)

    def test_somente_altura_no_json_sem_peso_valido_para_motor(self):
        dados = json.loads(EXEMPLO.read_text(encoding="utf-8"))
        l = copy.deepcopy(dados["leitos"][0])
        l["peso"] = {"altura_cm": 165}
        txt = texto_ficha({"meta": dados["meta"], "leitos": [l]})
        self.assertIn("Peso:  ?", txt)
        self.assertIn("Altura:  165 cm", txt)


class Balanco(unittest.TestCase):
    def test_sem_ganhos(self):
        dados = json.loads(EXEMPLO.read_text(encoding="utf-8"))
        l = dados["leitos"][0]
        r = motor.compute_leito(l, dados["meta"])
        _, bal = ficha_cola.linhas_controle(r, l)
        self.assertFalse(any(k == "Ganhos" for k, _ in bal))


if __name__ == "__main__":
    unittest.main()
