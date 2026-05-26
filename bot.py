import os
import io
from flask import Flask
from threading import Thread
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Flask app for Railway
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Image to PDF Bot is running!", 200

@flask_app.route('/health')
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Image to PDF Bot*\n\nSend me any image and I'll convert it to PDF!",
        parse_mode='Markdown'
    )

async def convert_to_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("🔄 Converting your image to PDF...")
        
        # Get the image
        photo = await update.message.photo[-1].get_file()
        image_bytes = await photo.download_as_bytearray()
        
        # Open image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Create PDF
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=letter)
        width, height = letter
        
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        img_width, img_height = image.size
        ratio = min(width / img_width, height / img_height)
        new_width = img_width * ratio
        new_height = img_height * ratio
        x = (width - new_width) / 2
        y = (height - new_height) / 2
        
        temp_img = io.BytesIO()
        image.save(temp_img, format='PNG')
        temp_img.seek(0)
        
        c.drawImage(temp_img, x, y, new_width, new_height)
        c.save()
        
        pdf_buffer.seek(0)
        await update.message.reply_document(
            document=pdf_buffer,
            filename="image.pdf",
            caption="✅ Here's your PDF!"
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

def main():
    if not TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN not set!")
        return
    
    # Start Flask in background thread
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    print(f"✅ Flask server started")
    
    # Start Telegram bot
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, convert_to_pdf))
    
    print("🤖 Bot started! Waiting for messages...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
