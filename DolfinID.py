from PyQt5.QtWidgets import QTableWidgetItem, QMainWindow, QHeaderView, QFileDialog, QCheckBox, \
                            QWidget, QHBoxLayout, QVBoxLayout, QProgressBar, QApplication, \
                            QDialog, QLineEdit, QLabel, QPushButton, QAbstractItemView, \
                            QMessageBox, QListView, QTreeWidgetItem, QToolButton, QTreeView, QFileSystemModel

from PyQt5 import uic
from PyQt5.QtGui import QIcon, QColor, QPainter, QPen, QPixmap, QStandardItemModel, QStandardItem,\
                        QPainterPath, QFont, QImageReader
from PyQt5.QtCore import Qt, QRect, QSortFilterProxyModel, QSettings, QEvent, QRegExp, QSize, \
                         QItemSelectionModel, QDateTime, QBuffer, QIODevice, QByteArray

import os,sys
from pathlib import Path
from peewee import *
import hashlib
from datetime import datetime, timezone

PROGRAM_NAME = "DolfinID"
PROGRAM_VERSION = "0.0.1"

db = SqliteDatabase('dolfinid.db')

class DolfinImageFile(Model):
    path = CharField()
    type = CharField()
    name = CharField()
    md5hash = CharField()
    uploaded = BooleanField()
    size = IntegerField()
    file_created = TimestampField()
    file_modified = DateTimeField()
    parent = ForeignKeyField('self', backref='children', null=True)

    class Meta:
        database = db # This model uses the "people.db" database.


form_class = uic.loadUiType("DolfinID.ui")[0]
class DolfinIDWindow(QMainWindow, form_class):

    def check_db(self):
        db.connect()
        tables = db.get_tables()
        if tables:
            print(tables)
        else:
            db.create_tables([DolfinImageFile])
        


    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.check_db()
        #self.treeView = QTreeView()
        self.fileSystemModel = QFileSystemModel(self.treeView)
        self.fileSystemModel.setReadOnly(False)
        self.fileSystemModel.setNameFilters(["*.jpg"])
        root = self.fileSystemModel.setRootPath('D:/Dropbox/DolfinID/')
        self.fileSystemModel.setNameFilterDisables(False)
        self.treeView.setModel(self.fileSystemModel)
        self.treeView.setRootIndex(root)
        self.treeView.setColumnWidth(0, 300)
        self.treeView.setColumnWidth(1, 100)
        self.treeView.setColumnHidden(2,True)
        self.treeView.setColumnHidden(3,True)

        self.treeView.doubleClicked.connect(self.treeViewDoubleClicked)

        self.pushButton.clicked.connect(self.pushButtonClicked)
        self.fs_list = []

    def pushButtonClicked(self):
        print("reading tree")
        self.set_rootdir()
        #fd = open("output.log","w")
        print("checking database")
        dir_hash = {}
        for f in self.fs_list:
            #print(f)
            fullpath = Path(f[0])
            stem = fullpath.stem
            fname = fullpath.name
            rec_image = DolfinImageFile.get_or_none( path=fullpath )
            if not rec_image:
                #print("no such record", f)
                if stem in dir_hash.keys():
                    parent = dir_hash[f[0]]
                else:
                    parent = None
                rec_image = DolfinImageFile(path=f[0],type=f[1],name=fname,file_created=f[2],file_modified=f[3],size=f[4],md5hash='',uploaded=False,parent=parent)
                rec_image.save()
                if type == 'dir':
                    dir_hash[f[0]] = rec_image
            else:
                pass
                #print("already_exist", f)
            #print(stem, fname)
            #fd.write(str(f)+"\n")
        #fd.close()
        print("database done")


        #print(self.fs_list)

    def treeViewDoubleClicked(self):
        index = self.treeView.currentIndex()
        print(index)
        self.treeView.setCurrentIndex(index)
        #self.stackedWidget.setCurrentIndex(CLOSEUP_VIEW)

    def set_rootdir(self):
        rootdir = 'D:/Dropbox/DolfinID'
        rootpath = Path(rootdir).resolve()
        stat_result = os.stat(rootpath)
        self.fs_list.append([str(rootpath),'dir',datetime.fromtimestamp(stat_result.st_ctime), datetime.fromtimestamp(stat_result.st_mtime),0])

        for (root,dirs,files) in os.walk(rootdir, topdown=True):
            #print(root)
            #print(dirs)
            for dir in dirs:
                dir_path = Path(root,dir).resolve()
                stat_result = os.stat(dir_path)
                if not list(dir_path.rglob("*.JPG")) and not list(dir_path.rglob("*.jpg")):
                    #print("no jpg file in dir", dir_path)
                    continue
                self.fs_list.append([str(dir_path),'dir',datetime.fromtimestamp(stat_result.st_ctime),datetime.fromtimestamp(stat_result.st_mtime),0])
            #print(files)
            for file in files:
                file_path = Path(root,file).resolve()
                if file_path.suffix.upper() != '.JPG':
                    #print(file_path, file_path.suffix)
                    continue
                stat_result = os.stat(file_path)
                #print(file_path.suffix)#if file_path.suffix != 
                self.fs_list.append([str(file_path),'file',datetime.fromtimestamp(stat_result.st_ctime),datetime.fromtimestamp(stat_result.st_mtime),stat_result.st_size])
    


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
