import demucs.separate
import demucs.api
import ffmpeg
import io
import sys
import os
import sys
import yt_dlp
from enum import Enum
import subprocess

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QComboBox, QMessageBox, QProgressBar, QCheckBox
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QThread, pyqtSignal
from selenium import webdriver

from selenium.webdriver.chrome.options import Options
import time


class ThreadStdout(io.StringIO):
    """ Custom stdout class for capturing and reading output. """
    def __init__(self, signal):
        super().__init__()
        self.signal = signal
        self.buffer = io.StringIO()  # Internal buffer to store printed text

    def write(self, text):
        super().write(text)
        self.buffer.write(self.buffer.getvalue() +'\n'+ text)  # Store text in buffer
        self.signal.emit(text)  # Emit signal for UI updates

    def read_output(self):
        return self.buffer.getvalue()  # Retrieve stored output



class DownloadThread(QThread):
    progress_signal = pyqtSignal(int) 
    finished_signal = pyqtSignal(bool, str, str) 
    output_signal = pyqtSignal(str)

    def __init__(self, url, format_selected, quality_selected, save_path):
        super().__init__()
        self.quality_selected = quality_selected
        self.format_selected = format_selected
        self.url = url
        self.save_path = save_path
        self.service = None
        self.stdout = ThreadStdout(self.output_signal)
        
   


    def ensure_scdl_installed(self):
        try:
            # Check if scdl is installed
            subprocess.run(["scdl", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("scdl is already installed.")
        except subprocess.CalledProcessError:
            print("scdl is not installed. Installing now...")
            subprocess.run([sys.executable, "-m", "pip", "install", "scdl"], check=True)
            print("scdl installed successfully.")
        except FileNotFoundError:
            print("scdl is not installed. Installing now...")
            subprocess.run([sys.executable, "-m", "pip", "install", "scdl"], check=True)
            print("scdl installed successfully.")

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
        if "youtube.com" in self.url:

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

                self.finished_signal.emit(True, "Download completed! Do you want to stem split this track?", ydl.prepare_filename(ydl.extract_info(self.url, download=False)))
            except Exception as e:
                self.finished_signal.emit(False, f"Download failed: {str(e)}", "")
        elif "soundcloud.com" in self.url:
            self.ensure_scdl_installed()
            try:
                
                output = subprocess.run(["scdl", "-l", self.url, "--path", self.save_path,  "-c", "--addtofile"],stdout=self.stdout, text=True)
                output_text = self.stdout.read_output()

                self.finished_signal.emit(True, "Download completed! Do you want to stem split this track?", output_text)
            except Exception as e:
                self.finished_signal.emit(False, f"Download failed: {str(e)}", "")
            


class YouTubeDownloader(QWidget):  

    def __init__(self):
        super().__init__()

        self.setWindowTitle("YouTube Downloader")
        self.setGeometry(200, 200, 400, 350)
        layout = QVBoxLayout()
        
        self.search_button = QPushButton("Search on YouTube")
        self.search_button.clicked.connect(self.open_youtube)
        layout.addWidget(self.search_button)

        self.search_soundcloud_button = QPushButton("Search on Soundcloud")
        self.search_soundcloud_button.clicked.connect(self.open_soundcloud)
        layout.addWidget(self.search_soundcloud_button)
        
        self.url_label = QLabel("URL/Search:")
        layout.addWidget(self.url_label)

        self.url_input = QLineEdit(self)
        layout.addWidget(self.url_input)
        self.url_input.returnPressed.connect(self.open_youtube)      
        self.format_label = QLabel("Select Format:")
        layout.addWidget(self.format_label)

        self.format_dropdown = QComboBox(self)
        self.format_dropdown.addItems(["Video - mp4", "Audio - mp3", "Audio - wav", "Audio - m4a", "Audio - aac", "Audio - flac", "Audio - opus"])
        layout.addWidget(self.format_dropdown)

        
        self.quality_label = QLabel("Select Audio Quality:")
        layout.addWidget(self.quality_label)

        self.quality_dropdown = QComboBox(self)
        self.quality_dropdown.addItems(["Low (64kbps)", "Medium (128kbps)", "High (192kbps)"])
        layout.addWidget(self.quality_dropdown)

        
        self.save_button = QPushButton("Select Save Location")
        self.save_button.clicked.connect(self.select_save_location)
        layout.addWidget(self.save_button)

        self.save_path = ""

        self.split_stems_checkbox = QCheckBox("Split Stems?", self)
        self.split_stems_checkbox.stateChanged.connect(self.toggle_stem_options)
        layout.addWidget(self.split_stems_checkbox)

        self.stem_options_dropdown = QComboBox(self)
        self.stem_options_dropdown.addItems(["Vocals Only", "4 Stem Split (Fast but lower quality)", "4 Stem Split (Higher Quality But Slower)", "4 Stem Split (MDX)", "6 Stem Split (Guitar + Piano)"])
        self.stem_options_dropdown.setEnabled(False)
        layout.addWidget(self.stem_options_dropdown)
        
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        
        self.download_button = QPushButton("Download")
        self.download_button.clicked.connect(self.download_video)
        layout.addWidget(self.download_button)

        self.terminal_output = QLabel()
        self.terminal_output.setVisible(False)
        layout.addWidget(self.terminal_output)
        self.setLayout(layout)

    def toggle_stem_options(self):
        if self.split_stems_checkbox.isChecked():
            self.stem_options_dropdown.setEnabled(True)
        else:
            self.stem_options_dropdown.setEnabled(False)

    def open_soundcloud(self):
        self.service = "soundcloud"
        query = "https://soundcloud.com/"
        if self.url_input.text() and "https://soundcloud.com" not in self.url_input.text():
            query = f"https://soundcloud.com/search?q={self.url_input.text().replace(' ', '+')}"
               

        chrome_options = Options()
        chrome_options.add_experimental_option("detach", True)
        QMessageBox.information(self, "Soundcloud Search", "Search for a song, then close the browser after loading the page of the correct one.")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(query)
        current_url = driver.current_url
    
        
        while True:
            try:
                time.sleep(.5)
                if current_url != driver.current_url:
                    urls = driver.current_url.split("://")[1].split("/")
                    if len(urls) < 3:
                        continue
                    elif "soundcloud.com" in urls[0] and len(urls) >= 3:
                        if len(urls) == 3:
                            
                            current_url = driver.current_url
                            self.url_input.setText(current_url)
                            break
                        
                current_url = driver.current_url
            except:                
                break

        
        

    # Opens Youtube for finding the correct URL
    def open_youtube(self):
        self.service = "youtube"
        query = "https://www.youtube.com/"
        if self.url_input.text() and "https://www.youtube.com" not in self.url_input.text():
            query = f"https://www.youtube.com/results?search_query={self.url_input.text().replace(' ', '+')}"

        chrome_options = Options()
        chrome_options.add_experimental_option("detach", True)
        QMessageBox.information(self, "YouTube Search", "Search for a video, then close the browser after loading the page of the correct one.")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(query)
        current_url = driver.current_url
  
        
        while True:
            try:
                driver.title  
                time.sleep(.5)             

                if current_url != driver.current_url:
                    current_url = driver.current_url
            except:
                break

        
        last_url = current_url
        if "watch?v=" in last_url:
            self.url_input.setText(last_url)
        else:
            QMessageBox.warning(self, "Error", "No video URL detected. Try again.")

    def select_save_location(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder")
        if folder:
            self.save_path = folder

    # Callback function for download button.
    def download_video(self):
        url = self.url_input.text()
        
        if self.service == "youtube":            
            if "watch?v=" not in url and len(url) > 0:
                self.open_youtube()
        elif self.service == "soundcloud":
            if "soundcloud.com" not in url and len(url) > 0:
                self.open_soundcloud()


        format_selected = self.format_dropdown.currentText().split(" - ")[1].lower()
        self.format = format_selected
        quality_selected = self.quality_dropdown.currentText()

        if not url:
            QMessageBox.warning(self, "Error", "Please enter a valid URL.")
            return
        
        self.progress_bar.setValue(0)        
        self.download_thread = DownloadThread(url, format_selected, quality_selected, self.save_path.replace("/", "\\"))
        self.download_thread.progress_signal.connect(self.update_progress)
        self.download_thread.finished_signal.connect(self.download_complete)
        
        self.download_thread.start()

    # Updates download progress bar
    def update_progress(self, value):
        self.progress_bar.setValue(value)

    # Returns model names from dropdown selection. (model, args)
    def convert_stems(self):
        stem = self.stem_options_dropdown.currentText()
        
        match stem:
            case "Vocals Only":
                return ("htdemucs",("--two-stems","vocals"))
            case "4 Stem Split (Fast but lower quality)":
                return ("htdemucs",None)
            case "4 Stem Split (Higher Quality But Slower)":
                return ("htdemucs_ft",None)
            case "4 Stem Split (MDX)":
                return ("mdx",None)
            case "6 Stem Split (Guitar + Piano)":
                return ("htdemucs_6s",None)

    # Called when the download thread finishes
    def download_complete(self, success, message, file_path):
        if success:
            if self.split_stems_checkbox.isChecked():
                if '/' in file_path:

                    file_path = file_path.replace("/", "\\")
                print(file_path)
                
                if not file_path.endswith(".wav"):
                    format = file_path.split(".")[-1]
                    ffmpeg.input(file_path).output(file_path.replace("."+ format, ".wav")).run()
                    file_path = file_path.replace("."+ format, ".wav")
                st = self.convert_stems()
                print(file_path)
                directory = file_path.split("\\")               
                dir = directory[-1]                
                if st[1]:
                    demucs.separate.main(["--two-stems", "vocals", "-n", st[0], "-o", dir, file_path])
                else:
                    demucs.separate.main(["-n", st[0], "-o", dir, file_path])
        else:
            QMessageBox.critical(self, "Error", message)


    def convert_complete(self, success, message):
        if success:
            QMessageBox.information(self, "Conversion", message)        
        else:
            QMessageBox.critical(self, "Error", message)

    def convert_mp4_to_wav(self, input_file, output_file):
        try:
            ffmpeg.input(input_file).output(output_file).run()
            print(f"Conversion successful: {output_file}")
        except ffmpeg.Error as e:
            print(f"Error occurred: {e.stderr.decode()}")
# https://www.youtube.com/watch?v=1VQ_3sBZEm0
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('icon.ico'))
    window = YouTubeDownloader()
    window.show()
    sys.exit(app.exec())



