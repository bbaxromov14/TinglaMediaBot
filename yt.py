import yt_dlp

def download_youtube(url):
    ydl_opts = {
        'format': 'mp4',
        'outtmpl': 'yt_video.mp4',
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return 'yt_video.mp4'