# -*- coding: utf-8 -*-
"""Regras da sincronização com o OneDrive (sync/plantao_sync.py). Rodar: python3 -m unittest discover -s tests"""
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "sync"))
import plantao_sync as S  # noqa: E402

AGORA = datetime(2026, 11, 22, 13, 0, tzinfo=timezone.utc)
VELHA = AGORA - timedelta(days=5)


class Arquivar(unittest.TestCase):
    def test_fica_so_o_plantao_mais_recente(self):
        pastas = ["21-11-26-uti2-not", "14-11-26- UTI 2-not", "17-10-26-UTI2-not", "Leia-me"]
        mexida = {"14-11-26- UTI 2-not": VELHA, "17-10-26-UTI2-not": VELHA}
        self.assertEqual(S.a_arquivar(pastas, mexida, AGORA), ["17-10-26-UTI2-not", "14-11-26- UTI 2-not"])

    def test_pasta_antiga_mexida_ha_pouco_espera(self):
        # plantão novo criado, mas o anterior ainda recebeu output há 2 h: fica até 12 h quieto
        pastas = ["28-11-26-uti2-not", "21-11-26-uti2-not"]
        mexida = {"21-11-26-uti2-not": AGORA - timedelta(hours=2)}
        self.assertEqual(S.a_arquivar(pastas, mexida, AGORA), [])

    def test_uma_pasta_so_nao_mexe(self):
        self.assertEqual(S.a_arquivar(["21-11-26-uti2-not"], {}, AGORA), [])

    def test_sem_data_no_nome_nao_e_tocada(self):
        self.assertIsNone(S.data_da_pasta("outputs"))
        self.assertIsNone(S.data_da_pasta("31-02-26-x"))  # data impossível
        self.assertEqual(str(S.data_da_pasta("22-11-26-uti2-diurno")), "2026-11-22")


class Subir(unittest.TestCase):
    def test_outputs_vao_para_onde_a_pasta_esta(self):
        self.assertEqual(S.destino_da_saida("21-11-26-uti2-not", ["21-11-26-uti2-not"], []),
                         f"{S.REMOTO}/21-11-26-uti2-not/outputs")
        self.assertEqual(S.destino_da_saida("14-11-26-not", [], ["14-11-26-not"]),
                         f"{S.HISTORICO}/14-11-26-not/outputs")
        self.assertIsNone(S.destino_da_saida("pasta-local-so", ["a"], ["b"]))  # não cria pasta no OneDrive


if __name__ == "__main__":
    unittest.main()
