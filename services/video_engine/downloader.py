import yt_dlp
import os
import uuid
from typing import Optional

class VideoDownloader:
    def __init__(self, download_dir: str = "temp/downloads"):
        self.download_dir = download_dir
        os.makedirs(self.download_dir, exist_ok=True)

    async def download_video(self, url: str) -> Optional[str]:
        """
        Downloads a video from a URL and returns the local file path.
        """
        from api.config import settings
        file_id = str(uuid.uuid4())
        output_path = os.path.join(self.download_dir, f"{file_id}.%(ext)s")
        
        ydl_opts = {
            # Resilient format selector: Try preferred quality, then fallback to anything combined
            'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
            'outtmpl': output_path,
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        }
        
        # Determine cookies path
        is_tiktok = 'tiktok' in url.lower()
        is_youtube = 'youtube' in url.lower() or 'youtu.be' in url.lower()
        
        cookie_path = None
        if is_tiktok:
            cookie_path = settings.TIKTOK_COOKIES_PATH or os.getenv('TIKTOK_COOKIES_FILE')
        elif is_youtube:
            cookie_path = settings.YOUTUBE_COOKIES_PATH or os.getenv('YOUTUBE_COOKIES_FILE')

        if cookie_path and os.path.exists(cookie_path):
            ydl_opts['cookiefile'] = cookie_path
        elif cookie_path:
            print(f"[VideoDownloader] WARNING: Cookie file {cookie_path} not found.")

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                final_path = ydl.prepare_filename(info)
                return final_path
        except Exception as e:
            # Absolute last resort for any format error
            print(f"[VideoDownloader] Broad fallback triggered for {url}. Error: {str(e)}")
            ydl_opts.pop('format', None) # Let yt-dlp decide
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    return ydl.prepare_filename(info)
            except Exception as e2:
                print(f"[VideoDownloader] Critical Failure for {url}: {str(e2)}")
                return None

    async def verify_video_asset(self, url: str) -> bool:
        """
        Quickly inspects the URL to ensure it has a valid video stream.
        """
        from api.config import settings
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'simulate': True,
            'skip_download': True,
            # DO NOT specify format here. specifying format leads to "Requested format is not available"
            # on some platforms if the selector is even slightly off.
        }
        
        # Add cookies for validation bypass
        is_tiktok = 'tiktok' in url.lower()
        is_youtube = 'youtube' in url.lower() or 'youtu.be' in url.lower()
        
        cookie_path = None
        if is_tiktok:
            cookie_path = settings.TIKTOK_COOKIES_PATH or os.getenv('TIKTOK_COOKIES_FILE')
        elif is_youtube:
            cookie_path = settings.YOUTUBE_COOKIES_PATH or os.getenv('YOUTUBE_COOKIES_FILE')

        if cookie_path and os.path.exists(cookie_path):
            ydl_opts['cookiefile'] = cookie_path

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                # Check for video stream (vcodec != 'none')
                vcodec = info.get('vcodec') or 'none'
                if vcodec == 'none':
                    print(f"[VideoDownloader] VALIDATION FAILED: {url} is audio-only.")
                    return False
                return True
        except Exception as e:
            print(f"[VideoDownloader] Validation Error for {url}: {e}")
            return False

base_video_downloader = VideoDownloader()
