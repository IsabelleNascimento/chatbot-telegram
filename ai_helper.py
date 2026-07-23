"""
ai_helper.py

Camada de integração com a API do Gemini (Google GenAI).

Responsabilidades:
- Classificar mensagens que não bateram com o menu fixo, tentando encaixá-las
  em um dos setores conhecidos (financeiro, tecnico, duvidas).
- Gerar uma resposta cordial quando nem o menu, nem a classificação, resolvem.
- Gerar um resumo curto para o atendente humano quando o atendimento escala.

Todas as funções têm fallback silencioso: se a chamada à IA falhar (rate limit,
sem internet, chave inválida etc.), o bot continua funcionando com uma resposta
padrão, sem quebrar a conversa do usuário.
"""

import logging
import os

from google import genai

logger = logging.getLogger(__name__)

# Nome do modelo configurável via .env, para facilitar troca quando o Google
# atualizar os modelos disponíveis no free tier.
MODELO = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

_client = None


def _get_client():
    """Cria o client do Gemini de forma preguiçosa (lazy), só na primeira chamada."""
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY não encontrada. Configure o arquivo .env "
                "(veja .env.example)."
            )
        _client = genai.Client(api_key=api_key)
    return _client


def classificar_intencao(mensagem: str) -> str:
    """
    Tenta encaixar uma mensagem livre em um dos setores conhecidos do menu.

    Retorna uma destas strings: 'financeiro', 'tecnico', 'duvidas' ou 'indefinido'.
    """
    prompt = (
        "Classifique a mensagem de um usuário de chatbot de atendimento em "
        "APENAS UMA destas categorias, respondendo só com a palavra da "
        "categoria, sem pontuação e sem explicação: "
        "financeiro, tecnico, duvidas, indefinido.\n\n"
        f'Mensagem do usuário: "{mensagem}"'
    )
    try:
        resposta = _get_client().models.generate_content(
            model=MODELO,
            contents=prompt,
        )
        categoria = (resposta.text or "").strip().lower()
        if categoria not in {"financeiro", "tecnico", "duvidas"}:
            categoria = "indefinido"
        return categoria
    except Exception as erro:  # nunca deixamos a IA derrubar o bot
        logger.warning("Falha ao classificar intenção via Gemini: %s", erro)
        return "indefinido"


def responder_livre(mensagem: str, nome: str) -> str:
    """
    Gera uma resposta curta e cordial quando não foi possível identificar
    o setor desejado, redirecionando o usuário de volta ao menu.
    """
    prompt = (
        f"Você é um assistente de atendimento ao cliente. O usuário se chama "
        f"{nome} e escreveu: \"{mensagem}\". Responda em português, em até 2 "
        "frases curtas, de forma cordial, dizendo que não entendeu totalmente "
        "o pedido e convidando a pessoa a escolher uma das opções do menu."
    )
    try:
        resposta = _get_client().models.generate_content(
            model=MODELO,
            contents=prompt,
        )
        texto = (resposta.text or "").strip()
        return texto or _resposta_padrao()
    except Exception as erro:
        logger.warning("Falha ao gerar resposta livre via Gemini: %s", erro)
        return _resposta_padrao()


def resumir_para_atendente(nome: str, setor: str, pedido: str) -> str:
    """
    Gera um resumo curto de 1 frase para o atendente humano que vai assumir
    a conversa, poupando o tempo dele de reler todo o histórico.
    """
    prompt = (
        f"Resuma em uma frase, para um atendente humano, o seguinte "
        f"atendimento: cliente {nome}, setor {setor}, pedido: \"{pedido}\". "
        "Seja direto, em português."
    )
    try:
        resposta = _get_client().models.generate_content(
            model=MODELO,
            contents=prompt,
        )
        return (resposta.text or "").strip() or pedido
    except Exception as erro:
        logger.warning("Falha ao gerar resumo via Gemini: %s", erro)
        return pedido


def _resposta_padrao() -> str:
    return "Desculpe, não consegui entender. Pode escolher uma das opções do menu?"