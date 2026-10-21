# -*- coding: utf-8 -*-
"""Teste de doutrina: docs e skills não podem contradizer o BRIEFING nem o motor.

Cada regra aqui já custou uma entrega (docs/DECISOES.md). Se este teste falhar, o texto que ele aponta voltou a
ensinar a coisa errada: corrija o texto, não o teste.
"""
import re
import subprocess
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "skills" / "sasi-ingest-export" / "scripts"))
import build_passagem as motor  # noqa: E402

# textos que ensinam o formato (amostras OCR e o histórico de decisões ficam de fora)
DOUTRINA = [p for p in RAIZ.rglob("*.md")
            if "amostras" not in p.parts and p.name != "DECISOES.md" and ".git" not in p.parts]
LIMIARES_EM = [RAIZ / "docs" / "BRIEFING.md", RAIZ / "skills" / "controles-vitais-janela" / "SKILL.md",
               RAIZ / "extracao-web" / "README.md"]


def ler(p):
    return p.read_text(encoding="utf-8")


class Doutrina(unittest.TestCase):
    def test_limiares_do_motor_estao_nos_docs(self):
        numeros = {re.sub(r"[<> ]", "", lab) for regras in motor.LIMIARES.values() for _, _, lab in regras}
        for p in LIMIARES_EM:
            txt = ler(p)
            for n in numeros:
                self.assertRegex(txt, r"[<>]\s*`?\s*" + re.escape(n) + r"\b",
                                 f"{p.relative_to(RAIZ)} não tem o limiar {n} do motor (LIMIARES)")

    def test_rodape_nao_e_verdade(self):
        for p in DOUTRINA:
            self.assertNotRegex(ler(p), r"(?i)verdade confi",
                                f"{p.relative_to(RAIZ)}: rodapé tratado como verdade (balanço = soma das células)")

    def test_maximo_minimo_sem_travessao(self):
        padrao = re.compile(r"\b(PAS|PAD|PAM|FC|FR|SpO2|TAX):\s*\d+\s?[–—]\s?\d")  # linha do bloco
        for p in DOUTRINA:
            m = padrao.search(ler(p))
            self.assertIsNone(m, f"{p.relative_to(RAIZ)}: Máx - Mín com travessão: {m and m.group(0)}")

    def test_nada_de_marca_dentro_do_bloco(self):
        for p in DOUTRINA:
            txt = ler(p)
            for proibido in (r"marca\w*\s+`?\(?revisar", r"\(CONFIRMAR\)", r"\bnomear \+ `CONFIRMAR`",
                             r"vermelho na ficha"):
                m = re.search(proibido, txt, re.I)
                self.assertIsNone(m, f"{p.relative_to(RAIZ)}: ensina marca proibida no bloco: {m and m.group(0)}")

    def test_pagina_de_extracao_sem_marca_no_bloco_e_com_os_limiares(self):
        js = ler(RAIZ / "extracao-web" / "extracao-controles-labs-prescricao.html")
        for proibido in ('" (revisar)"', '(REVISAR OCR)', '(CONFIRMAR)', '"⚠'):
            self.assertNotIn(proibido, js, f"página de extração põe {proibido} no bloco")
        for op, n in ((">", "37.8"), ("<", "70")):
            self.assertRegex(js, r'\["' + re.escape(op) + r'",\s*' + re.escape(n) + r"\]",
                             f"página de extração sem o limiar {op} {n} do motor")

    def test_sasi_so_com_pedido_explicito(self):
        cab = ler(RAIZ / "skills" / "sasi-ingest-export" / "SKILL.md").split("---")[1]
        self.assertIn("SÓ com pedido explícito", cab)

    def test_versao_das_instrucoes_no_decisoes(self):
        versao = re.search(r"v(\d+\.\d+)", ler(RAIZ / "docs" / "instrucoes-projeto.md").splitlines()[0]).group(1)
        self.assertIn(f"v{versao}", ler(RAIZ / "docs" / "DECISOES.md"))

    def test_nenhum_dado_de_plantao_versionado(self):
        try:
            arquivos = subprocess.run(["git", "-C", str(RAIZ), "ls-files"], capture_output=True, text=True,
                                      check=True).stdout.split()
        except (OSError, subprocess.CalledProcessError):
            self.skipTest("sem git")
        permitidos = ("gerador/exemplo/", "skills/sasi-ingest-export/assets/", "tests/fixtures/")
        dados = [a for a in arquivos if re.search(r"\.(json|docx|pdf)$", a) and not a.startswith(permitidos)]
        self.assertEqual(dados, [], "JSON/Word/PDF de plantão versionado (só exemplos fictícios)")


if __name__ == "__main__":
    unittest.main()
