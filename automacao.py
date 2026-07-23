"""
bot.py

Chatbot de atendimento no Telegram com fluxo guiado por menus (ConversationHandler)
e um fallback inteligente via Gemini para quando o usuário escreve algo que não
bate exatamente com as opções do menu.

Fluxo:
1. Pergunta o nome do usuário.
2. Mostra os setores disponíveis (Financeiro, Técnico, Dúvidas).
3. Dentro de cada setor, mostra opções específicas.
4. Se o texto do usuário não bater com nenhuma opção esperada em qualquer etapa,
   o Gemini tenta classificar a intenção; se não conseguir, gera uma resposta
   cordial pedindo para escolher uma opção do menu.
"""

import logging
import os

from dotenv import load_dotenv
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import ai_helper
import registro

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Etapas da conversa
(
    PEDIR_NOME,
    ESCOLHER_SETOR,
    ESCOLHER_OPCAO_FINANCEIRO,
    ESCOLHER_OPCAO_TECNICO,
    ESCOLHER_OPCAO_DUVIDAS,
    DECIDIR_O_QUE_FAZER,
) = range(6)

TECLADO_SETORES = ReplyKeyboardMarkup(
    [
        ["Financeiro 💰", "Técnico 🛠️"],
        ["Dúvidas ❓"],
    ],
    one_time_keyboard=True,
)

TECLADO_PROXIMO_PASSO = ReplyKeyboardMarkup(
    [["Escolher outro setor"], ["Encerrar atendimento"]],
    one_time_keyboard=True,
)


# Etapa 1: início da conversa

async def iniciar_conversa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Nova conversa iniciada (usuário %s)", update.effective_user.id)
    await update.message.reply_text("Olá! Antes de começarmos, qual é o seu nome?")
    return PEDIR_NOME


# Etapa 2: recebe o nome e mostra os setores

async def receber_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nome = update.message.text.strip()
    context.user_data["nome"] = nome
    await update.message.reply_text(
        f"Prazer, {nome}! Qual setor deseja conversar?",
        reply_markup=TECLADO_SETORES,
    )
    return ESCOLHER_SETOR


# Etapa 3: recebe o setor (com fallback via Gemini se não reconhecer)
async def receber_setor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.lower().strip()

    if "financeiro" in texto:
        return await _entrar_financeiro(update, context)
    if "técnico" in texto or "tecnico" in texto:
        return await _entrar_tecnico(update, context)
    if "dúvidas" in texto or "duvidas" in texto:
        return await _entrar_duvidas(update, context)

    # Não bateu com nenhuma opção do menu: deixa o Gemini tentar entender
    nome = context.user_data.get("nome", "amigo(a)")
    categoria = ai_helper.classificar_intencao(update.message.text)
    registro.registrar(nome, "fallback_setor", update.message.text, categoria)

    if categoria == "financeiro":
        return await _entrar_financeiro(update, context)
    if categoria == "tecnico":
        return await _entrar_tecnico(update, context)
    if categoria == "duvidas":
        return await _entrar_duvidas(update, context)

    resposta_ia = ai_helper.responder_livre(update.message.text, nome)
    await update.message.reply_text(resposta_ia, reply_markup=TECLADO_SETORES)
    return ESCOLHER_SETOR


async def _entrar_financeiro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["setor"] = "financeiro"
    teclado = ReplyKeyboardMarkup(
        [["Dúvidas sobre pagamento"], ["Segunda via do boleto"]],
        one_time_keyboard=True,
    )
    await update.message.reply_text("Escolha uma das opções abaixo:", reply_markup=teclado)
    return ESCOLHER_OPCAO_FINANCEIRO


async def _entrar_tecnico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["setor"] = "tecnico"
    teclado = ReplyKeyboardMarkup(
        [["Falar com suporte"], ["PDF com instruções de uso"]],
        one_time_keyboard=True,
    )
    await update.message.reply_text(
        "Certo! Como posso te ajudar na parte técnica?", reply_markup=teclado
    )
    return ESCOLHER_OPCAO_TECNICO


async def _entrar_duvidas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["setor"] = "duvidas"
    teclado = ReplyKeyboardMarkup(
        [["Como funciona o serviço"], ["Não sei operar o aparelho"]],
        one_time_keyboard=True,
    )
    await update.message.reply_text(
        "Claro, escolha uma das dúvidas abaixo:", reply_markup=teclado
    )
    return ESCOLHER_OPCAO_DUVIDAS


# Etapa 4: opções dentro do setor Financeiro
async def tratar_opcao_financeiro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    escolha = update.message.text
    nome = context.user_data.get("nome", "amigo(a)")

    if "Dúvidas sobre pagamento" in escolha:
        resumo = ai_helper.resumir_para_atendente(nome, "financeiro", escolha)
        resposta = "Certo! Um atendente do setor financeiro vai falar com você em instantes."
        await update.message.reply_text(resposta)
        registro.registrar(nome, "financeiro", escolha, f"escalado | resumo_ia: {resumo}")
        return await encerrar_atendimento(update)

    if "Segunda via do boleto" in escolha:
        resposta = "Você pode acessar a segunda via do boleto pelo portal: https://seuportal.com/boletos"
        await update.message.reply_text(resposta)
        registro.registrar(nome, "financeiro", escolha, resposta)
        return await encerrar_atendimento(update)

    await update.message.reply_text(
        "Desculpe, não entendi. O que você gostaria de fazer?",
        reply_markup=TECLADO_PROXIMO_PASSO,
    )
    return DECIDIR_O_QUE_FAZER


# Etapa 4: opções dentro do setor Técnico
async def tratar_opcao_tecnico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    escolha = update.message.text
    nome = context.user_data.get("nome", "amigo(a)")

    if "Falar com suporte" in escolha:
        resumo = ai_helper.resumir_para_atendente(nome, "tecnico", escolha)
        resposta = "Um atendente técnico vai te ajudar em instantes. 🔧"
        await update.message.reply_text(resposta)
        registro.registrar(nome, "tecnico", escolha, f"escalado | resumo_ia: {resumo}")
        return await encerrar_atendimento(update)

    if "PDF" in escolha or "instruções" in escolha:
        resposta = "Aqui está o PDF: https://seusite.com/manual.pdf 📄"
        await update.message.reply_text(resposta)
        registro.registrar(nome, "tecnico", escolha, resposta)
        return await encerrar_atendimento(update)

    await update.message.reply_text(
        "Desculpe, não entendi. O que você gostaria de fazer?",
        reply_markup=TECLADO_PROXIMO_PASSO,
    )
    return DECIDIR_O_QUE_FAZER


# Etapa 4: opções dentro do setor Dúvidas
async def tratar_opcao_duvidas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    escolha = update.message.text
    nome = context.user_data.get("nome", "amigo(a)")

    if "Como funciona" in escolha:
        resposta = (
            "Nosso serviço funciona de forma simples: você escolhe o setor, "
            "seleciona sua necessidade e recebe atendimento personalizado. 😊"
        )
        await update.message.reply_text(resposta)
        registro.registrar(nome, "duvidas", escolha, resposta)
        return await encerrar_atendimento(update)

    if "operar" in escolha or "aparelho" in escolha:
        resposta = "Os prazos de entrega variam conforme o tipo de serviço, geralmente de 3 a 5 dias úteis. 📦"
        await update.message.reply_text(resposta)
        registro.registrar(nome, "duvidas", escolha, resposta)
        return await encerrar_atendimento(update)

    await update.message.reply_text(
        "Desculpe, não entendi. O que você gostaria de fazer?",
        reply_markup=TECLADO_PROXIMO_PASSO,
    )
    return DECIDIR_O_QUE_FAZER


# Etapa 5: decidir o que fazer após uma opção não reconhecida
async def decidir_proximo_passo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    escolha = update.message.text

    if "Escolher outro setor" in escolha:
        await update.message.reply_text(
            "Tudo bem! Escolha outro setor abaixo:", reply_markup=TECLADO_SETORES
        )
        return ESCOLHER_SETOR

    if "Encerrar atendimento" in escolha:
        return await encerrar_atendimento(update)

    await update.message.reply_text(
        "Desculpe, não entendi. Por favor, escolha uma das opções disponíveis.",
        reply_markup=TECLADO_PROXIMO_PASSO,
    )
    return DECIDIR_O_QUE_FAZER


# Encerramento e cancelamento
async def encerrar_atendimento(update: Update):
    await update.message.reply_text("Se precisar de mais alguma coisa, é só chamar. Até mais! 👋")
    return ConversationHandler.END


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Fallback global: garante que o usuário sempre tem uma saída da conversa."""
    await update.message.reply_text(
        "Atendimento cancelado. Quando quiser recomeçar, é só mandar /start."
    )
    return ConversationHandler.END


# Montagem e execução do bot
def main():
    if not TOKEN:
        raise RuntimeError(
            "TELEGRAM_TOKEN não encontrado. Configure o arquivo .env (veja .env.example)."
        )

    app = ApplicationBuilder().token(TOKEN).build()

    conversa = ConversationHandler(
        entry_points=[
            CommandHandler("start", iniciar_conversa),
            MessageHandler(filters.TEXT & ~filters.COMMAND, iniciar_conversa),
        ],
        states={
            PEDIR_NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_nome)],
            ESCOLHER_SETOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_setor)],
            ESCOLHER_OPCAO_FINANCEIRO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, tratar_opcao_financeiro)
            ],
            ESCOLHER_OPCAO_TECNICO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, tratar_opcao_tecnico)
            ],
            ESCOLHER_OPCAO_DUVIDAS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, tratar_opcao_duvidas)
            ],
            DECIDIR_O_QUE_FAZER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, decidir_proximo_passo)
            ],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
    )

    app.add_handler(conversa)
    logger.info("Bot iniciado e ouvindo mensagens...")
    app.run_polling()


if __name__ == "__main__":
    main()





