from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QRadioButton, QLabel, QGroupBox, QPushButton


def LoadSettingsFromIni(self):
    print("ваыпр")


def SaveSettingToIni(parameter, what):
    print("srgn")


class CustomDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("ReadThat - Settings")

        QBtn = QDialogButtonBox.StandardButton.Close  # QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        # Thebut = QDialogButtonBox("asdfasdf")
        # QBtn = QDialogButtonBox()
        # QBtn.addButton("asdfsd", QDialogButtonBox.StandardButton.Close)

        group_box = QGroupBox("Основные настройки")

        ChooseModel = QPushButton("Выбрать модель")
        ChooseModel.clicked.connect(self.TheChooseModel)
        CheckUpdates = QPushButton("Посмотреть обновления")
        CheckUpdates.clicked.connect(self.TheCheckUpdates)
        DeleteModel = QPushButton("Удалить модель")
        DeleteModel.clicked.connect(self.TheDeleteModel)

        settings_layout = QVBoxLayout()
        settings_layout.addWidget(ChooseModel)
        settings_layout.addWidget(CheckUpdates)
        settings_layout.addWidget(DeleteModel)

        group_box.setLayout(settings_layout)

        buttonBox = QDialogButtonBox(QBtn)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(group_box)
        layout.addWidget(buttonBox)
        self.setLayout(layout)

    def TheChooseModel(self):
        print("choose")

    def TheCheckUpdates(self):
        url = QUrl("https://alphacephei.com/vosk/models")
        QDesktopServices.openUrl(url)
        print("check")

    def TheDeleteModel(self):
        print("del")


