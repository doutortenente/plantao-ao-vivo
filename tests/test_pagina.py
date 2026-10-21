# -*- coding: utf-8 -*-
"""Página de extração (extracao-web) × motor: o bloco da página e o motor rodando sobre o JSON que ela exporta têm
de dar os mesmos números. Precisa de node + playwright (Chromium); sem eles o teste é pulado.
Rodar: python3 -m unittest discover -s tests"""
import json
import os
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "gerador"))
sys.path.insert(0, str(RAIZ / "skills" / "sasi-ingest-export" / "scripts"))
import build_passagem as motor  # noqa: E402
import validar  # noqa: E402

PAGINA = RAIZ / "extracao-web" / "extracao-controles-labs-prescricao.html"


def _node_env():
    if not shutil.which("node") or not shutil.which("npm"):
        return None
    raiz_npm = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip()
    env = dict(os.environ, NODE_PATH=raiz_npm)
    ok = subprocess.run(["node", "-e", "require('playwright')"], env=env, capture_output=True).returncode == 0
    return env if ok else None


ENV = _node_env()


@unittest.skipUnless(ENV, "sem node + playwright")
class Pagina(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        r = subprocess.run(["node", str(RAIZ / "tests" / "pagina" / "teste_pagina.js"), str(PAGINA)], env=ENV,
                           capture_output=True, text=True, timeout=120)
        if r.returncode:
            raise unittest.SkipTest(f"Chromium não abriu: {r.stderr[-300:]}")
        saida = json.loads(r.stdout)
        cls.bed = saida["beds"][0]
        cls.plantao = json.loads(saida["json"])
        cls.noturno = saida["noturno"]

    def secao(self, texto):
        linhas = texto.split("\n")
        i = next(i for i, l in enumerate(linhas) if l.startswith("Sinais vitais + balanço"))
        fim = next((j for j in range(i + 1, len(linhas)) if not linhas[j].strip()), len(linhas))
        return linhas[i:fim]

    maxDiff = None

    def test_bloco_da_pagina_igual_ao_motor(self):
        texto, _ = motor.build(self.plantao)
        self.assertEqual(self.secao(self.bed["texto"]), self.secao(texto))

    def test_recorte_noturno_igual_ao_motor(self):
        plantao = json.loads(self.noturno["json"])
        self.assertEqual((plantao["meta"]["janela"], plantao["meta"]["recorte"]), ("12 h noturno", "noturno"))
        self.assertEqual(sorted(plantao["leitos"][0]["vitais"]["PAS"]), ["01", "03", "05", "19", "21", "23"])
        texto, _ = motor.build(plantao)
        self.assertEqual(self.secao(self.noturno["beds"][0]["texto"]), self.secao(texto))
        self.assertTrue(self.secao(texto)[0].startswith("Sinais vitais + balanço 12 h noturno"))

    def test_limiares_novos_e_duvida_fora_do_bloco(self):
        bloco = self.bed["texto"]
        self.assertIn("[1x < 70]", bloco)
        self.assertIn("[2x > 37,8]", bloco)
        self.assertIn("SpO2: 94 - 90 % (2L) [1x < 92]", bloco)  # suporte antes do flag, como o motor
        self.assertNotRegex(bloco, r"(?i)\(revisar|confirmar\)|⚠")
        self.assertTrue(any("leitura incerta" in p for p in self.bed["pend"]))
        self.assertTrue(any("BIC \"NORA\"" in p for p in self.bed["pend"]))

    def test_conta_pelas_celulas_e_rodape_so_confere(self):
        self.assertIn("Ingesta hídrica: 1.736 ml", self.bed["texto"])  # 12 × 50 + 12 × 3 + 100 + 1.000
        self.assertIn("BH: + 1.056 ml", self.bed["texto"])
        self.assertTrue(any("rodapé Ganhos diz 1.836, células somam 1.736" in p for p in self.bed["pend"]))

    def test_json_no_formato_do_schema(self):
        meta, leito = self.plantao["meta"], self.plantao["leitos"][0]
        self.assertEqual(meta, {"unidade": "UTI 2", "data": "01/01/2026", "turno": "diurno", "janela": "24 h",
                                "data_prescricao": "01/01"})
        self.assertEqual(list(leito["vitais"]["PAS"]), list(motor.SLOTS))  # horas na ordem da folha
        self.assertEqual(leito["vitais"]["SpO2"]["23"], "?")
        for item in leito["ganhos"] + leito["perdas"]:
            self.assertIsNotNone(motor.classify(item["nome"]), item["nome"])
        erros, _ = validar.validar({"meta": meta, "leitos": [dict(leito, dia_uti="D? UTI", dispositivos="?", ficha={
            "infusoes": [], "sistemas": [], "vigiar": [], "lab": []})]})
        self.assertEqual([e for e in erros if not re.search(r"ficha", e)], [])


if __name__ == "__main__":
    unittest.main()
