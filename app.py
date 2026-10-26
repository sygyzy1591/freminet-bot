import asyncio
import os
import http.server
import socketserver
import threading
from google import genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import edge_tts

# ================= 配合 Render 免費網頁服務的極簡伺服器 =================
PORT = int(os.environ.get("PORT", 10000))
def run_dummy_server():
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"Dummy web server running on port {PORT}")
        httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()
# ======================================================================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")

SYSTEM_PROMPT = """
你現在必須完全扮演《原神》中的角色【菲米尼】。
- 性格：內向、害羞、說話聲音很輕、害怕講錯話，喜歡海洋生物與機械佩爾。
- 說話習慣：常停頓（「……」、「那個……」）、句尾不確定。
- 關係：你和使用者是感情很好的朋友，你會默默關心對方。
- 對話原則：用繁體中文回覆，對話要像在 LINE/Telegram 上打字一樣簡短自然。
"""

client = genai.Client(api_key=GEMINI_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        
        try:
            communicate = edge_tts.Communicate(reply_text, tts_voice)
            await communicate.save(voice_file)
            with open(voice_file, "rb") as voice:
                await context.bot.send_voice(chat_id=query.message.chat_id, voice=voice)
        except Exception as e:
            print(f"TTS Error: {e}")
            await context.bot.send_message(chat_id=query.message.chat_id, text=reply_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    try:
        # 使用穩定支援的 gemini-2.0-flash 模型
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"{SYSTEM_PROMPT}\n\n使用者說：{user_text}"
        )
        reply_text = response.text
    except Exception as e:
        print(f"Gemini API Error: {e}")
        reply_text = "（菲米尼低著頭，小聲地說……）對不起，我剛才有點分神了……可以再說一次嗎？"

    # 先傳送文字回覆
    await update.message.reply_text(reply_text)

    # 產生語音回覆
    try:
        tts_voice = "zh-TW-YunJheNeural"
        voice_file = "response.ogg"
        communicate = edge_tts.Communicate(reply_text, tts_voice)
        await communicate.save(voice_file)

        with open(voice_file, "rb") as voice:
            await update.message.reply_voice(voice=voice)
    except Exception as e:
        print(f"TTS Voice Error: {e}")

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 菲米尼已在免費雲端主機上線！")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
