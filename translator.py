import os
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from googletrans import Translator
import re
import logging
import asyncio
import wave
import subprocess
from vosk import Model, KaldiRecognizer

# Инициализация логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token="7414886214:AAFVmDPO4yE1Ywvj7aWvsVGuc25935z40XU")
dp = Dispatcher()

# Инициализация переводчика
translator = Translator()

# Регулярное выражение для обнаружения URL
url_pattern = re.compile(r'https?://\S+|www\.\S+')

# Инициализация моделей Vosk
model_ru = Model(r"C:\Users\Pc2\Desktop\translator_bot\vosk-model-small-ru-0.22")
model_en = Model(r"C:\Users\Pc2\Desktop\translator_bot\vosk-model-small-en-us-0.15")

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

def convert_oga_to_wav(file_path):
    wav_path = file_path.replace('.oga', '.wav')
    command = f"ffmpeg -i {file_path} -ac 1 -ar 16000 {wav_path}"
    subprocess.run(command, shell=True, check=True)
    
    # Проверка формата выходного файла
    with wave.open(wav_path, "rb") as wf:
        logging.info(f"Channels: {wf.getnchannels()}, Sample Width: {wf.getsampwidth()}, Frame Rate: {wf.getframerate()}")
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
            raise ValueError("Конвертация не удалась: Audio file must be WAV format mono PCM with 16000 Hz sample rate.")
    
    return wav_path

def recognize_speech(file_path):
    wav_path = convert_oga_to_wav(file_path)
    
    results = {'ru': None, 'en': None}
    for lang, model in [('ru', model_ru), ('en', model_en)]:
        wf = wave.open(wav_path, "rb")
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
            raise ValueError("Audio file must be WAV format mono PCM with 16000 Hz sample rate.")
        
        recognizer = KaldiRecognizer(model, wf.getframerate())
        
        result = []
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if recognizer.AcceptWaveform(data):
                result.append(recognizer.Result())
        
        final_result = recognizer.FinalResult()
        result.append(final_result)
        
        result_text = " ".join([eval(res)['text'] for res in result])
        
        wf.close()
        
        if result_text.strip():
            results[lang] = result_text.strip()
    
    os.remove(file_path)  # Удаление временного файла .oga
    os.remove(wav_path)   # Удаление временного файла .wav
    
    return results

@dp.message()
async def handle_message(message: types.Message):
    if message.voice:
        file_id = message.voice.file_id
        file = await bot.get_file(file_id)
        file_path = file.file_path

        # Скачивание голосового файла
        local_oga_path = 'voice.oga'
        await bot.download_file(file_path, local_oga_path)

        # Распознавание речи
        try:
            results = recognize_speech(local_oga_path)
            text_ru = results['ru']
            text_en = results['en']
            
            if text_ru:
                translated_text_ru = translate_text(text_ru, src='ru', dest='en')
                await message.reply(translated_text_ru, parse_mode=ParseMode.MARKDOWN)
            else:
                await message.reply("Русская модель не смогла распознать текст.")
            
            if text_en:
                translated_text_en = translate_text(text_en, src='en', dest='ru')
                await message.reply(translated_text_en, parse_mode=ParseMode.MARKDOWN)
            else:
                await message.reply("Английская модель не смогла распознать текст.")
                
        except Exception as e:
            await message.reply(f"Ошибка при распознавании аудио: {e}")
        finally:
            # Удаление временного файла
            if os.path.exists(local_oga_path):
                os.remove(local_oga_path)

    elif message.text:
        text = message.text
        src_lang = detect_language(text)
        dest_lang = 'en' if src_lang == 'ru' else 'ru'
        translated_text = translate_text(text, src=src_lang, dest=dest_lang)
        await message.reply(translated_text, parse_mode=ParseMode.MARKDOWN)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())










