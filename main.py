import sys


from PyQt6.QtWidgets import (
    QApplication, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QComboBox, QMessageBox, QProgressBar, QCheckBox, QWidget
)
from PyQt6.QtGui import QIcon


import YoutubeDownloader, Downloader, StemSplitter


class MainGUI(QWidget):  

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
        self.save_label = QLabel("Save Location: None")
        layout.addWidget(self.save_label)

        self.split_stems_checkbox = QCheckBox("Split Stems?", self)
        self.split_stems_checkbox.stateChanged.connect(self.toggle_stem_options)
        layout.addWidget(self.split_stems_checkbox)

        self.stem_options_dropdown = QComboBox(self)
        self.stem_options_dropdown.addItems(["Vocals Only", "4 Stem Split (Fast but lower quality)", "4 Stem Split (Higher Quality But Slower)", "4 Stem Split (MDX)", "6 Stem Split (Guitar + Piano)"])
        self.stem_options_dropdown.setEnabled(False)
        layout.addWidget(self.stem_options_dropdown)
        
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0,0)
        self.progress_bar.hide()
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
        if ".com" in self.url_input.text():
            self.ytd = YoutubeDownloader.YoutubeDownloader(f"https://soundcloud.com?q={self.url_input.text().replace(' ', '+')}")
        else:
            self.ytd = YoutubeDownloader.YoutubeDownloader("https://soundcloud.com")
        self.ytd.finished.connect(self.set_url)
        self.ytd.start()       
        

    def set_url(self, url):
        self.url_input.setText(url)
        self.ytd.quit()

    def open_youtube(self):
        if ".com" in self.url_input.text():
            self.ytd = YoutubeDownloader.YoutubeDownloader(f"https://youtube.com?q={self.url_input.text().replace(' ', '+')}")
        else:
            self.ytd = YoutubeDownloader.YoutubeDownloader("https://youtube.com")        
        self.ytd.finished.connect(self.set_url)
        self.ytd.start()
        
    def toggle_loading(self):
        if self.progress_bar.isVisible():
            self.progress_bar.hide()
        else:
            self.progress_bar.show()
            
    
    def select_save_location(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Download Folder")
        if folder:
            self.save_path = folder
            self.save_label.setText(f"Save Location: {folder}")

    # Callback function for download button.
    def download_video(self):
        self.progress_bar.show()
        url = self.url_input.text()
        format_selected = self.format_dropdown.currentText().split(" - ")[1].lower()
        self.format = format_selected
        quality_selected = self.quality_dropdown.currentText()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a valid URL.")
            return
        
              
        self.download_thread = Downloader.DownloadThread(url, format_selected, quality_selected, self.save_path.replace("/", "\\"))
        self.download_thread.finished_signal.connect(self.download_complete)        
        self.download_thread.start()

    

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

    def split_complete(self, message):
        print(message)
        self.splitter.quit()
        self.progress_bar.hide()

    # Called when the download thread finishes
    def download_complete(self, success, message, file_path):
        if success:
            if self.split_stems_checkbox.isChecked():
                self.splitter = StemSplitter.StemSplitter(self.convert_stems(), file_path)
                self.splitter.finished.connect(self.split_complete)
                self.splitter.start()
                self.filepath = file_path
                print(self.filepath)
                
        else:
            self.progress_bar.hide()
        print(message)

        


    
# https://www.youtube.com/watch?v=1VQ_3sBZEm0
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('icon.ico'))
    window = MainGUI()
    window.show()
    sys.exit(app.exec())



