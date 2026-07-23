"""
registro.py

Registra cada interação relevante do bot em um CSV local (logs/interacoes.csv).

Esse log é o que permite, depois, construir uma analytics simples em cima do
atendimento: quantas conversas caem no fallback de IA, quais setores são mais
procurados, quantos atendimentos são resolvidos sem intervenção humana etc.
"""

import csv
import os
from datetime import datetime

CAMINHO_LOG = os.path.join(os.path.dirname(__file__), "logs", "interacoes.csv")

CABECALHO = ["timestamp", "nome", "setor", "mensagem", "resposta"]


def registrar(nome: str, setor: str, mensagem: str, resposta: str) -> None:
    """Adiciona uma linha ao log de interações, criando o arquivo se necessário."""
    os.makedirs(os.path.dirname(CAMINHO_LOG), exist_ok=True)
    arquivo_novo = not os.path.exists(CAMINHO_LOG)

    with open(CAMINHO_LOG, "a", newline="", encoding="utf-8") as arquivo:
        escritor = csv.writer(arquivo)
        if arquivo_novo:
            escritor.writerow(CABECALHO)
        escritor.writerow(
            [datetime.now().isoformat(timespec="seconds"), nome, setor, mensagem, resposta]
        )