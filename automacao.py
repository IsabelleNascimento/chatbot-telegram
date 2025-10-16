from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    ConversationHandler,
    filters
)

# Etapas da conversa
PEDIR_NOME, ESCOLHER_SETOR, ESCOLHER_OPCAO_FINANCEIRO, DECIDIR_O_QUE_FAZER,ESCOLHER_OPCAO_TECNICO, ESCOLHER_OPCAO_DUVIDAS = range(6)

# Token
from dotenv import load_dotenv
import os

load_dotenv()
chave_API = os.getenv("TELEGRAM_TOKEN")


# Etapa 1: Início da conversa
async def iniciar_conversa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Mensagem recebida (iniciar_conversa):", update.message.text)
    await update.message.reply_text("Olá! Antes de começarmos, qual é o seu nome?")
    return PEDIR_NOME

# Etapa 2: Receber nome e mostrar setores
async def receber_nome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nome = update.message.text
    context.user_data["nome"] = nome

    opcoes_setor = [
        ["Financeiro 💰", "Técnico 🛠️"],
        ["Dúvidas ❓", "Melhoria/Crítica 💡"],
        ["Alterar Plano 📦"]
    ]
    teclado = ReplyKeyboardMarkup(opcoes_setor, one_time_keyboard=True)

    await update.message.reply_text(
        f"Prazer, {nome}! Qual setor deseja conversar?",
        reply_markup=teclado
    )
    return ESCOLHER_SETOR

# Etapa 3: Receber setor e mostrar opções específicas
async def receber_setor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    setor = update.message.text.lower().strip()
    context.user_data["setor"] = setor

    if "financeiro" in setor:
        opcoes_financeiro = [
            ["Dúvidas sobre pagamento"],
            ["Segunda via do boleto"]
        ]
        teclado_financeiro = ReplyKeyboardMarkup(opcoes_financeiro, one_time_keyboard=True)

        await update.message.reply_text(
            "Escolha uma das opções abaixo:",
            reply_markup=teclado_financeiro
        )
        return ESCOLHER_OPCAO_FINANCEIRO
    
    elif "técnico" in setor:
        opcoes_tecnico = [
        ["Falar com suporte"],
        ["Gostaria do PDF com instruções de uso dos equipamentos"]
        ]
        teclado_tecnico = ReplyKeyboardMarkup(opcoes_tecnico, one_time_keyboard= True)
    
        await update.message.reply_text(
        "Certo! Como posso te ajudar na parte técnica? ", 
        reply_markup = teclado_tecnico
        )
        return ESCOLHER_OPCAO_TECNICO
    
    elif "dúvidas" in setor :
        opcoes_duvidas = [
            ["Como funciona o serviço"],
            ["Não sei operar o aparelho"]
        ]
        teclado_duvidas = ReplyKeyboardMarkup(opcoes_duvidas, one_time_keyboard= True)
        
        await update.message.reply_text(
            "Claro, Escolha uma das dúvidas abaixo: ",
            reply_markup=teclado_duvidas
        )
        return ESCOLHER_OPCAO_DUVIDAS
    
async def tratar_opcao_duvidas(update: Update, context: ContextTypes.DEFAULT_TYPE):
        escolha = update.message.text

        if "Como funciona" in escolha:
            await update.message.reply_text(
                "Nosso serviço funciona de forma simples: você escolhe o setor, seleciona sua necessidade e recebe atendimento personalizado. 😊"
            )
            await encerrar_atendimento(update)

        elif "operar" in escolha or "aparelho" in escolha:
            await update.message.reply_text(
                "Os prazos de entrega variam conforme o tipo de serviço, mas geralmente são de 3 a 5 dias úteis. 📦"
            )
            await encerrar_atendimento(update)

        else: 
            opcoes = [
            ["Escolher outro setor"],
            ["Encerrar atendimento"]
            ]
        teclado = ReplyKeyboardMarkup(opcoes, one_time_keyboard= True)

        await update.message.reply_text (
           
            reply_markup= teclado )
        return DECIDIR_O_QUE_FAZER


# Etapa 4: Decidir o que fazer após setor inválido
async def decidir_proximo_passo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    escolha = update.message.text

    if "Escolher outro setor" in escolha:
        opcoes_setor = [
            ["Financeiro 💰", "Técnico 🛠️"],
            ["Dúvidas ❓", "Melhoria/Crítica 💡"],
            ["Alterar Plano 📦"]
        ]
        teclado = ReplyKeyboardMarkup(opcoes_setor, one_time_keyboard=True)

        await update.message.reply_text(
            "Tudo bem! Escolha outro setor abaixo:",
            reply_markup=teclado
        )
        return ESCOLHER_SETOR

    elif "Encerrar atendimento" in escolha:
        await update.message.reply_text(
            "Atendimento encerrado. Se precisar de algo, é só chamar. Até mais! 👋"
        )
        return ConversationHandler.END

    else:
        await update.message.reply_text(
            "Desculpe, não entendi. Por favor, escolha uma das opções disponíveis."
        )
        return DECIDIR_O_QUE_FAZER

# Etapa 5: Tratar opções dentro do setor financeiro
async def tratar_opcao_financeiro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    escolha = update.message.text

    if "Dúvidas sobre pagamento" in escolha:
        await update.message.reply_text(
            "Certo! Um atendente do setor financeiro vai falar com você em instantes."
        )
    elif "Segunda via do boleto" in escolha:
        await update.message.reply_text(
            "Você pode acessar a segunda via do boleto diretamente pelo portal X: https://seuportal.com/boletos"
        )
    else:
        await update.message.reply_text(
            "Desculpe, não entendi. Por favor, escolha uma das opções disponíveis."
        )

    return ConversationHandler.END

async def tratar_opcao_tecnico(update: Update, context: ContextTypes.DEFAULT_TYPE):
    escolha = update.message.text

    if "Falar com suporte" in escolha:
        await update.message.reply_text("Um atendente técnico vai te ajudar em instantes. 🔧")
        await encerrar_atendimento(update)

    elif "PDF" in escolha or "instruções" in escolha:
        await update.message.reply_text("Aqui está o PDF: https://seusite.com/manual.pdf 📄")
        await encerrar_atendimento(update)

    else:
        opcoes = [["Escolher outro setor"], ["Encerrar atendimento"]]
        teclado = ReplyKeyboardMarkup(opcoes, one_time_keyboard=True)
        await update.message.reply_text("Desculpe, não entendi. O que você gostaria de fazer?", reply_markup=teclado)
        return DECIDIR_O_QUE_FAZER

    return ConversationHandler.END

# Diagnóstico: responder qualquer mensagem fora do fluxo
async def eco(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Mensagem recebida (eco):", update.message.text)
    await update.message.reply_text("Recebido!")

#Encerrar atendimento
async def encerrar_atendimento(update: Update):
    await update.message.reply_text(
        "Se precisar de mais alguma coisa, é só chamra. Até mais! "
    )

# Montando e ativando o bot
def main():
    app = ApplicationBuilder().token(chave_API).build()

    conversa = ConversationHandler(
        entry_points=[
            CommandHandler("start", iniciar_conversa),
            MessageHandler(filters.TEXT & ~filters.COMMAND, iniciar_conversa)
        ],
        states={
            PEDIR_NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_nome)],
            ESCOLHER_SETOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_setor)],
            ESCOLHER_OPCAO_FINANCEIRO: [MessageHandler(filters.TEXT & ~filters.COMMAND, tratar_opcao_financeiro)],
            ESCOLHER_OPCAO_TECNICO: [MessageHandler(filters.TEXT & ~filters.COMMAND, tratar_opcao_tecnico)],
            ESCOLHER_OPCAO_DUVIDAS: [MessageHandler(filters.TEXT & ~filters.COMMAND, tratar_opcao_duvidas)],
            DECIDIR_O_QUE_FAZER: [MessageHandler(filters.TEXT & ~filters.COMMAND, decidir_proximo_passo)],
        },
        fallbacks=[]
    )
    print("Entrando no main")

    app.add_handler(conversa)
    app.add_handler(MessageHandler(filters.TEXT, eco))

    print("Bot está rodando e ouvindo mensagens...")
    app.run_polling()

# Executando o bot
if __name__ == "__main__":
    main()
    





