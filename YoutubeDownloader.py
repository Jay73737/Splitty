from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

class YoutubeDownloader(QThread):
    finished = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        self.open_youtube()
    # Opens Youtube for finding the correct URL
    def open_youtube(self):
        self.service = "youtube"
        query = "https://www.youtube.com/"
        if self.url and "https://www.youtube.com" not in self.url:
            query = f"https://www.youtube.com/results?search_query={self.url.replace(' ', '+')}"

        chrome_options = Options()
        chrome_options.add_experimental_option("detach", True)
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
            self.finished.emit(last_url)
        else:
            QMessageBox.warning(self, "Error", "No video URL detected. Try again.")
