import telebot
import yt_dlp
import os
import uuid
from dotenv import load_dotenv
from telebot.types import BotCommand
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton


load_dotenv()
TOKEN = os.getenv("TOKEN")

bot = telebot.TeleBot(TOKEN)

user_langs = {}  # user_id: lang_code
user_search_results = {}  # user_id: list of search entries

texts = {
    "uz_latn": {
        "welcome": (
            "👋 *Salom, men TinglaMediaBotman!* ✅\n\n"
            "📌 *Imkoniyatlarim:*\n"
            "• Qo‘shiq nomi yoki matni orqali musiqa topaman\n"
            "• Instagram va YouTube'dan video va musiqa yuklab beraman\n"
            "⬇️ Havolani yoki qo‘shiq nomini yuboring."
        ),
        "send_link": "❗ Iltimos, havola yoki qo‘shiq nomini yuboring.",
        "unsupported": "❌ Bu platforma hozircha qo‘llab-quvvatlanmaydi.",
        "downloading": "⏳ Yuklanmoqda, iltimos kuting...",
        "success_video": "✅ Video muvaffaqiyatli yuklandi!\n\n🎧 @TinglaMediaBot'dan foydalanganingiz uchun rahmat!",
        "success_audio": "✅ Musiqa topildi va yuborildi!\n\n🎧 @TinglaMediaBot'dan foydalanganingiz uchun rahmat!",
        "error": "❌ Xatolik yuz berdi yoki musiqani topib bo‘lmadi.",
        "send_fail": "❌ Faylni yuborishda xatolik yuz berdi.",
        "change_lang": "Tilni tanlang:",
        "choose_track": "Quyidagi natijalardan musiqani tanlang:\n\n",
        "invalid_choice": "❌ Noto‘g‘ri tanlov, iltimos raqamni to‘g‘ri tanlang.",
    },
    "uz_cyrl": {
        "welcome": (
            "👋 *Салом, мен TinglaMediaBotман!* ✅\n\n"
            "📌 *Иқтидорларим:*\n"
            "• Қўшиқ номи ёки матни орқали мусиқани топаман\n"
            "• Instagram ва YouTubeдан видео ва мусиқани юклаб бераман\n"
            "⬇️ Ҳавола ёки қўшиқ номини юборинг."
        ),
        "send_link": "❗ Илтимос, ҳавола ёки қўшиқ номини юборинг.",
        "unsupported": "❌ Бу платформа ҳозирча қўллаб-қувватланмайди.",
        "downloading": "⏳ Юкланмоқда, илтимос кутиб туринг...",
        "success_video": "✅ Видео муваффақиятли юкланди!\n\n🎧 @TinglaMediaBotдан фойдаланганингиз учун раҳмат!",
        "success_audio": "✅ Мусиқани топиб юбордим!\n\n🎧 @TinglaMediaBotдан фойдаланганингиз учун раҳмат!",
        "error": "❌ Хатолик юз берди ёки мусиқани топиб бўлмади.",
        "send_fail": "❌ Файлни юборишда хатолик юз берди.",
        "change_lang": "Тилни танланг:",
        "choose_track": "Қуйидаги натижалардан мусиқани танланг:\n\n",
        "invalid_choice": "❌ Нотўғри танлов, илтимос рақамни тўғри танланг.",
    },
    "ru": {
        "welcome": (
            "👋 *Привет, я TinglaMediaBot!* ✅\n\n"
            "📌 *Что я умею:*\n"
            "• Нахожу музыку по названию или тексту\n"
            "• Скачиваю видео и музыку с Instagram и YouTube\n"
            "⬇️ Отправьте ссылку или название песни."
        ),
        "send_link": "❗ Пожалуйста, отправьте ссылку или название песни.",
        "unsupported": "❌ Эта платформа пока не поддерживается.",
        "downloading": "⏳ Идёт загрузка, подождите...",
        "success_video": "✅ Видео успешно загружено!\n\n🎧 Спасибо, что используете @TinglaMediaBot!",
        "success_audio": "✅ Музыка найдена и отправлена!\n\n🎧 Спасибо, что используете @TinglaMediaBot!",
        "error": "❌ Произошла ошибка или музыка не найдена.",
        "send_fail": "❌ Ошибка при отправке файла.",
        "change_lang": "Пожалуйста, выберите язык:",
        "choose_track": "Выберите трек из списка:\n\n",
        "invalid_choice": "❌ Неверный выбор, пожалуйста, выберите правильный номер.",
    },
    "en": {
        "welcome": (
            "👋 *Hello, I'm TinglaMediaBot!* ✅\n\n"
            "📌 *What I can do:*\n"
            "• Find music by title or lyrics\n"
            "• Download videos/music from Instagram and YouTube\n"
            "⬇️ Send a link or song title."
        ),
        "send_link": "❗ Please send a link or song title.",
        "unsupported": "❌ This platform is not supported yet.",
        "downloading": "⏳ Downloading, please wait...",
        "success_video": "✅ Video downloaded successfully!\n\n🎧 Thanks for using @TinglaMediaBot!",
        "success_audio": "✅ Music found and sent!\n\n🎧 Thanks for using @TinglaMediaBot!",
        "error": "❌ An error occurred or music was not found.",
        "send_fail": "❌ Failed to send the file.",
        "change_lang": "Please select a language:",
        "choose_track": "Please choose a track from the list:\n\n",
        "invalid_choice": "❌ Invalid choice, please select a valid number.",
    }
}

def get_lang(user_id):
    return user_langs.get(user_id, "uz_latn")

def is_supported_url(url):
    return "youtube.com" in url or "youtu.be" in url or "instagram.com" in url

def download_video(url):
    video_id = str(uuid.uuid4())[:8]
    ydl_opts = {
        'format': 'mp4',
        'outtmpl': f'{video_id}.%(ext)s',
        'quiet': True,
        'user_agent': 'Mozilla/5.0'
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if filename.endswith(".webm") or filename.endswith(".mkv"):
                filename = filename.rsplit(".", 1)[0] + ".mp4"
            return filename
    except Exception:
        return None

def search_tracks(query, max_results=10):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'skip_download': True,
        'default_search': 'ytsearch',
        'extract_flat': True,  # Чтобы получить список без скачивания
        'forceurl': True,
        'forcejson': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_result = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
            entries = search_result.get('entries', [])
            # Собираем нужные данные для вывода и скачивания
            tracks = []
            for e in entries:
                tracks.append({
                    'id': e['id'],
                    'title': e['title'],
                    'duration': e.get('duration', 0),  # в секундах
                    'webpage_url': e.get('url') or e.get('webpage_url'),
                })
            return tracks
    except Exception as e:
        print(f"Ошибка поиска: {e}")
        return []

def download_audio_by_id(video_id):
    filename = f"{video_id}.mp3"
    if os.path.exists(filename):
        return filename
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'outtmpl': f'{video_id}.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
        return filename if os.path.exists(filename) else None
    except Exception as e:
        print(f"Ошибка скачивания: {e}")
        return None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_langs[message.from_user.id] = "uz_latn"
    lang = get_lang(message.from_user.id)
    inline = InlineKeyboardMarkup()
    inline.add(InlineKeyboardButton("➕ Guruhga qo‘shish", url="https://t.me/TinglaMediaBot?startgroup=true"))
    bot.send_message(message.chat.id, texts[lang]["welcome"], parse_mode="Markdown", reply_markup=inline)

@bot.message_handler(commands=['lang'])
def ask_language(message):
    lang = get_lang(message.from_user.id)
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("🇺🇿 O‘zbek (Lotin)", callback_data="lang_uz_latn"),
        InlineKeyboardButton("🇺🇿 Ўзбекча (Кирилл)", callback_data="lang_uz_cyrl")
    )
    markup.add(
        InlineKeyboardButton("🇷🇺 Русский", callback_data="lang_ru"),
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")
    )
    bot.send_message(message.chat.id, texts[lang]["change_lang"], reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("lang_"))
def set_language(call):
    lang_code = call.data.split("_", 1)[1]
    user_langs[call.from_user.id] = lang_code
    bot.answer_callback_query(call.id, text="✅ Til o‘zgartirildi.")
    bot.send_message(call.message.chat.id, texts[lang_code]["welcome"], parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    lang = get_lang(message.from_user.id)
    text = message.text.strip()

    if text.startswith("http") and is_supported_url(text):
        loading_msg = bot.send_message(message.chat.id, texts[lang]["downloading"])
        filename = download_video(text)

        if filename:
            try:
                with open(filename, 'rb') as video:
                    bot.send_video(
                        chat_id=message.chat.id,
                        video=video,
                        caption=texts[lang]["success_video"],
                        parse_mode="Markdown"
                    )
            except Exception:
                bot.send_message(message.chat.id, texts[lang]["send_fail"])
            finally:
                if os.path.exists(filename):
                    os.remove(filename)
        else:
            bot.send_message(message.chat.id, texts[lang]["error"])

        bot.delete_message(message.chat.id, loading_msg.message_id)
        return

    loading_msg = bot.send_message(message.chat.id, texts[lang]["downloading"])
    tracks = search_tracks(text, max_results=10)
    bot.delete_message(message.chat.id, loading_msg.message_id)

    if not tracks:
        bot.send_message(message.chat.id, texts[lang]["error"])
        return

    user_search_results[message.from_user.id] = tracks

    msg_text = texts[lang]["choose_track"]
    for i, track in enumerate(tracks, start=1):
        if track.get('duration'):
            duration_min = int(track['duration'] // 60)
            duration_sec = int(track['duration'] % 60)
            duration_str = f"{duration_min}:{duration_sec:02d}"
        else:
            duration_str = "—"
        msg_text += f"{i}. {track['title']} ({duration_str})\n"

    markup = InlineKeyboardMarkup(row_width=5)
    buttons = [InlineKeyboardButton(str(i), callback_data=f"track_{i}") for i in range(1, len(tracks)+1)]
    markup.add(*buttons)

    bot.send_message(message.chat.id, msg_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("track_"))
def send_selected_track(call: CallbackQuery):
    lang = get_lang(call.from_user.id)
    choice_str = call.data.split("_")[1]
    if not choice_str.isdigit():
        bot.answer_callback_query(call.id, texts[lang]["invalid_choice"], show_alert=True)
        return

    choice = int(choice_str) - 1
    tracks = user_search_results.get(call.from_user.id)
    if not tracks or choice < 0 or choice >= len(tracks):
        bot.answer_callback_query(call.id, texts[lang]["invalid_choice"], show_alert=True)
        return

    track = tracks[choice]
    bot.answer_callback_query(call.id, f"🎵 {track['title']} yuklanmoqda...")

    loading_msg = bot.send_message(call.message.chat.id, texts[lang]["downloading"])

    filename = download_audio_by_id(track['id'])

    bot.delete_message(call.message.chat.id, loading_msg.message_id)

    if filename:
        try:
            with open(filename, 'rb') as audio:
                bot.send_audio(
                    call.message.chat.id,
                    audio=audio,
                    caption=texts[lang]['success_audio'],
                    parse_mode="Markdown",
                    title=track['title']
                )
        except Exception:
            bot.send_message(call.message.chat.id, texts[lang]["send_fail"])
        finally:
            if os.path.exists(filename):
                os.remove(filename)
    else:
        bot.send_message(call.message.chat.id, texts[lang]["error"])


@bot.message_handler(commands=['setcommands'])
def set_bot_commands(message):
    commands = [
        BotCommand("start", "♻️ Start the bot"),
        BotCommand("lang", "🌐 Change language"),
        # Можешь добавить другие команды, если будут
        # BotCommand("help", "ℹ️ Yordam"),
    ]
    bot.set_my_commands(commands)
    bot.reply_to(message, "✅ Buyruqlar ro'yxati o‘rnatildi.")


if __name__ == '__main__':
    print("Bot is running...")
    bot.infinity_polling()