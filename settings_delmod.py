from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QGroupBox, QLabel, QComboBox, QVBoxLayout, QPushButton, QMessageBox
import os
import shutil


class DelMod(QDialog):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Read That - Delete Model")

        QBtn = QDialogButtonBox.StandardButton.Close

        group_box_main = QGroupBox("Удаление модели")

        self.label1 = QLabel("Выберете модель для удаления.", self)
        self.label2 = QLabel("Внимание! Модель удаляется окончательно.", self)

        self.combobox = QComboBox()

        self.thelist = os.listdir('models/')
        self.combobox.addItems(self.thelist)

        self.delutton = QPushButton("Удалить выбранную модель", self)
        self.delutton.clicked.connect(self.TheDelButton)

        delmod_layout = QVBoxLayout()
        delmod_layout.addWidget(self.label1)
        delmod_layout.addWidget(self.label2)
        delmod_layout.addWidget(self.combobox)
        delmod_layout.addWidget(self.delutton)

        group_box_main.setLayout(delmod_layout)

        buttonBox = QDialogButtonBox(QBtn)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addWidget(group_box_main)

        layout.addWidget(buttonBox)
        self.setLayout(layout)

    def TheDelButton(self):
        folderpath = 'models/'+self.thelist[self.combobox.currentIndex()]
        qm = QMessageBox()

        ret = qm.question(self, '', "Вы уверены что хотите удалить модель?", qm.StandardButton.Yes | qm.StandardButton.No)

        if ret == qm.StandardButton.Yes:
            try:
                print("удалил!") #shutil.rmtree(folderpath)  # ааа страшна
                qm.information(self, '', "Модель успешно удалена")
            except OSError as e:
                print("Error: %s - %s." % (e.filename, e.strerror))
                qm.information(self, '', "Ошибка: %s - %s." % (e.filename, e.strerror))
            print(folderpath)
        else:
            qm.information(self, '', "Операция удаления отменена")

