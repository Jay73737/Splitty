import ffmpeg
import demucs.separate
import demucs.api
import traceback
from PyQt6.QtCore import QThread, pyqtSignal


class StemSplitter(QThread):
    finished = pyqtSignal(str)

    def __init__(self, model, file_path):
        super().__init__()
        self.stem = None
        self.model = model
        self.file_path = file_path


    def run(self):
        
        self.split_stems()

    
    

    def split_stems(self):
        
        file_name = self.file_path.split('\\')[-1].split('.')[0]
        dir = self.file_path.replace(file_name.split('\\')[-1], '')
        if self.model[1]:
            demucs.separate.main(["--two-stems", "vocals", "-n", self.model[0], "-o", dir, self.file_path])
        else:
            demucs.separate.main(["-n",self.model[0], "-o", dir, self.file_path])