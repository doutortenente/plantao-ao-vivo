"""Roda os testes em JavaScript do leitor de laudo do n8n (tests/exames_n8n.test.js) dentro do unittest do CI."""
import shutil
import subprocess
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


@unittest.skipUnless(shutil.which("node"), "node não instalado")
class TestExamesN8n(unittest.TestCase):
    def test_leitor_e_resposta(self):
        r = subprocess.run(["node", "--test", str(RAIZ / "tests" / "exames_n8n.test.js")],
                           capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stdout[-4000:] + r.stderr[-2000:])


if __name__ == "__main__":
    unittest.main()
