from PyQt6.QtCore import QThread, pyqtSignal
import yt_dlp

class DownloadThread(QThread):
    progress_signal = pyqtSignal(int) 
    finished_signal = pyqtSignal(bool, str, str) 


    def __init__(self, url, format_selected, quality_selected, save_path):
        super().__init__()
        self.quality_selected = quality_selected
        self.format_selected = format_selected
        self.url = url
        self.save_path = save_path
        self.service = None  


    def run(self):
        
        def progress_hook(d):
            if d['status'] == 'downloading':
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes', 1) or d.get('total_bytes_estimate', 1)
                progress_percent = int((downloaded / total) * 100)
                self.progress_signal.emit(progress_percent)

            elif d['status'] == 'finished':
                self.progress_signal.emit(100)
        

        quality_map = {"Low (64kbps)": "64", "Medium (128kbps)": "128", "High (192kbps)": "192"}
        bitrate = quality_map.get(self.quality_selected, "192")        

        ydl_opts = {
            
            'format': 'bestaudio/best' if self.format_selected in ["mp3", "wav", "m4a", "aac", "flac", "opus"]
                    else f'bestvideo[ext={self.format_selected}]+bestaudio/best[ext={self.format_selected}]',
            'outtmpl': f"{self.save_path}/%(title)s.%(ext)s",
            'progress_hooks': [progress_hook],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': self.format_selected,
                'preferredquality': bitrate,
            }] if self.format_selected in ["mp3", "wav", "m4a", "aac", "flac", "opus"] else []
        }
    
    
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([self.url])

            self.finished_signal.emit(True, "Download completed!", ydl.prepare_filename(ydl.extract_info(self.url, download=False)).split('.')[0] + f".{self.format_selected}")
        except Exception as e:
            self.finished_signal.emit(False, f"Download failed: {str(e)}", "")