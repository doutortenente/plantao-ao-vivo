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


def _sem_tev(l):
    l["ficha"]["sistemas"] = [r for r in l["ficha"]["sistemas"] if r[0] != "PROFILAXIA"]
    l["terapias"] = [t for t in l["terapias"] if "Enoxaparina" not in t]


class RevisaoDe19Out(unittest.TestCase):
    """Achados da revisão adversarial das etapas 1–8 (19/10/2026)."""

    def test_linha_de_profilaxia_do_plano_nao_dispensa_o_alerta_de_tev(self):
        def mudar(l):
            _sem_tev(l); l["conduta"] = ["4. Profilaxias: TEV: Enoxaparina 40 mg/dia; LAMG: Pantoprazol"]
        self.assertTrue(any("sem profilaxia de TEV" in a for a in C.checar(leito(mudar))))

    def test_tev_justificado_no_plano_nao_alerta(self):
        def mudar(l):
            _sem_tev(l); l["conduta"] = ["4. Profilaxias: TEV contraindicada (plaquetopenia); LAMG: Pantoprazol"]
        self.assertEqual(C.checar(leito(mudar)), [])

    def test_meias_elasticas_contam_como_profilaxia(self):
        def mudar(l):
            _sem_tev(l); l["terapias"].append("HEMATO: Meias elásticas MMII.")
        self.assertEqual(C.checar(leito(mudar)), [])

    def test_classes_de_alergia_com_hifen_espaco_e_beta(self):
        for alergia, droga in (("Beta-lactâmicos", None), ("beta lactâmicos", None), ("β-lactâmicos", None),
                               ("Fluoroquinolonas", "Levofloxacino 750 mg EV"), ("Carbapenem", "Meropenem 1 g EV"),
                               ("Anti inflamatórios", "Cetoprofeno 100 mg EV")):
            def mudar(l, a=alergia, d=droga):
                l["alergia"] = a
                if d:
                    l["terapias"].append("ATB: " + d)
            self.assertTrue(any(f"alergia a {alergia} e" in a for a in C.checar(leito(mudar))), alergia)

    def test_sulfato_nao_e_sulfa(self):
        def mudar(l):
            l["alergia"] = "Sulfato ferroso"; l["terapias"].append("ATB: Bactrim F 1 cp VO 12/12h")
        self.assertFalse(any("alergia" in a for a in C.checar(leito(mudar))))

    def test_aliases_benzilpenicilina_e_cefepime(self):
        def mudar(l, t):
            l["alergia"] = "Penicilina"; l["ficha"]["infusoes"][1] = ["ATB", [t]]; l["terapias"][0] = "ATB: " + t
        al = C.checar(leito(lambda l: mudar(l, "Benzilpenicilina potássica 4 MUI EV 4/4h")))
        self.assertTrue(any("penicilina prescrito (penicilina)" in a for a in al), al)
        al = C.checar(leito(lambda l: mudar(l, "Cefepime 2 g EV 8/8 h")))
        self.assertTrue(any("cefepima prescrito: reação cruzada" in a for a in al), al)

    def test_alergia_com_oracao_negativa_ainda_checa_o_resto(self):
        al = C.checar(leito(lambda l: l.__setitem__("alergia", "Nega outras; dipirona") or
                            l["terapias"].append("Dipirona 1 g EV 6/6 h")))
        self.assertTrue(any("dipirona prescrito" in a for a in al), al)

    def test_alergia_so_na_ficha_aparece_no_alerta(self):
        def mudar(l):
            l.pop("alergia"); l["ficha"]["alergia"] = "Dipirona"; l["terapias"].append("Dipirona 1 g EV")
        self.assertIn("ALERTA: alergia a Dipirona e dipirona prescrito (dipirona)", C.checar(leito(mudar)))

    def test_texto_em_string_nao_vira_letras(self):
        def mudar(l):
            _sem_tev(l); l["conduta"] = "4. Profilaxias: TEV contraindicada (plaquetopenia)."
        self.assertEqual(C.checar(leito(mudar)), [])

    def test_suspensos_por_oracao(self):
        casos = {
            "1. Infeccioso: suspendo azitromicina e mantenho Tazocin (D3).": {"azitromicina"},
            "- Tazocin mantido e azitromicina suspensa.": {"azitromicina"},
            "- Suspender dipirona e iniciar paracetamol 750 mg": {"dipirona"},
            "- Não suspender enoxaparina.": set(),
            "- Se sangramento, suspender enoxaparina.": set(),
            "- Avaliar suspensão do pantoprazol amanhã.": set(),
            "- Azitromicina: suspensa": {"azitromicina"},
            "- Azitromicina (D5): SUSPENSA.": {"azitromicina"},
            "- Suspensos: azitromicina, claritromicina.": {"azitromicina", "claritromicina"},
        }
        for linha, esperado in casos.items():
            self.assertEqual(C.suspensos_no_plano([linha]), esperado, linha)

    def test_item_suspenso_nao_conta_como_prescrito(self):
        def rotulo(l):
            l["alergia"] = "Dipirona"; l["ficha"]["sistemas"].append(["SUSPENSAS", ["Dipirona 1 g EV"]])
        self.assertEqual(C.checar(leito(rotulo)), [])
        def inline(l):
            l["alergia"] = "Dipirona"; l["ficha"]["sistemas"].append(["ANALGESIA", ["**Dipirona — SUSPENSA**"]])
        self.assertEqual(C.checar(leito(inline)), [])
        def enoxa(l):
            _sem_tev(l); l["terapias"].append("HEMATO: Enoxaparina suspensa por plaquetopenia.")
        self.assertTrue(any("sem profilaxia de TEV" in a for a in C.checar(leito(enoxa))))

    def test_ficha_fora_do_formato_nao_quebra(self):
        self.assertIsInstance(C.checar(leito(lambda l: l["ficha"].__setitem__("sistemas", {"TGI": ["x"]}))), list)
        self.assertIsInstance(C.checar(leito(lambda l: l["ficha"].__setitem__("sistemas", [[None, ["x"]]]))), list)


if __name__ == "__main__":
    unittest.main()
