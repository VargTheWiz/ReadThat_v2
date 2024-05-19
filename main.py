from PyQt6.QtCore import QSize, QObject, pyqtSignal, pyqtSlot, QThread, Qt, QSettings, QCoreApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QMainWindow,
    QHBoxLayout,
    QVBoxLayout,
    QToolButton,
    QSizePolicy,
    QPlainTextEdit,
    QFileDialog, QRadioButton, QGroupBox, QDialogButtonBox, QDialog
)  # QPushButton, QTextEdit,
# from PyQt6.QtGui import QPalette, QColor
from datetime import datetime
from vosk import Model, KaldiRecognizer
import pyaudiowpatch as pyaudio
import json
import queue
import sys
import wave
import os
from settings import CustomDialog, LoadSettingsFromIni, SaveSettingToIni


# Step 1: Create a worker class
class Worker (QObject):
    finished = pyqtSignal()
    rectext = pyqtSignal(str)

    def run(self):
        DURATION = 5.0
        CHUNK_SIZE = 512

        filename = "loopback_record.wav"

        outfileText = "outms4.json"
        results = ""
        textResults = []

        ######
        with pyaudio.PyAudio() as p:
            try:
                # Get default WASAPI info
                wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
            except OSError:
                print("Looks like WASAPI is not available on the system. Exiting...")
                exit()

            default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
            print()

            if not default_speakers["isLoopbackDevice"]:
                for loopback in p.get_loopback_device_info_generator():
                    """
                    Try to find loopback device with same name(and [Loopback suffix]).
                    Unfortunately, this is the most adequate way at the moment.
                    """
                    if default_speakers["name"] in loopback["name"]:
                        default_speakers = loopback
                        break
                else:
                    exit()

            wave_file = wave.open(filename, 'wb')
            wave_file.setnchannels(default_speakers["maxInputChannels"])
            wave_file.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
            wave_file.setframerate(int(default_speakers["defaultSampleRate"]))

            # setup queue and callback function
            q = queue.Queue()

            def callback(in_data, frame_count, time_info, status):
                """Write frames and return PA flag"""
                wave_file.writeframes(in_data)
                #
                if status:
                    print(status, file=sys.stderr)
                q.put(bytes(in_data))
                return in_data, pyaudio.paContinue

            # build the model and recognizer objects.
            self.rectext.emit("code1234")
            self.rectext.emit("Пожалуйста, подождите, модель загружается")
            print("===> Build the model and recognizer objects.  This will take a few minutes.")
            # model = Model(r"D:/Programmeas/makesubtitles/vosk-model-ru-0.42")
            model = Model(r"D:/Programmeas/makesubtitles/vosk-model-small-ru-0.22")
            if LoadSettingsFromIni('model'):
                print(LoadSettingsFromIni('model'))
                model = Model(LoadSettingsFromIni('model'))
            recognizer = KaldiRecognizer(model, int(default_speakers["defaultSampleRate"]))
            recognizer.SetWords(False)

            print("===> Begin recording. Press Ctrl+C to stop the recording ")
            self.rectext.emit("code1234")
            print(default_speakers)

            try:
                with p.open(format=pyaudio.paInt16,
                            channels=1,  # default_speakers["maxInputChannels"],
                            rate=int(default_speakers["defaultSampleRate"]),
                            frames_per_buffer=CHUNK_SIZE,
                            input=True,
                            input_device_index=default_speakers["index"],
                            stream_callback=callback
                            ) as stream:
                    """
                    Opena PA stream via context manager.
                    After leaving the context, everything will
                    be correctly closed(Stream, PyAudio manager)            
                    """
                    while True:
                        data = q.get()
                        if recognizer.AcceptWaveform(data):
                            recognizerResult = recognizer.Result()
                            results = results + recognizerResult
                            # convert the recognizerResult string into a dictionary
                            resultDict = json.loads(recognizerResult)
                            if not resultDict.get("text", "") == "":
                                # print(recognizerResult)
                                textResults.append(resultDict.get("text", ""))
                                print(resultDict.get("text", ""))
                                self.rectext.emit(resultDict.get("text", ""))
                            else:
                                print("no input sound")
            except KeyboardInterrupt:
                # write text portion of results to a file
                with open(outfileText, 'w') as output:
                    print(json.dumps(textResults, indent=4, ensure_ascii=False), file=output)
                print('===> Finished Recording')
            except Exception as e:
                # write text portion of results to a file
                with open(outfileText, 'w') as output:
                    print(json.dumps(textResults, indent=4, ensure_ascii=False), file=output)
                print(str(e))

            wave_file.close()


# Подкласс QMainWindow для настройки главного окна приложения
class MainWindow(QMainWindow):

    def __init__(self):
        self.settings = QSettings("config.ini", QSettings.Format.IniFormat)
        super(MainWindow, self).__init__()

        self.worker = None
        self.thread = None

        self.defaultWindowFlags = self.windowFlags()

        self.setWindowTitle("ReadThat")
        self.setMinimumSize(QSize(400, 150))
        # self.setWindowFlag(Qt.WindowType.FramelessWindowHint)

        # раскладка форм в приложении
        layout = QHBoxLayout()  # горизонтальная: вывод + все л2 + скрытие
        layout2 = QVBoxLayout()  # вертикальная: опции + старт + сейв и все что в л3
        layout3 = QVBoxLayout()  # горизонтальная: размер поля + выход | скрытие + выход
        # итого надо скрыть: (размер поля + выход) опции + старт + сейв
        # виджет вывода текста
        self.TheTextField = QPlainTextEdit()
        self.TheTextField.setReadOnly(1)
        self.TheTextField.setPlainText("Привет! Тут будет показываться распознанный текст из воспроизведенного в "
                                       "системе звука после того как ты нажмешь на кнопку старта!")
        layout.addWidget(self.TheTextField)

        # раскладка форм в приложении
        layout.addLayout(layout2)

        # виджет-кнопка раскрытия окна вывода текста (сомнительно, пропускаем пока что)
        # self.TextFieldSizeBtn = QToolButton()
        # self. TextFieldSizeBtn.setMinimumWidth(20)
        # self.TextFieldSizeBtn.setMinimumHeight(20)
        # self. TextFieldSizeBtn.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)
        # layout3.addWidget(self.TextFieldSizeBtn)

        # кнопка открытия окна настроек
        self.OptionsBtn = QToolButton()
        self.OptionsBtn.setMaximumWidth(50)
        # self.HideBtn.setMinimumHeight(200)
        self.OptionsBtn.setIcon(QIcon("src/TheSettingsButton.png"))
        self.OptionsBtn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.OptionsBtn.clicked.connect(self.TheOptions)
        layout2.addWidget(self.OptionsBtn)

        # кнопка старта/паузы
        self.StaPauBtn = QToolButton()
        self.StaPauBtn.setIcon(QIcon("src/TheStartButton.png"))
        self.StaPauBtn.setCheckable(True)
        self.stapau_button_is_checked = 0
        self.StaPauBtn.clicked.connect(self.runLongTask)
        self.StaPauBtn.setMaximumWidth(50)
        # self.HideBtn.setMinimum Height(200)
        self.StaPauBtn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout2.addWidget(self.StaPauBtn)

        # кнопка сохранения текста
        self.SaveTxtBtn = QToolButton()
        self.SaveTxtBtn.setIcon(QIcon("src/TheSaveButton.png"))
        self.SaveTxtBtn.setMaximumWidth(50)
        # self.HideBtn.setMinimum Height (200)
        self.SaveTxtBtn.clicked.connect(self.saveAs)
        self.SaveTxtBtn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout2.addWidget(self.SaveTxtBtn)

        layout.addLayout(layout3)

        # виджет-тулкнопка закрытия
        self.ExitBtn = QToolButton()
        self.ExitBtn.clicked.connect(self.TheExitButton)
        self.ExitBtn.setIcon(QIcon("src/TheCloseButton.png"))
        self.ExitBtn.setMaximumWidth(30)
        # self.ExitBtn.setMinimumWidth(5)
        # #self.ExitBtn.setMinimumHeight(5)
        # layout3.addWidget(self.ExitBtn)
        layout3.addWidget(self.ExitBtn)

        # кнопка скрытия лишних кнопочек (layout3)
        self.HideBtn = QToolButton()
        self.HideBtn.setCheckable(True)
        self.hide_button_is_checked = 0
        self.HideBtn.setIcon(QIcon("src/TheHideButton.png"))
        self.HideBtn.setMaximumWidth(30)
        # self.HideBtn.setMinimumHeight(200)
        self.HideBtn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.HideBtn.clicked.connect(self.TheHideButton)
        layout3.addWidget(self.HideBtn)

        # главный виджет со всем внутри
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # self.button = QPushButton("Press Me!")

        self.defaultWindowFlags = self.windowFlags()

    # функция запуска распознавания
    def runLongTask(self, checked):
        self.stapau_button_is_checked = checked
        if self.stapau_button_is_checked:
            self.TheTextField.setPlainText("")  # затрем поле вывода
            self.StaPauBtn.setIcon(QIcon("src/TheStopButton.png"))  # 2 - иконка стоп

            # Step 2: Create a QThread object
            self.thread = QThread()
            # Step 3: Create a worker object
            self.worker = Worker()
            # Step 4: Move worker to the thread
            self.worker.moveToThread(self.thread)
            # Step 5: Connect signals and slots
            self.worker.rectext.connect(self.AcceptRecText)
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)
            # Step 6: Start the thread
            self.thread.start()
            # Final resets
            self.thread.finished.connect(
                lambda: self.StaPauBtn.setEnabled(True)
            )
            # self.thread.finished.connect(print('finishedasd'))
        else:
            print("wtf")
            self.thread.requestInterruption()
            self.thread.quit()
            self.StaPauBtn.setIcon(QIcon("src/TheStartButton.png"))  # 2 - иконка старт

    # Функция кнопки
    # def TheStaPauBtn(self):
    # self.StaPauBtn.setEnabled(False)
    # ой я вспомнил это лишнее мы сразу запускаем процесс длинной задачи

    def TheExitButton(self):
        # добавить интеррапт и нормальное закрытие треда
        self.close()

    def TheOptions(self):
        print("setti")
        dlg = CustomDialog()
        dlg.exec()
        # открывает окно настроек

    def saveAs(self):
        now = datetime.now()
        fileName, _ = QFileDialog.getSaveFileName(self, "Save File", now.strftime("%Y-%d-%m--%H-%M-%S"), "All Files(*);;Text Files(*.txt)")
        if fileName:
            with open(fileName, 'w') as f:
                f.write(self.TheTextField.toPlainText())
            # self.fileName = fileName

    def TheHideButton(self, checked):
        if checked:
            self.HideBtn.setIcon(QIcon("src/TheUnhideButton.png"))
            self.setWindowFlag(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
            # self.TextFieldSizeBtn.setVisible(False)
            # self.ExitBtn.setVisible(False)
            self.OptionsBtn.setVisible(False)
            self.StaPauBtn.setVisible(False)
            self.SaveTxtBtn.setVisible(False)
            window.show()
        else:
            self.HideBtn.setIcon(QIcon("src/TheHideButton.png"))
            self.setWindowFlags(self.defaultWindowFlags)
            # self.TextFieldSizeBtn.setVisible(True)
            # self.ExitBtn.setVisible(True)
            self.OptionsBtn.setVisible(True)
            self.StaPauBtn.setVisible(True)
            self.SaveTxtBtn.setVisible(True)
            window.show()
    # тут большое условие, меняет картинку, скрывает виджеты, показывает картинку

    @pyqtSlot(str)
    def AcceptRecText(self, string):
        self.TheTextField.appendPlainText(string)
        if string == "code1234":
            self.TheTextField.setPlainText("")  # очищает поле текста


app = QApplication([])

window = MainWindow()
window.show()

app.exec()
