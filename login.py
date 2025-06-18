import asyncio
from telethon import TelegramClient

api_id = 22314602
api_hash = '5d51eac2c282975874dce68b56652097'

client = TelegramClient('story_session', api_id, api_hash)

async def manual_login():
    await client.connect()
    if not await client.is_user_authorized():
        phone = input("📱 Telegram telefon raqamingizni kiriting (masalan: +99890...): ")
        await client.send_code_request(phone)
        code = input("📩 SMS bilan kelgan kodni kiriting: ")
        await client.sign_in(phone, code)
    print("✅ Tizimga kirdingiz.")
    await client.disconnect()

asyncio.run(manual_login())
