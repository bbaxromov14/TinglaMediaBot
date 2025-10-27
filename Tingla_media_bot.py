import os
import telebot
import yt_dlp
import uuid
import requests
import acoustid
import subprocess
import logging
from mutagen.mp3 import MP3
from mutagen.id3 import APIC, TIT2, TPE1, ID3
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, BotCommand

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Получаем переменные из окружения Railway
BOT_TOKEN = os.environ['BOT_TOKEN']
RAPIDAPI_KEY = os.environ['RAPIDAPI_KEY']
ACOUSTID_API_KEY = os.environ['ACOUSTID_API_KEY']

bot = telebot.TeleBot(BOT_TOKEN)

# Глобальные переменные
user_langs = {}
user_tracks_cache = {}
user_search_results = {}
user_download_choices = {}

# Тексты (сокращенная версия для примера)
texts = {
    "uz_latn": {
        "welcome": "👋 *Salom, men TinglaMediaBotman!* ✅\n\n📌 *Imkoniyatlarim:*\n• Musiqa topish\n• Video va audio yuklab olish\n⬇️ Havolani yoki qo'shiq nomini yuboring.",
        "downloading": "⏳ Yuklanmoqda, iltimos kuting...",
        "success_audio": "✅ Musiqa yuklandi!",
        "error": "❌ Xatolik yuz berdi.",
        "choose_format": "📥 Formatni tanlang:",
        "format_video": "🎥 Video",
        "format_audio": "🎵 Audio",
    },
    "ru": {
        "welcome": "👋 *Привет! Я TinglaMediaBot!* ✅\n\n📌 *Мои возможности:*\n• Поиск музыки\n• Скачивание видео и аудио\n⬇️ Отправьте ссылку или название песни.",
        "downloading": "⏳ Загрузка, подождите...",
        "success_audio": "✅ Музыка загружена!",
        "error": "❌ Произошла ошибка.",
        "choose_format": "📥 Выберите формат:",
        "format_video": "🎥 Видео",
        "format_audio": "🎵 Аудио",
    }
}

country_maps = {
    'chartt_uz': 'UZ', 'chartt_ru': 'RU', 'chartt_us': 'US',
    'chartt_kz': 'KZ', 'chartt_tr': 'TR', 'chartt_az': 'AZ',
}

def get_lang(user_id):
    return user_langs.get(user_id, "uz_latn")

def is_supported_url(url):
    return any(domain in url for domain in ["youtube.com", "youtu.be", "instagram.com"])

def setup_ffmpeg():
    """Проверка и настройка FFmpeg"""
    try:
        result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("✅ FFmpeg найден")
            return True
        else:
            logger.error("❌ FFmpeg не найден")
            return False
    except Exception as e:
        logger.error(f"Ошибка проверки FFmpeg: {e}")
        return False

def download_media(url, media_type='audio'):
    """Универсальная функция для скачивания"""
    file_id = str(uuid.uuid4())[:8]
    
    if media_type == 'audio':
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'/tmp/{file_id}.%(ext)s',
            'quiet': True,
            'no_warnings': False,
            'ignoreerrors': True,
            'retries': 3,
            'fragment_retries': 3,
            'socket_timeout': 30,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
    else:  # video
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': f'/tmp/{file_id}.%(ext)s',
            'quiet': True,
            'no_warnings': False,
            'ignoreerrors': True,
            'retries': 3,
            'fragment_retries': 3,
            'socket_timeout': 30,
        }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if media_type == 'audio':
                filename = os.path.splitext(filename)[0] + '.mp3'
            
            logger.info(f"✅ Успешно скачан: {filename}")
            return filename
    except Exception as e:
        logger.error(f"❌ Ошибка скачивания: {e}")
        return None

def search_tracks(query, max_results=5):
    """Поиск треков"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'skip_download': True,
        'default_search': 'ytsearch',
        'extract_flat': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_result = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
            entries = search_result.get('entries', [])
            tracks = []
            for e in entries:
                if e:
                    tracks.append({
                        'id': e.get('id', ''),
                        'title': e.get('title', 'Unknown'),
                        'duration': e.get('duration', 0),
                    })
            return tracks
    except Exception as e:
        logger.error(f"❌ Ошибка поиска: {e}")
        return []

# Обработчики бота
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_langs[message.from_user.id] = "uz_latn"
    lang = get_lang(message.from_user.id)
    logger.info(f"Новый пользователь: {message.from_user.id}")
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("➕ Guruhga qo'shish", url="https://t.me/TinglaMediaBot?startgroup=true"))
    bot.send_message(message.chat.id, texts[lang]["welcome"], parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(commands=['lang'])
def ask_language(message):
    lang = get_lang(message.from_user.id)
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang_uz_latn"),
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru")
    )
    bot.send_message(message.chat.id, "Tilni tanlang / Выберите язык:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def set_language(call):
    lang_code = call.data.split("_", 1)[1]
    user_langs[call.from_user.id] = lang_code
    bot.answer_callback_query(call.id, "✅ Til o'zgartirildi / Язык изменен")
    bot.send_message(call.message.chat.id, texts[lang_code]["welcome"], parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    lang = get_lang(message.from_user.id)
    text = message.text.strip()
    logger.info(f"Сообщение от {message.from_user.id}: {text}")

    if text.startswith("http") and is_supported_url(text):
        user_download_choices[message.from_user.id] = {'url': text, 'format': None}
        
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton(texts[lang]["format_video"], callback_data="format_video"),
            InlineKeyboardButton(texts[lang]["format_audio"], callback_data="format_audio")
        )
        
        bot.send_message(message.chat.id, texts[lang]["choose_format"], reply_markup=markup)
        return

    # Поиск музыки
    loading_msg = bot.send_message(message.chat.id, texts[lang]["downloading"])
    tracks = search_tracks(text, max_results=5)
    bot.delete_message(message.chat.id, loading_msg.message_id)

    if not tracks:
        bot.send_message(message.chat.id, texts[lang]["error"])
        return

    user_search_results[message.from_user.id] = tracks

    msg_text = "Natijalar:\n\n"
    for i, track in enumerate(tracks, start=1):
        duration_str = f"{track['duration']//60}:{track['duration']%60:02d}" if track.get('duration') else "—"
        msg_text += f"{i}. {track['title']} ({duration_str})\n"

    markup = InlineKeyboardMarkup(row_width=3)
    buttons = [InlineKeyboardButton(str(i), callback_data=f"track_{i}") for i in range(1, len(tracks)+1)]
    markup.add(*buttons)

    bot.send_message(message.chat.id, msg_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["format_video", "format_audio"])
def handle_format_choice(call):
    lang = get_lang(call.from_user.id)
    user_data = user_download_choices.get(call.from_user.id)
    
    if not user_data:
        bot.answer_callback_query(call.id, "❌ Сессия истекла")
        return
    
    url = user_data['url']
    format_type = call.data
    
    bot.answer_callback_query(call.id, texts[lang]["downloading"])
    
    try:
        msg = bot.send_message(call.message.chat.id, "⏳ Yuklanmoqda...")
        
        if format_type == "format_video":
            filename = download_media(url, 'video')
            if filename and os.path.exists(filename):
                with open(filename, 'rb') as video:
                    bot.send_video(call.message.chat.id, video, caption=texts[lang]["success_audio"])
                os.remove(filename)
            else:
                bot.send_message(call.message.chat.id, "❌ Video yuklab bo'lmadi")
                
        elif format_type == "format_audio":
            filename = download_media(url, 'audio')
            if filename and os.path.exists(filename):
                with open(filename, 'rb') as audio:
                    bot.send_audio(call.message.chat.id, audio, caption=texts[lang]["success_audio"])
                os.remove(filename)
            else:
                bot.send_message(call.message.chat.id, "❌ Audio yuklab bo'lmadi")
        
        bot.delete_message(call.message.chat.id, msg.message_id)
            
    except Exception as e:
        logger.error(f"Ошибка обработки: {e}")
        bot.send_message(call.message.chat.id, texts[lang]["error"])

@bot.callback_query_handler(func=lambda call: call.data.startswith("track_"))
def send_selected_track(call):
    lang = get_lang(call.from_user.id)
    choice_str = call.data.split("_")[1]
    
    if not choice_str.isdigit():
        bot.answer_callback_query(call.id, "❌ Noto'g'ri tanlov")
        return

    choice = int(choice_str) - 1
    tracks = user_search_results.get(call.from_user.id)
    
    if not tracks or choice < 0 or choice >= len(tracks):
        bot.answer_callback_query(call.id, "❌ Noto'g'ri tanlov")
        return

    track = tracks[choice]
    bot.answer_callback_query(call.id, f"🎵 {track['title']} yuklanmoqda...")

    loading_msg = bot.send_message(call.message.chat.id, texts[lang]["downloading"])
    
    # Скачиваем аудио
    url = f"https://www.youtube.com/watch?v={track['id']}"
    filename = download_media(url, 'audio')
    
    bot.delete_message(call.message.chat.id, loading_msg.message_id)

    if filename:
        try:
            with open(filename, 'rb') as audio:
                bot.send_audio(call.message.chat.id, audio, caption=texts[lang]['success_audio'], title=track['title'])
            os.remove(filename)
        except Exception as e:
            logger.error(f"Ошибка отправки: {e}")
            bot.send_message(call.message.chat.id, "❌ Yuborishda xatolik")
    else:
        bot.send_message(call.message.chat.id, texts[lang]["error"])

# Запуск бота
if __name__ == "__main__":
    logger.info("🚀 Запуск бота...")
    
    # Проверка окружения
    if setup_ffmpeg():
        logger.info("✅ Окружение настроено правильно")
    else:
        logger.warning("⚠️ Проблемы с окружением")
    
    # Установка команд бота
    bot.set_my_commands([
        BotCommand("start", "Ботни ишга тушириш"),
        BotCommand("lang", "Тилни ўзгартириш"),
    ])
    
    logger.info("✅ Бот готов к работе")
    bot.infinity_polling(timeout=60, long_polling_timeout=30)