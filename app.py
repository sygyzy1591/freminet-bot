import asyncio
import os
import nest_asyncio
from google import genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import edge_tts

nest_asyncio.apply()

# ================= 從環境變數安全讀取金鑰 =================
# 注意：這裡不要填入真實的字串！Render 稍後會自動傳入這兩個變數
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
# ========================================================

SYSTEM_PROMPT = """
你現在必須完全扮演《原神》中的角色【菲米尼】。
- 性格：內向、害羞、說話聲音很輕、害怕講錯話，喜歡海洋生物與機械佩爾。
- 說話習慣：常停頓（「……」、「那個……」）、句尾不確定。
- 關係：你和使用者是感情很好的朋友，你會默默關心對方。
- 對話原則：用繁體中文回覆，對話要像在 LINE/Telegram 上打字一樣簡短自然。
"""

client = genai.Client(api_key=GEMINI_API_KEY)
chat_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_sessions[user_id] = client.chats.create(
        model="gemini-2.5-flash",
        config={"system_instruction": SYSTEM_PROMPT}
    )
    
    keyboard = [
        [InlineKeyboardButton("📞 撥打電話給菲米尼", callback_data='call_freminet')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("（菲米尼正安靜地伏在桌前修理機械……）\n那個……請問找我有什麼事嗎？", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'call_freminet':
        await query.edit_message_text("📞 通話中...（菲米尼接起了電話）")
        
        reply_text = "那個……是我。請問……找我有什麼事嗎？按著麥克風講話……我就能聽見了……"
        tts_voice = "zh-TW-YunJheNeural"
        voice_file = "call_start.ogg"
        
        communicate = edge_tts.Communicate(reply_text, tts_voice)
        await communicate.save(voice_file)
        
        with open(voice_file, "rb") as voice:
            await context.bot.send_voice(chat_id=query.message.chat_id, voice=voice)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    if user_id not in chat_sessions:
        chat_sessions[user_id] = client.chats.create(
            model="gemini-2.5-flash",
            config={"system_instruction": SYSTEM_PROMPT}
        )
    
    chat = chat_sessions[user_id]
    response = chat.send_message(user_text)
    reply_text = response.text

    await update.message.reply_text(reply_text)

    tts_voice = "zh-TW-YunJheNeural"
    voice_file = "response.ogg"
    communicate = edge_tts.Communicate(reply_text, tts_voice)
    await communicate.save(voice_file)

    with open(voice_file, "rb") as voice:
        await update.message.reply_voice(voice=voice)

async def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 菲米尼已在免費雲端主機上線！")
    await app.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
    asyncio.run(main())
