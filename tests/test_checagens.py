# -*- coding: utf-8 -*-
"""Testes dos cruzamentos de segurança. Rodar: python3 -m unittest discover -s tests"""
import copy
import json
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "skills" / "sasi-ingest-export" / "scripts"))
import build_passagem as motor  # noqa: E402
import checagens as C  # noqa: E402

EXEMPLO = json.loads((RAIZ / "gerador" / "exemplo" / "plantao-exemplo.json").read_text(encoding="utf-8"))


def leito(mudar=None):
    l = copy.deepcopy(EXEMPLO["leitos"][0])
    if mudar:
        mudar(l)
    return l


class Alergia(unittest.TestCase):
    def test_exemplo_sem_alerta(self):
        self.assertEqual(C.checar(leito()), [])

    def test_caso_antigo_dipirona_com_novalgina(self):
        al = C.checar(leito(lambda l: l["ficha"]["sistemas"].append(
            ["ANALGESIA", ["Novalgina (dipirona) 1 g EV 6/6 h => 10-16-22-04"]])))
        self.assertTrue(any("alergia a Dipirona e dipirona prescrito" in a for a in al), al)

    def test_classe_e_reacao_cruzada(self):
        def mudar(l):
            l["alergia"] = "Penicilina"
            l["ficha"]["infusoes"][1] = ["ATB", ["Rocefin (ceftriaxona) 2 g EV 1x/dia"]]
            l["terapias"][0] = "ATB: Rocefin 2 g EV 1x/dia."
        al = "\n".join(C.checar(leito(mudar)))
        self.assertIn("ceftriaxona prescrito: reação cruzada possível", al)
        al = "\n".join(C.checar(leito(lambda l: l.__setitem__("alergia", "AINEs"))) +
                       C.checar(leito(lambda l: (l.__setitem__("alergia", "AINEs"),
                                                 l["terapias"].append("ANALGESIA: Cetoprofeno 100 mg EV 12/12h")))))
        self.assertIn("cetoprofeno prescrito (aine)", al)

    def test_nega_nao_alerta(self):
        self.assertEqual(C.checar(leito(lambda l: l.__setitem__("alergia", "Nega"))), [])


class TevEDuplicidade(unittest.TestCase):
    def test_sem_tev(self):
        def mudar(l):
            l["ficha"]["sistemas"] = [s for s in l["ficha"]["sistemas"] if s[0] != "PROFILAXIA"]
            l["terapias"] = [t for t in l["terapias"] if "Enoxaparina" not in t]
            l["conduta"] = [c for c in l["conduta"] if "Profilax" not in c]
        self.assertTrue(any("sem profilaxia de TEV" in a for a in C.checar(leito(mudar))))

    def test_plano_que_fala_de_tev_nao_alerta(self):
        def mudar(l):
            l["ficha"]["sistemas"] = [s for s in l["ficha"]["sistemas"] if s[0] != "PROFILAXIA"]
            l["terapias"] = [t for t in l["terapias"] if "Enoxaparina" not in t]
            l["conduta"][-1] = "4. Profilaxias: TEV: contraindicada (plaquetopenia); LAMG: pantoprazol."
        self.assertEqual(C.checar(leito(mudar)), [])

    def test_dois_ibp(self):
        al = C.checar(leito(lambda l: l["ficha"]["sistemas"].append(["TGI", ["Omeprazol 40 mg VO"]])))
        self.assertTrue(any("dois IBP" in a for a in al), al)


class Suspenso(unittest.TestCase):
    def test_suspenso_no_plano_anterior(self):
        al = C.checar(leito(lambda l: l.__setitem__("plano_anterior", ["1. Infeccioso: Suspendo Azitromicina (D2)."])))
        self.assertTrue(any("suspender azitromicina" in a for a in al), al)

    def test_suspenso_que_saiu_da_prescricao(self):
        def mudar(l):
            l["plano_anterior"] = ["- Azitromicina suspensa."]
            l["ficha"]["infusoes"][1][1] = [l["ficha"]["infusoes"][1][1][0]]
            l["ficha"]["sistemas"].append(["SUSPENSOS", ["Azitromicina"]])
        self.assertEqual(C.checar(leito(mudar)), [])


class NoMotor(unittest.TestCase):
    def test_alerta_sai_no_topo_dos_avisos(self):
        dados = copy.deepcopy(EXEMPLO)
        dados["leitos"][0]["ficha"]["sistemas"].append(["ANALGESIA", ["Novalgina (dipirona) 1 g EV"]])
        _, avisos = motor.build(dados)
        self.assertTrue(avisos[0].startswith("L99: ALERTA: alergia"), avisos)


if __name__ == "__main__":
    unittest.main()
