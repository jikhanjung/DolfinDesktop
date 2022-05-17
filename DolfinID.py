from PyQt5.QtWidgets import QTableWidgetItem, QMainWindow, QHeaderView, QFileDialog, QCheckBox, \
                            QWidget, QHBoxLayout, QVBoxLayout, QProgressBar, QApplication, \
                            QDialog, QLineEdit, QLabel, QPushButton, QAbstractItemView, \
                            QMessageBox, QListView, QTreeWidgetItem, QToolButton, QTreeView, QFileSystemModel, \
                            QTableView

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
import requests

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
    file_created = DateTimeField()
    file_modified = DateTimeField()
    parent = ForeignKeyField('self', backref='children', null=True)

    class Meta:
        database = db # This model uses the "people.db" database.

class PreferencesDialog(QDialog):
    '''
    PreferencesDialog shows preferences.

    Args:
        None

    Attributes:
        well..
    '''
    def __init__(self,parent):
        super().__init__()
        self.setGeometry(QRect(100, 100, 400, 300))
        self.setWindowTitle("Preferences")
        #self.lbl_main_view.setMinimumSize(400, 300)

        self.parent = parent
        self.lblDolfinIDPrefix = QLabel()
        self.edtDolfinIDPrefix = QLineEdit()
        self.lblDataFolder = QLabel()
        self.edtDataFolder = QLineEdit()

        self.btnDataFolder = QPushButton()
        self.btnDataFolder.setText("Select Folder")
        self.btnDataFolder.clicked.connect(self.select_folder)

        self.btnOkay = QPushButton()
        self.btnOkay.setText("OK")
        self.btnOkay.clicked.connect(self.Okay)

        self.btnCancel = QPushButton()
        self.btnCancel.setText("Cancel")
        self.btnCancel.clicked.connect(self.Cancel)


        self.layout = QVBoxLayout()
        #self.layout1 = QHBoxLayout()
        #self.layout1.addWidget(self.lblDolfinIDPrefix)
        #self.layout1.addWidget(self.edtDolfinIDPrefix)
        self.layout2 = QHBoxLayout()
        self.layout2.addWidget(self.lblDataFolder)
        self.layout2.addWidget(self.edtDataFolder)
        self.layout2.addWidget(self.btnDataFolder)
        self.layout3 = QHBoxLayout()
        self.layout3.addWidget(self.btnOkay)
        self.layout3.addWidget(self.btnCancel)
        #self.layout.addLayout(self.layout1)
        self.layout.addLayout(self.layout2)
        self.layout.addLayout(self.layout3)
        self.setLayout(self.layout)
        #self.dolfinid_prefix = ''
        self.data_folder = ''
        print("pref dlg data_folder:", self.data_folder)
        self.read_settings()
        print("pref dlg data_folder:", self.data_folder)
        self.lblDolfinIDPrefix.setText("Dolfin ID Prefix")
        self.lblDataFolder.setText("Data Folder")
        self.edtDolfinIDPrefix.setText("")
        self.edtDataFolder.setText(str(self.data_folder.resolve()))

    def write_settings(self):
        #self.parent.dolfinid_prefix = self.edtDolfinIDPrefix.text()
        self.parent.data_folder = Path(self.edtDataFolder.text())
        #print( self.parent.dolfinid_prefix, self.parent.data_folder)

    def read_settings(self):
        #self.dolfinid_prefix = self.parent.dolfinid_prefix
        self.data_folder = self.parent.data_folder.resolve()
        print("pref dlg data folder:", self.data_folder)

    def Okay(self):
        self.write_settings()
        self.close()

    def Cancel(self):
        self.close()

    def select_folder(self):
        folder = str(QFileDialog.getExistingDirectory(self, "Select Folder", str(self.data_folder)))
        if folder:
            self.data_folder = Path(folder).resolve()
            self.edtDataFolder.setText(folder)



form_class = uic.loadUiType("DolfinID.ui")[0]
class DolfinIDWindow(QMainWindow, form_class):

    def check_db(self):
        db.connect()
        tables = db.get_tables()
        if tables:
            return
            print(tables)
        else:
            db.create_tables([DolfinImageFile])
        
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.read_settings()
        self.check_db()
        #self.treeView = QTreeView()
        '''
        self.fileSystemModel = QFileSystemModel(self.treeView)
        self.fileSystemModel.setReadOnly(False)
        self.fileSystemModel.setNameFilters(["*.jpg"])
        root = self.fileSystemModel.setRootPath(str(self.data_folder))
        self.fileSystemModel.setNameFilterDisables(False)
        self.treeView.setModel(self.fileSystemModel)
        self.treeView.setRootIndex(root)
        self.treeView.setColumnWidth(0, 300)
        self.treeView.setColumnWidth(1, 100)
        self.treeView.setColumnHidden(2,True)
        self.treeView.setColumnHidden(3,True)
        '''
        self.actionPreferences.triggered.connect(self.open_preferences)

        #self.treeView.doubleClicked.connect(self.treeViewDoubleClicked)

        self.pushButton.clicked.connect(self.pushButtonClicked)
        self.pushButton_2.clicked.connect(self.pushButton2Clicked)
        self.pushButton_3.clicked.connect(self.pushButton3Clicked)
        #self.data_folder = Path('.')
        self.dir_model = QStandardItemModel()
        self.file_model = QStandardItemModel()
        self.file_model.setColumnCount(2)
        self.treeView.setModel(self.dir_model)
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.file_model)
        self.listView.setModel(self.proxy_model)
        self.tableView.setModel(self.proxy_model)
        self.tableView.setSelectionBehavior(QTableView.SelectRows)
        self.tableView.hideColumn(1)
        #self.tableView.hideColumn(1)


        self.treeView.setHeaderHidden( True )
        self.tableView.horizontalHeader().hide()
        self.tableView.verticalHeader().hide()

        self.treeView.expandAll()
        #print("__init__ dir model row count:", self.dir_model.rowCount())
        self.dirSelModel = self.treeView.selectionModel()
        self.dirSelModel.selectionChanged.connect(self.dirSelectionChanged)
        self.fileSelModel = self.listView.selectionModel()
        self.fileSelModel.selectionChanged.connect(self.fileSelectionChanged)
        self.fileSelModel2 = self.tableView.selectionModel()
        self.fileSelModel2.selectionChanged.connect(self.fileSelectionChanged)

        self.dir_record_tree = []
        self.file_record_hash = {}
        self.dir_list = []
        self.file_list = []

    def get_hash(self,path, blocksize=65536):
        afile = open(path, 'rb')
        hasher = hashlib.md5()
        buf = afile.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = afile.read(blocksize)
        afile.close()
        return hasher.hexdigest()

    def fileSelectionChanged(self):
        return
        index = self.fileSelModel.currentIndex()
        print(index,index.row())
        item1 = self.file_model.item(index.row(),0)
        item2 = self.file_model.item(index.row(),1)
        print(item1.text(),item2.text() )

        index_list = self.fileSelModel.selection().indexes()
        print(index_list)
        item1 = self.file_model.itemFromIndex(index_list[0])
        print(item1, item1.text())
        #item2 = self.file_model.itemFromIndex(index_list[1])
        #print(item2, item2.text())


    def dirSelectionChanged(self):
        index_list = self.dirSelModel.selection().indexes()
        #print(index_list)
        item1 = self.dir_model.itemFromIndex(index_list[0])
        #print(item1, item1.text())
        item2 = self.dir_model.itemFromIndex(index_list[1])
        #print(item2, item2.text())
        filter_text = item2.text()
        #print(filter_text)
        #filter_text.replace("\\","\\\\")
        print("filter text:", filter_text)

        self.proxy_model.setFilterRegExp(QRegExp('^'+filter_text+'$', Qt.CaseInsensitive))
        self.proxy_model.setFilterKeyColumn(1)
        #print()

    def load_subdir (self,item,children):
        #print("load subdir", item, children)
        for rec in children:
            if rec.type == 'file':
                sub_item1 = QStandardItem(Path(rec.path).name)
                sub_item2 = QStandardItem(str(Path(rec.path).parent.as_posix()))
                #print( sub_item1.text(), sub_item2.text() )
                self.file_model.appendRow([sub_item1,sub_item2])
                #print("column count:", self.file_model.columnCount())
                #print(self.file_model.item(0,0).text(),self.file_model.item(0,1).text())
            else:
                sub_item1 = QStandardItem(Path(rec.path).name)
                sub_item2 = QStandardItem(str(Path(rec.path).as_posix()))
                #sub_item.setData(rec)
                item.appendRow([sub_item1,sub_item2])
                if rec.children:
                    self.load_subdir(sub_item1, rec.children)
        return
    
    def load_dir(self):
        all_record = DolfinImageFile.filter(type='dir',parent=None)

        for rec in all_record:
            #print(rec.path)
            #print("readdir 1 dir model row count:", self.dir_model.rowCount())
            item1 = QStandardItem(Path(rec.path).name)
            item2 = QStandardItem(rec.path)
            self.dir_model.appendRow([item1,item2] )
            if rec.children:
                self.load_subdir(item1,rec.children)
            #item.setData(rec)
            #root = self.dir_model.invisibleRootItem()
            #print(root,root.index(), "("+root.text()+")")
            #self.dir_model.appendRow(item)
            #print("readdir2 dir model row count:", self.dir_model.rowCount())
        self.treeView.expandAll()
        self.treeView.hideColumn(1)
        #self.listView.hideColumn(1)
        #self.treeView.setColumnWidth( 2, 50 )
            
        '''
        model = QStandardItemModel()
        parentItem = model.invisibleRootItem()
        for i in range(4):
            item = QStandardItem("item %d" % i)
            parentItem.appendRow(item)
            parentItem = item'''

    def upload_file(self):
        index = self.tableView.currentIndex()
        print(index)

        selected_index_list = self.fileSelModel2.selection().indexes()
        if len(selected_index_list) == 0:
            return
        print("selected_index",selected_index_list)

        new_index_list = []
        model = selected_index_list[0].model()
        if hasattr(model, 'mapToSource'):
            for index in selected_index_list:
                new_index = model.mapToSource(index)
                new_index_list.append(new_index)
        print("new_index_list",new_index_list)
        item_text_list = []
        for index in new_index_list:
            item = self.file_model.itemFromIndex(index)
            print("item_text:",item.text())
            item_text_list.append(item.text())
        filepath = item_text_list[1]
        filename = item_text_list[0]
        #item_text_list.reverse()
        path = Path(filepath,filename).resolve()
        #path = 
        print(path)
        hash_val = ''

        if os.path.exists(path):
            hash_val = self.get_hash(path)
            print(hash_val)
        else:
            return
        data_hash = {'title':'test','filepath':filepath,'filename':filename,'md5hash':hash_val}

        fd = open(path, 'rb')
        file_hash = {'imagefile': fd}   
        #fields = {'title':'test','filename':item_text_list[1],'md5hash':hash_val,"imagefile": fd}
        #print(fields)

        post_url = "http://127.0.0.1:8000/dolfinrest/dolfinimage_list/"

        #print(requests.Request('POST', post_url, files=file_hash, data=data_hash).prepare().body)
        response = requests.post(post_url, files=file_hash,data=data_hash)
        
        print(response)
        print(response.json())
        #log = open("log.txt","w")
        #log.write(str(response.json()))
        #log.close()
        



    def pushButton3Clicked(self):
        self.upload_file()


    def pushButton2Clicked(self):
        self.load_dir()
        #self.treeView.hideColumn(2)

    def pushButtonClicked(self):
        print("reading tree", datetime.now())
        rootdir = self.data_folder
        self.setRootdir(rootdir)

        #fd = open("output.log","w")
        print("checking database", datetime.now())
        dir_hash = {}
        #rec_list = [ self.dir_list, ]
        with db.atomic() as txn:
            for list in [ self.dir_list, self.file_list ]:
                for f in list:
                    #print(f)
                    fullpath = Path(f[0])
                    #stem = fullpath.stem
                    fname = fullpath.name
                    rec_image = DolfinImageFile.get_or_none( path=str(fullpath) )
                    if not rec_image:
                        #print("no such record"+str(f)+"\n")
                        #print(str(dir_hash))
                        #print(stem)
                        if str(fullpath.parent) in dir_hash.keys():
                            parent = dir_hash[str(fullpath.parent)]
                            #print(fullpath.parent)
                        else:
                            #print("no key")
                            #print(dir_hash.keys(), fullpath.parent)
                            parent = None
                        rec_image = DolfinImageFile(path=f[0],type=f[1],name=fname,file_created=f[2],file_modified=f[3],size=f[4],md5hash='',uploaded=False)
                        rec_image.parent=parent
                        rec_image.save()
                        if f[1] == 'dir':
                            dir_hash[str(fullpath)] = rec_image
                            #print(rec_image)
                            #print(dir_hash)
                    else:
                        pass
        #fd.writepstr(dir_hash))
        print(dir_hash)
                #print("already_exist", f)
            #print(stem, fname)
            #fd.write(str(f)+"\n")
        #fd.close()
        print("database done", datetime.now())


        #print(self.fs_list)

    def treeViewDoubleClicked(self):
        index = self.treeView.currentIndex()
        print(index)
        self.treeView.setCurrentIndex(index)
        #self.stackedWidget.setCurrentIndex(CLOSEUP_VIEW)

    def updateRootdir(self,rootdir):
        for (root,dirs,files) in os.walk(rootdir, topdown=True):
            dir_path = Path(root).resolve()
            stat_result = os.stat(dir_path)
            rec_dir = DolfinImageFile.get_or_none( path=str(dir_path) )
            if rec_dir and datetime.fromtimestamp(rec_dir.file_modified) == rec_dir.file_modified: #디렉토리 변경 시간이 기록된 것과 같으면
                continue

            self.dir_list.append([str(dir_path),'dir',datetime.fromtimestamp(stat_result.st_ctime),datetime.fromtimestamp(stat_result.st_mtime),jpg_count])
            #print(root,dirs,len(files),files[:10])
            #print(dirs)
            #for dir in dirs:
            #print(files)
            for file in files:
                file_path = Path(root,file).resolve()
                if file_path.suffix.upper() != '.JPG':
                    #print(file_path, file_path.suffix)
                    continue
                jpg_count += 1
                stat_result = os.stat(file_path)
                #print(file_path.suffix)#if file_path.suffix != 
                #print(file_path, rootdir)
                #rel_path = file_path.relative_to(Path(rootdir).resolve())
                self.file_list.append([str(file_path),'file',datetime.fromtimestamp(stat_result.st_ctime),datetime.fromtimestamp(stat_result.st_mtime),stat_result.st_size])

            if jpg_count + len(dirs) > 0:
                #print(dir_path, rootdir)
                #rel_path = dir_path.relative_to(Path(rootdir).resolve())
                #if str(rel_path) == ".":
                #    rel_path = Path(rootdir).resolve()
                pass
    
    
    def setRootdir(self,rootdir):
        #rootdir = 
        #rootpath = Path(rootdir).resolve()
        #stat_result = os.stat(rootpath)

        #self.fs_list.append([str(rootpath),'dir',datetime.fromtimestamp(stat_result.st_ctime), datetime.fromtimestamp(stat_result.st_mtime),0])

        for (root,dirs,files) in os.walk(rootdir, topdown=True):
            #print(root,dirs,len(files),files[:10])
            #print(dirs)
            #for dir in dirs:
            #print(files)
            jpg_count = 0
            for file in files:
                file_path = Path(root,file).resolve()
                if file_path.suffix.upper() != '.JPG':
                    #print(file_path, file_path.suffix)
                    continue
                jpg_count += 1
                stat_result = os.stat(file_path)
                #print(file_path.suffix)#if file_path.suffix != 
                #print(file_path, rootdir)
                #rel_path = file_path.relative_to(Path(rootdir).resolve())
                self.file_list.append([str(file_path),'file',datetime.fromtimestamp(stat_result.st_ctime),datetime.fromtimestamp(stat_result.st_mtime),stat_result.st_size])

            if jpg_count + len(dirs) > 0:
                dir_path = Path(root).resolve()
                stat_result = os.stat(dir_path)
                #print(dir_path, rootdir)
                #rel_path = dir_path.relative_to(Path(rootdir).resolve())
                #if str(rel_path) == ".":
                #    rel_path = Path(rootdir).resolve()
                self.dir_list.append([str(dir_path),'dir',datetime.fromtimestamp(stat_result.st_ctime),datetime.fromtimestamp(stat_result.st_mtime),jpg_count])

    
    def closeEvent(self, event):
        #if self.mainview_dlg is not None:
        #    self.mainview_dlg.close()
        print("closing")
        self.write_settings()

    def write_settings(self):
        #print("write settings", str(self.data_folder))
        settings = QSettings(QSettings.IniFormat, QSettings.UserScope,"DiploSoft", "DolfinID")

        settings.beginGroup("Defaults")
        #settings.setValue("DolfinID prefix", self.dolfinid_prefix)
        settings.setValue("Data Folder", str(self.data_folder))
        settings.endGroup()

    def read_settings(self):
        #print("read settings")
        settings = QSettings(QSettings.IniFormat, QSettings.UserScope,"DiploSoft", "DolfinID")

        settings.beginGroup("Defaults")
        #self.dolfinid_prefix = settings.value("DolfinID prefix", "JTA")
        self.data_folder = Path(settings.value("Data Folder", "./"))
        self.working_folder = self.data_folder
        settings.endGroup()


    def open_preferences(self):
        self.preferences_dialog = PreferencesDialog(self)
        self.preferences_dialog.parent = self
        self.preferences_dialog.show()


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
