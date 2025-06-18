requirements = [
    "pyTelegramBotAPI",
    "yt-dlp",
    "requests",
    "pyacoustid"
]

with open("requirements.txt", "w") as f:
    f.write("\n".join(requirements))

print("✅ requirements.txt успешно создан.")
