from PyQt5.QtWidgets import QTableWidgetItem, QMainWindow, QHeaderView, QFileDialog, QCheckBox, \
                            QWidget, QHBoxLayout, QVBoxLayout, QProgressBar, QApplication, \
                            QDialog, QLineEdit, QLabel, QPushButton, QAbstractItemView, \
                            QMessageBox, QListView, QTreeWidgetItem, QToolButton, QTreeView, QFileSystemModel

from PyQt5 import uic
from PyQt5.QtGui import QIcon, QColor, QPainter, QPen, QPixmap, QStandardItemModel, QStandardItem,\
                        QPainterPath, QFont, QImageReader
from PyQt5.QtCore import Qt, QRect, QSortFilterProxyModel, QSettings, QEvent, QRegExp, QSize, \
                         QItemSelectionModel, QDateTime, QBuffer, QIODevice, QByteArray

import sys

PROGRAM_NAME = "DolfinID"
PROGRAM_VERSION = "0.0.1"


form_class = uic.loadUiType("DolfinID.ui")[0]

class DolfinIDWindow(QMainWindow, form_class):

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        #self.treeView = QTreeView()
        self.fileSystemModel = QFileSystemModel(self.treeView)
        self.fileSystemModel.setReadOnly(False)
        self.fileSystemModel.setNameFilters(["*.jpg"])
        root = self.fileSystemModel.setRootPath('D:/DolfinID/')
        self.fileSystemModel.setNameFilterDisables(False)
        self.treeView.setModel(self.fileSystemModel)
        self.treeView.setRootIndex(root)
        self.treeView.setColumnWidth(0, 300)
        self.treeView.setColumnWidth(1, 100)
        self.treeView.setColumnHidden(2,True)
        self.treeView.setColumnHidden(3,True)
#app = QApplication(sys.argv)
#treeView = QTreeView()
#fileSystemModel = QFileSystemModel(treeView)
#fileSystemModel.setReadOnly(False)
#root = fileSystemModel.setRootPath('.')
#treeView.setModel(fileSystemModel)
#treeView.setRootIndex(root)
#treeView.show()
#app.exec_()

if __name__ == "__main__":
    #QApplication : 프로그램을 실행시켜주는 클래스
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('marc_icon.png'))

    #WindowClass의 인스턴스 생성
    myWindow = DolfinIDWindow()

    #프로그램 화면을 보여주는 코드
    myWindow.show()

    #프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()
