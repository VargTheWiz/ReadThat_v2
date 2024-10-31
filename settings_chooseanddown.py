from urllib.request import urlopen

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QLabel, QPushButton, QDialog, QComboBox, QGroupBox, QVBoxLayout, QDialogButtonBox
from PyQt6.QtWidgets import QProgressBar
import zipfile
import os


class Downloader(QThread):

    # Signal for the window to establish the maximum value
    # of the progress bar.
    setTotalProgress = pyqtSignal(int)
    # Signal to increase the progress.
    setCurrentProgress = pyqtSignal(int)
    # Signal to be emitted when the file has been downloaded successfully.
    succeeded = pyqtSignal()

    def __init__(self, url, filename):
        super().__init__()
        self._url = url
        self._filename = filename

    def run(self):
        # url = "https://www.python.org/ftp/python/3.7.2/python-3.7.2.exe"
        # filename = "python-3.7.2.exe"
        url = self._url
        filename = 'models/'+self._filename
        readBytes = 0
        chunkSize = 1024
        # Open the URL address.
        with urlopen(url) as r:
            # Tell the window the amount of bytes to be downloaded.
            self.setTotalProgress.emit(int(r.info()["Content-Length"]))
            with open(filename, "ab") as f:
                while True:
                    # Read a piece of the file we are downloading.
                    chunk = r.read(chunkSize)
                    # If the result is `None`, that means data is not
                    # downloaded yet. Just keep waiting.
                    if chunk is None:
                        continue
                    # If the result is an empty `bytes` instance, then
                    # the file is complete.
                    elif chunk == b"":
                        break
                    # Write into the local file the downloaded chunk.
                    f.write(chunk)
                    readBytes += chunkSize
                    # Tell the window how many bytes we have received.
                    self.setCurrentProgress.emit(readBytes)
        # If this line is reached then no exception has ocurred in
        # the previous lines.

        # тут код распаковки архива в папку
        with zipfile.ZipFile(filename, "r") as zip_ref:
            zip_ref.extractall("models/")

        # удалим зип после распаковки
        if os.path.isfile(filename):
            os.remove(filename)

        self.succeeded.emit()


class ChAndDo(QDialog):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Read That - Download Model")
        # self.resize(400, 300)

        QBtn = QDialogButtonBox.StandardButton.Close

        group_box_main = QGroupBox("Выбор и загрузка модели")

        # Выбор модели
        self.combobox = QComboBox()
        self.combobox.addItems(["Russian | vosk-model-small-ru-0.22 | 45Mb",
                                "English | vosk-model-small-en-us-0.15 | 40Mb",
                                "Chinese | vosk-model-small-cn-0.22 | 42Mb"])
        # Russian | vosk-model-small-ru-0.22 | 45Mb https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip
        # English | vosk-model-small-en-us-0.15 | 40Mb https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
        # Indian English | vosk-model-small-en-in-0.4 | 36Mb
        # Chinese | vosk-model-small-cn-0.22 | 42Mb https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip
        # self.combobox.currentIndexChanged.connect(self.index_changed)

        self.label1 = QLabel("Выберете модель и начните загрузку.", self)
        self.label2 = QLabel("Пожалуйста, обратите внимание на размер:", self)
        self.label3 = QLabel("Большие модели будут не только долго скачиваться,", self)
        self.label4 = QLabel("но и очень долго загружаться в память", self)
        # self.label.setGeometry(20, 20, 200, 25)

        # Кнопка загрузки
        self.downloadbutton = QPushButton("Начать загрузку", self)
        # self.button.move(20, 60)
        self.downloadbutton.pressed.connect(self.initDownload)

        # Прогресс-бар загрузки
        self.progressBar = QProgressBar(self)
        # self.progressBar.setGeometry(20, 115, 300, 25)
        self.progressBar.setVisible(False)

        chanddo_layout = QVBoxLayout()
        chanddo_layout.addWidget(self.combobox)
        chanddo_layout.addWidget(self.label1)
        chanddo_layout.addWidget(self.label2)
        chanddo_layout.addWidget(self.label3)
        chanddo_layout.addWidget(self.label4)
        chanddo_layout.addWidget(self.downloadbutton)
        chanddo_layout.addWidget(self.progressBar)

        group_box_main.setLayout(chanddo_layout)

        buttonBox = QDialogButtonBox(QBtn)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(group_box_main)
        layout.addWidget(buttonBox)
        self.setLayout(layout)

    def index_changed(self, i):  # i — это int
        print(i)

    def initDownload(self):
        theurl = "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip "
        thefilename = "vosk-model-small-ru-0.22.zip "
        self.indexmodeltodown = self.combobox.currentIndex()
        if self.indexmodeltodown == 0:
            theurl = "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip "
            thefilename = "vosk-model-small-ru-0.22.zip "
        elif self.indexmodeltodown == 1:
            theurl = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip "
            thefilename = "vosk-model-small-en-us-0.15.zip "
        elif self.indexmodeltodown == 2:
            theurl = "https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip "
            thefilename = "vosk-model-small-cn-0.22.zip "
        self.label1.setText("Скачиваем файл модели...")
        # Disable the button while the file is downloading.
        self.downloadbutton.setEnabled(False)
        self.progressBar.setVisible(True)
        # Run the download in a new thread.
        self.downloader = Downloader(theurl, thefilename)
        #    "https://www.python.org/ftp/python/3.7.2/python-3.7.2-webinstall.exe ",
        #    "python-3.7.2-webinstall.exe "
        # )
        # Connect the signals which send information about the download
        # progress with the proper methods of the progress bar.
        self.downloader.setTotalProgress.connect(self.progressBar.setMaximum)
        self.downloader.setCurrentProgress.connect(self.progressBar.setValue)
        # Qt will invoke the `succeeded()` method when the file has been
        # downloaded successfully and `downloadFinished()` when the
        # child thread finishes.
        self.downloader.succeeded.connect(self.downloadSucceeded)
        self.downloader.finished.connect(self.downloadFinished)
        self.downloader.start()

    def downloadSucceeded(self):
        # Set the progress at 100%.
        self.progressBar.setValue(self.progressBar.maximum())
        self.label1.setText("Модель распознавания успешно загружена!")
        self.label2.setText("")
        self.label3.setText("")
        self.label4.setText("")

    def downloadFinished(self):
        # Restore the button.
        self.downloadbutton.setEnabled(True)
        # Delete the thread when no longer needed.
        del self.downloader
