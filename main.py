# -*- coding: utf-8 -*-
"""
Created on Mon May  4 13:57:03 2026

@author: VargTheWiz
"""

"""
todo
- style into css file
-+ add dark mode for text field
-+ add the old code
- add whisper capability or other rec neuro
- add linux Pulse audio comp?
- add linux interface?
- add sound input choice (micropphone) in settings?
- add timestamps in text?

"""

from PyQt6.QtCore import ( 
    QSize,
    Qt,
    QRect,
    QObject,
    pyqtSignal,
    pyqtSlot,
    QThread,
    QSettings,
)
from PyQt6.QtGui import (
    QIcon, 
    QColor,
)
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QSizeGrip,
    QGraphicsOpacityEffect,
    QPlainTextEdit,
    QTextEdit,
    QSizePolicy,
    QFileDialog,
    QMessageBox,
)


from datetime import datetime

from vosk import Model, KaldiRecognizer

import pyaudiowpatch as pyaudio

import json
import queue
import sys
import wave
import ctypes

from settings import SettingsDialog, LoadSettingsFromIni, SaveSettingToIni

# titlebar code example is from https://www.pythonguis.com/tutorials/custom-title-bar-pyqt6/
# by Leo Well
class CustomTitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.initial_pos = None
        title_bar_layout = QHBoxLayout(self)
        title_bar_layout.setContentsMargins(1, 1, 1, 1)
        title_bar_layout.setSpacing(2)
        self.title = QLabel(f"{self.__class__.__name__}", self)
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet(
            """QLabel {
                    font-size: 10pt;
                    margin-left: 32px;
                    color: white;
                }
            """
            # Here margin-left: 32px; is a count for both 16 px buttons on right
        )

        if title := parent.windowTitle():
            self.title.setText(title)
        title_bar_layout.addWidget(self.title)

        # Min button
        self.min_button = QToolButton(self)
        min_icon = QIcon()
        min_icon.addFile("src/min.svg")
        self.min_button.setIcon(min_icon)
        self.min_button.clicked.connect(self.window().showMinimized)
        
        """
        # Max button
        self.max_button = QToolButton(self)
        max_icon = QIcon()
        max_icon.addFile("testicons/max.svg")
        self.max_button.setIcon(max_icon)
        self.max_button.clicked.connect(self.window().showMaximized)
        """
        
        # Close button
        self.close_button = QToolButton(self)
        close_icon = QIcon()
        close_icon.addFile("src/close.svg")  # Close has only a single state.
        self.close_button.setIcon(close_icon)
        self.close_button.clicked.connect(self.window().close)
        
        """
        # Normal button
        self.normal_button = QToolButton(self)
        normal_icon = QIcon()
        normal_icon.addFile("testicons/normal.svg")
        self.normal_button.setIcon(normal_icon)
        self.normal_button.clicked.connect(self.window().showNormal)
        self.normal_button.setVisible(False)
        """
        
        # Add buttons
        buttons = [
            self.min_button,
            #self.normal_button,
            #self.max_button,
            self.close_button,
        ]
        for button in buttons:
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            button.setFixedSize(QSize(16, 16))
            button.setStyleSheet(
                """QToolButton {
                        border: none;
                        padding: 2px;
                    }
                """
            )
            title_bar_layout.addWidget(button)
            
    # Catching min max window
    """
    def window_state_changed(self, state):
        if state == Qt.WindowState.WindowMaximized:
            self.normal_button.setVisible(True)
            self.max_button.setVisible(False)
        else:
            self.normal_button.setVisible(False)
            self.max_button.setVisible(True)
    """
    
    # Functions for window dragging
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.initial_pos = event.position().toPoint()
        super().mousePressEvent(event)
        event.accept()

    def mouseMoveEvent(self, event):
        if self.initial_pos is not None:
            delta = event.position().toPoint() - self.initial_pos
            self.window().move(
                self.window().x() + delta.x(),
                self.window().y() + delta.y(),
            )
        super().mouseMoveEvent(event)
        event.accept()

    def mouseReleaseEvent(self, event):
        self.initial_pos = None
        super().mouseReleaseEvent(event)
        event.accept()

# resizing is from https://stackoverflow.com/questions/62807295/how-to-resize-a-window-from-the-edges-after-adding-the-property-qtcore-qt-framel 
# code example by musicamante
class SideGrip(QWidget):
    def __init__(self, parent, edge):
        QWidget.__init__(self, parent)
        if edge == Qt.Edge.LeftEdge:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
            self.resizeFunc = self.resizeLeft
        elif edge == Qt.Edge.TopEdge:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
            self.resizeFunc = self.resizeTop
        elif edge == Qt.Edge.RightEdge:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
            self.resizeFunc = self.resizeRight
        else:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
            self.resizeFunc = self.resizeBottom
        self.mousePos = None
        

    def resizeLeft(self, delta):
        window = self.window()
        width = max(window.minimumWidth(), window.width() - delta.x())
        geo = window.geometry()
        geo.setLeft(geo.right() - width)
        window.setGeometry(geo)

    def resizeTop(self, delta):
        window = self.window()
        height = max(window.minimumHeight(), window.height() - delta.y())
        geo = window.geometry()
        geo.setTop(geo.bottom() - height)
        window.setGeometry(geo)

    def resizeRight(self, delta):
        window = self.window()
        width = max(window.minimumWidth(), window.width() + delta.x())
        window.resize(width, window.height())

    def resizeBottom(self, delta):
        window = self.window()
        height = max(window.minimumHeight(), window.height() + delta.y())
        window.resize(window.width(), height)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.mousePos = event.pos()

    def mouseMoveEvent(self, event):
        if self.mousePos is not None:
            delta = event.pos() - self.mousePos
            self.resizeFunc(delta)

    def mouseReleaseEvent(self, event):
        self.mousePos = None


class Worker (QObject):
    finished = pyqtSignal()
    rectext = pyqtSignal(str)

    def run(self):
        # DURATION = 5.0
        CHUNK_SIZE = 512

        def IsIntReq():
            interrupt = QThread.currentThread().isInterruptionRequested()
            if interrupt:
                raise NameError('vasya1998')

        now = datetime.now()
        filename = now.strftime("%Y-%m-%d--%H-%M-%S")+'.wav'  # "loopback_record.wav"

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
                self.rectext.emit("Looks like WASAPI is not available on the system. Exiting...")
                QThread.currentThread().requestInterruption()
                IsIntReq()
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
                    self.rectext.emit("Could not find loopback device with same name(and [Loopback suffix])")
                    QThread.currentThread().requestInterruption()
                    IsIntReq()
                    exit()

            isrecordon = LoadSettingsFromIni('makerecord')
            
            if isrecordon == "True":
                isrecordon = True
            else:
                isrecordon = False
                
            if isrecordon:
                wave_file = wave.open(filename, 'wb')
                wave_file.setnchannels(default_speakers["maxInputChannels"])
                wave_file.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
                wave_file.setframerate(int(default_speakers["defaultSampleRate"]))

            # setup queue and callback function
            q = queue.Queue()

            def callback(in_data, frame_count, time_info, status):
                """Write frames and return PA flag"""
                IsIntReq()
                if isrecordon:
                    wave_file.writeframes(in_data)
                #
                if status:
                    print(status, file=sys.stderr)
                q.put(bytes(in_data))
                return in_data, pyaudio.paContinue

            # build the model and recognizer objects.
            self.rectext.emit("code1234")  # очистка поля текста
            self.rectext.emit("Пожалуйста, подождите, модель загружается")
            print("===> Build the model and recognizer objects.  This will take a few minutes.")
            # model = Model(r"D:/Programmeas/makesubtitles/vosk-model-ru-0.42")
            # model = Model("models/vosk-model-small-ru-0.22")
            
            # Load the path to model from ini
            if LoadSettingsFromIni('chosen-model'):
                # folpath = 'r"{}"'.format(LoadSettingsFromIni('chosen-model'))
                folpath = '{}'.format(LoadSettingsFromIni('chosen-model'))
                print(folpath)  # (LoadSettingsFromIni('model'))
                model = Model(folpath)  # (LoadSettingsFromIni('model'))
            else:
                self.rectext.emit("Не указан путь для модели")
                print('===> Interrupted. Finished Recording')
                # and save the wav if it's going
                if isrecordon:
                    try:
                        wave_file.close()
                    except Exception as e:
                        self.rectext.emit(str(e))
                raise NameError('NoModelPath')
            
            recognizer = KaldiRecognizer(model, int(default_speakers["defaultSampleRate"]))
            recognizer.SetWords(False)

            print("===> Begin recording. Press Ctrl+C to stop the recording ")
            self.rectext.emit("code1234")  # очистка поля текста
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
                        IsIntReq()
                        if recognizer.AcceptWaveform(data):
                            IsIntReq()
                            recognizerResult = recognizer.Result()
                            results = results + recognizerResult
                            # convert the recognizerResult string into a dictionary
                            resultDict = json.loads(recognizerResult)
                            if not resultDict.get("text", "") == "":
                                # print(recognizerResult)
                                IsIntReq()
                                textResults.append(resultDict.get("text", ""))
                                print(resultDict.get("text", ""))
                                self.rectext.emit(resultDict.get("text", ""))
                            else:
                                print("no input sound")
                                IsIntReq()

            except KeyboardInterrupt:
                # write text portion of results to a file
                with open(outfileText, 'w') as output:
                    print(json.dumps(textResults, indent=4, ensure_ascii=False), file=output)
                print('===> Keyboard Interrupt. Finished Recording')
                # and save the wav if it's going
                if isrecordon:
                    try:
                        wave_file.close()
                    except Exception as e:
                        self.rectext.emit(str(e))

            except NameError as e:
                if str(e) == 'vasya1998':
                    # write text portion of results to a file
                    with open(outfileText, 'w') as output:
                        print(json.dumps(textResults, indent=4, ensure_ascii=False), file=output)
                    print('===> Interrupted. Finished Recording')
                    # and save the wav if it's going
                    if isrecordon:
                        try:
                            wave_file.close()
                        except Exception as e:
                            self.rectext.emit(str(e))


            except Exception as e:
                # write text portion of results to a file
                with open(outfileText, 'w') as output:
                    print(json.dumps(textResults, indent=4, ensure_ascii=False), file=output)
                print(str(e))
                # and save the wav if it's going
                if isrecordon:
                    try:
                        wave_file.close()
                    except Exception as e:
                        self.rectext.emit(str(e))

            if isrecordon:
                wave_file.close()




class MainWindow(QMainWindow):
    _gripSize = 4
    
    # The main function for main window
    def __init__(self):
        super().__init__()
        
        # Variables
        self.settings = QSettings("config.ini", QSettings.Format.IniFormat)
        
        self.worker = None
        self.thread = None
        
        # Main GUI
        # task bar logo for windows
        self.setWindowIcon(QIcon("src/logo.png"))
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('DInc.app.2')

        self.setWindowTitle("ReadThatV2.1")
        self.resize(600, 200)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        central_widget = QWidget()
        # This container holds the window contents, so we can style it. !css
        central_widget.setObjectName("Container")
        central_widget.setStyleSheet(
            """#Container {
                    background: qlineargradient(x1:0 y1:0, x2:1 y2:1, stop:0 #051c2a stop:1 #44315f);
                    border-radius: 5px;
                }
            """
        )
                                                
        # Opacity for the main widget == everything
        OpacityAmount = LoadSettingsFromIni('OpacityAmount')
        op = QGraphicsOpacityEffect()
        op.setOpacity(0.78)
        central_widget.setGraphicsEffect(op)
        
        # Titlebar Announce
        self.title_bar = CustomTitleBar(self)
        
        # Layout which contains text field and buttons on right
        work_space_layout = QHBoxLayout()
        work_space_layout.setContentsMargins(2, 2, 2, 2)
        work_space_layout.setSpacing(1)
        
        # Just the label in the centre (example)
        #hello_label = QLabel("Hello, World!", self)
        #hello_label.setStyleSheet("color: white;")
        #work_space_layout.addWidget(hello_label)
        
        # The main subtitle text field
        self.TheTextField = QTextEdit()# QPlainTextEdit()
        self.TheTextField.setReadOnly(1)
        # It's font size
        #f = self.TheTextField.document().defaultFont()
        #f.setPointSize(16)
        #self.TheTextField.document().setDefaultFont(f)
        #!css
        self.TheTextField.setStyleSheet(
            """QTextEdit {
                font-family: "MS Shell Dlg 2"; 
                font-size: 14pt; 
                font-weight: 400; 
                font-style: normal;
                background-color: #36313d;
                color: #D3D3D3;
                border: none;
            }
            """
        )
        #self.TheTextField.setTextBackgroundColor(QColor("#36313d"))
        #self.TheTextField.setTextColor(QColor("#7d0e59"))
        # Start text
        self.TheTextField.setPlainText("Привет! Тут будет показываться распознанный текст из воспроизведенного в "
                                       "системе звука после того как ты нажмешь на кнопку старта!")
        work_space_layout.addWidget(self.TheTextField)
        
        #Button panel layouts
        ButtonFunc1Panel = QVBoxLayout()
        ButtonFunc1Panel.setContentsMargins(0, 0, 0, 0)
        ButtonFunc2Panel = QVBoxLayout()
        ButtonFunc2Panel.setContentsMargins(0, 0, 0, 0)
         
        # Settings button
        self.OptionsBtn = QToolButton()
        self.OptionsBtn.clicked.connect(self.TheOptions)
        self.OptionsBtn.setMaximumWidth(50)
        self.OptionsBtn.setMinimumWidth(15)
        # self.HideBtn.setMinimumHeight(200)
        self.OptionsBtn.setIcon(QIcon("src/TheSettingsButton.png"))
        self.OptionsBtn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        ButtonFunc1Panel.addWidget(self.OptionsBtn)

        # Start/Stop button
        self.StaPauBtn = QToolButton()
        self.StaPauBtn.clicked.connect(self.runLongTask)
        self.StaPauBtn.setIcon(QIcon("src/TheStartButton.png"))
        self.StaPauBtn.setCheckable(True)
        #Changed the checked state colour !css
        self.StaPauBtn.setStyleSheet(
            """QToolButton:checked {
                background-color: white;
                }
            """
        )
        self.stapau_button_is_checked = 0
        self.StaPauBtn.setMaximumWidth(50)
        self.StaPauBtn.setMinimumWidth(15)
        # self.HideBtn.setMinimum Height(200)
        self.StaPauBtn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        ButtonFunc1Panel.addWidget(self.StaPauBtn)
        self.txtname = ""

        # Save Text button
        self.SaveTxtBtn = QToolButton()
        self.SaveTxtBtn.clicked.connect(self.TheSaveAs)
        self.SaveTxtBtn.setIcon(QIcon("src/TheSaveButton.png"))
        self.SaveTxtBtn.setMaximumWidth(50)
        self.SaveTxtBtn.setMinimumWidth(15)
        # self.HideBtn.setMinimum Height (200)
        self.SaveTxtBtn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        ButtonFunc1Panel.addWidget(self.SaveTxtBtn)
        
        # Putting ButtonFunc1Panel in work_space_layout
        work_space_layout.addLayout(ButtonFunc1Panel)
        
        # Hide button
        self.HideBtn = QToolButton()
        self.HideBtn.clicked.connect(self.TheHideButton)
        self.HideBtn.setCheckable(True)
        #Changed the checked state colour !css
        self.HideBtn.setStyleSheet(
            """QToolButton:checked {
                background-color: #555555;
                }
            """
        )
        self.hide_button_is_checked = 0
        self.HideBtn.setIcon(QIcon("src/TheHideButton.png"))
        self.HideBtn.setMaximumWidth(30)
        self.HideBtn.setMinimumWidth(15)
        # self.HideBtn.setMinimumHeight(200)
        self.HideBtn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        ButtonFunc2Panel.addWidget(self.HideBtn)
        
        # Puttong ButtonFunc2Panel in work_space_layout
        work_space_layout.addLayout(ButtonFunc2Panel)
        
        
        # The main layout which will conatain central widget and titlebar
        centra_widget_layout = QVBoxLayout()
        centra_widget_layout.setContentsMargins(0, 0, 0, 0)
        centra_widget_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        centra_widget_layout.addWidget(self.title_bar)
        centra_widget_layout.addLayout(work_space_layout)

        central_widget.setLayout(centra_widget_layout)
        self.setCentralWidget(central_widget)
        
        # Border with resize property
        self.sideGrips = [
            SideGrip(self, Qt.Edge.LeftEdge), 
            SideGrip(self, Qt.Edge.TopEdge), 
            SideGrip(self, Qt.Edge.RightEdge), 
            SideGrip(self, Qt.Edge.BottomEdge), 
        ]
        
        # Border's color !css
        for grip in self.sideGrips:
            grip.setObjectName("BorderGrips")
            grip.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            grip.setStyleSheet(
                """#BorderGrips {
                        background-color: rgba(0, 0, 0, 100);
                    }
                """
            )
        
        # Corner grips with resize property
        # Should be "on top" of everything, otherwise the side grips
        # Will take precedence on mouse events, so we are adding them *after*;
        # Alternatively, widget.raise_() can be used
        
        # Corners with diagonal resize property
        self.cornerGrips = [QSizeGrip(self) for i in range(4)]
        # Corner's color !css
        for corner in self.cornerGrips:
            corner.setObjectName("CornerGrips")
            corner.setStyleSheet(
                """#CornerGrips {
                       background-color: transparent;
                    }
                """
            )
    
    # Opens the settings window
    def TheOptions(self):
        dlg = SettingsDialog()
        dlg.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        dlg.exec()
    
    # Opens the text save QFileDialog
    def TheSaveAs(self):
        # Setting up variable for text file name if we didn't do it in before
        # The name should have time of start of the record
        # If we aren't recognizing anymore then it's the current time
        # Maybe i shoud change it to always current time? #NoMozgEblya
        # Otherwise it might be confusing and the user will not read anything
        if not self.txtname:
            now = datetime.now()
            fileName, _ = QFileDialog.getSaveFileName(self, 
                                                      "Save File", 
                                                      now.strftime("%Y-%m-%d--%H-%M-%S"),
                                                      "All Files(*);;Text Files(*.txt)")
            print("imintheif") #debug printout
        else:
            fileName, _ = QFileDialog.getSaveFileName(self, 
                                                      "Save File", 
                                                      self.txtname,
                                                      "All Files(*);;Text Files(*.txt)")
        if fileName:
            with open(fileName, 'w', encoding='utf-8') as f:
                output = self.TheTextField.toPlainText()
                output.encode('utf-8')
                f.write(output)
            # self.fileName = fileName
    
    
    def TheHideButton(self, checked):
        if checked:
            self.HideBtn.setIcon(QIcon("src/TheUnhideButton.png"))
            self.OptionsBtn.setVisible(False)
            self.StaPauBtn.setVisible(False)
            self.SaveTxtBtn.setVisible(False)
            self.title_bar.setVisible(False)
            window.show()
        else:
            self.HideBtn.setIcon(QIcon("src/TheHideButton.png"))
            self.OptionsBtn.setVisible(True)
            self.StaPauBtn.setVisible(True)
            self.SaveTxtBtn.setVisible(True)
            self.title_bar.setVisible(True)
            window.show()
    
    # Recognize start
    def runLongTask(self, checked):
        self.stapau_button_is_checked = checked
        if self.stapau_button_is_checked:
            self.OptionsBtn.setEnabled(False)
            self.TheTextField.setPlainText("")  # затрем поле вывода
            self.StaPauBtn.setIcon(QIcon("src/TheStopButton.png"))  # 2 - иконка стоп
            now = datetime.now()
            self.txtname = now.strftime("%Y-%m-%d--%H-%M-%S")
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
            self.thread.requestInterruption()
            # self.thread.stop()
            self.thread.quit()
            # del self.thread
            self.StaPauBtn.setIcon(QIcon("src/TheStartButton.png"))  # 2 - иконка старт
            self.txtname = ""  # имя txt файла
            self.OptionsBtn.setEnabled(True)


    
    @pyqtSlot(str)
    def AcceptRecText(self, string):
        #self.TheTextField.appendPlainText(string)
        self.TheTextField.append(string)
        if string == "code1234":
            self.TheTextField.setPlainText("")  # очищает поле текста

    # Function that catches maximize and minimize event
    """
    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            self.title_bar.window_state_changed(self.windowState())
        super().changeEvent(event)
        event.accept()
    """
    
    # Functions for grip-resize
    @property
    def gripSize(self):
        return self._gripSize

    def setGripSize(self, size):
        if size == self._gripSize:
            return
        self._gripSize = max(2, size)
        self.updateGrips()

    def updateGrips(self):
        self.setContentsMargins(*[self.gripSize] * 4)

        outRect = self.rect()
        # an "inner" rect used for reference to set the geometries of size grips
        inRect = outRect.adjusted(self.gripSize, self.gripSize,
            -self.gripSize, -self.gripSize)

        # top left
        self.cornerGrips[0].setGeometry(
            QRect(outRect.topLeft(), inRect.topLeft()))
        # top right
        self.cornerGrips[1].setGeometry(
            QRect(outRect.topRight(), inRect.topRight()).normalized())
        # bottom right
        self.cornerGrips[2].setGeometry(
            QRect(inRect.bottomRight(), outRect.bottomRight()))
        # bottom left
        self.cornerGrips[3].setGeometry(
            QRect(outRect.bottomLeft(), inRect.bottomLeft()).normalized())

        # left edge
        self.sideGrips[0].setGeometry(
            0, inRect.top(), self.gripSize, inRect.height())
        # top edge
        self.sideGrips[1].setGeometry(
            inRect.left(), 0, inRect.width(), self.gripSize)
        # right edge
        self.sideGrips[2].setGeometry(
            inRect.left() + inRect.width(), 
            inRect.top(), self.gripSize, inRect.height())
        # bottom edge
        self.sideGrips[3].setGeometry(
            self.gripSize, inRect.top() + inRect.height(), 
            inRect.width(), self.gripSize)

    def resizeEvent(self, event):
        QMainWindow.resizeEvent(self, event)
        self.updateGrips()

if __name__ == "__main__":
    app = QApplication([])
    
    window = MainWindow()
    window.show()
    app.exec()