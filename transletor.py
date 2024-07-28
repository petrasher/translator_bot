from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from googletrans import Translator
import re
import logging
import asyncio

logging.basicConfig(level=logging.INFO)

bot = Bot(token="7414886214:AAFVmDPO4yE1Ywvj7aWvsVGuc25935z40XU")

dp = Dispatcher()

translator = Translator()

# Regular expression to detect URLs
url_pattern = re.compile(r'https?://\S+|www\.\S+')

def detect_language(text):
    if re.search(r'[а-яА-Я]', text):
        return 'ru'
    else:
        return 'en'

def translate_text(text, src, dest):
    urls = url_pattern.findall(text)
    text_without_urls = url_pattern.sub('URL', text)
    
    translated = translator.translate(text_without_urls, src=src, dest=dest).text
    
    for url in urls:
        translated = translated.replace('URL', url, 1)
    
    return translated

@dp.message()
async def handle_message(message: types.Message):
    text = message.text
    src_lang = detect_language(text)
    dest_lang = 'en' if src_lang == 'ru' else 'ru'

    translated_text = translate_text(text, src=src_lang, dest=dest_lang)
    await message.reply(translated_text, parse_mode=ParseMode.MARKDOWN)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

