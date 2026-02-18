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
        
        Note: TikTok requires authentication cookies. Set TIKTOK_COOKIES_FILE environment
        variable to a Netscape-format cookie file path for TikTok downloads.
        """
        file_id = str(uuid.uuid4())
        output_path = os.path.join(self.download_dir, f"{file_id}.%(ext)s")
        
        ydl_opts = {
            'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
            'outtmpl': output_path,
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_warnings': True,
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
            'referer': 'https://www.tiktok.com/',
        }
        
        # Add cookie file if configured for TikTok
        cookie_file = os.getenv('TIKTOK_COOKIES_FILE')
        if cookie_file and 'tiktok' in url.lower():
            ydl_opts['cookiefile'] = cookie_file

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                final_path = ydl.prepare_filename(info)
                # Ensure the extension in the final path matches what was downloaded
                return final_path
        except Exception as e:
            print(f"[VideoDownloader] ERROR downloading {url}: {str(e)}")
            return None

base_video_downloader = VideoDownloader()
