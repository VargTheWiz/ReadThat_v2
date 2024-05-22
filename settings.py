from PyQt6.QtCore import QUrl, QSettings, pyqtSignal, QThread
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QRadioButton, QLabel, QGroupBox, QPushButton, \
    QFileDialog, QProgressBar, QSizePolicy
from settings_chooseanddown import ChAndDo


def LoadSettingsFromIni(value):
    print("ваыпр")
    settings = QSettings("config.ini", QSettings.Format.IniFormat)
    return settings.value(value, defaultValue=None, type=str)


def SaveSettingToIni(parameter, what):
    settings = QSettings("config.ini", QSettings.Format.IniFormat)
    settings.setValue(parameter, what)
    print("srgn")


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("ReadThat - Settings")

        QBtn = QDialogButtonBox.StandardButton.Close  # QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        # Thebut = QDialogButtonBox("asdfasdf")
        # QBtn = QDialogButtonBox()
        # QBtn.addButton("asdfsd", QDialogButtonBox.StandardButton.Close)

        group_box_main = QGroupBox("Основные настройки")

        ChooseModel = QPushButton("Выбрать модель")
        ChooseModel.clicked.connect(self.TheChooseModel)
        CheckUpdates = QPushButton("Загрузить модель")
        CheckUpdates.clicked.connect(self.TheCheckUpdates)
        DeleteModel = QPushButton("Удалить модель")
        DeleteModel.clicked.connect(self.TheDeleteModel)
        RecordFlag = QRadioButton("Записывать аудио во время распознавания")
        if LoadSettingsFromIni('makerecord') == "True":
            RecordFlag.setChecked(True)
        RecordFlag.toggled.connect(lambda: self.TheRecordFlag(RecordFlag))

        settings_layout = QVBoxLayout()
        settings_layout.addWidget(ChooseModel)
        settings_layout.addWidget(CheckUpdates)
        settings_layout.addWidget(DeleteModel)
        settings_layout.addWidget(RecordFlag)

        group_box_main.setLayout(settings_layout)

        buttonBox = QDialogButtonBox(QBtn)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(group_box_main)
        layout.addWidget(buttonBox)
        self.setLayout(layout)

    def TheChooseModel(self):
        folderpath = QFileDialog.getExistingDirectory(self, 'Select Folder')
        print(folderpath)
        SaveSettingToIni('chosen-model', folderpath)

    def TheCheckUpdates(self):
        # url = QUrl("https://alphacephei.com/vosk/models")
        # QDesktopServices.openUrl(url)
        dlg2 = ChAndDo()
        dlg2.exec()

    def TheDeleteModel(self):
        print("del")

    def TheRecordFlag(self, b):
        print("recordflag")
        if b.text() == "Записывать аудио во время распознавания":
            if b.isChecked():
                SaveSettingToIni('makerecord', 'True')
            else:
                SaveSettingToIni('makerecord', 'False')


