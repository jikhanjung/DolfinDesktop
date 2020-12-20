import webbrowser
import json
from datetime import datetime

import os
import sys
from pathlib import Path
import csv
import pickle

from PyQt5.QtWidgets import QTableWidgetItem, QMainWindow, QHeaderView, QFileDialog, QCheckBox, \
                            QWidget, QHBoxLayout, QApplication
from PyQt5 import uic
from PyQt5.QtGui import QIcon, QImageReader, QPixmap
from PyQt5.QtCore import Qt, QBuffer, QIODevice

from DolfinRecord import DolfinRecord

form_class = uic.loadUiType("DolfinExtractor.ui")[0]

PROGRAM_NAME = "DolfinExtractor"
PROGRAM_VERSION = "0.0.2"

class DolfinExtractorWindow(QMainWindow, form_class):
    '''
    DolfinExtractorWindow is the main window of DolfinExtractor application

    Args:
        None

    Attributes:
    '''

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.btnOpenFolder.clicked.connect(self.open_folder_function)
        self.btnClear.clicked.connect(self.clear_table)
        self.btnExportJS.clicked.connect(self.export_javascript)
        self.btnShowInMap.clicked.connect(self.show_in_map)
        self.btnExportFinImages.clicked.connect(self.export_fin_images)
        #self.btnExportFinImages.setEnabled(False)
        self.path_list = []
        self.checkbox_list = []
        self.working_folder = Path("./")
        self.setWindowTitle(PROGRAM_NAME + " " + PROGRAM_VERSION)
        self.setWindowIcon(QIcon('marc_icon.png'))

        self.set_table_header()

    def show_in_map(self):
        url = "file://" + str(Path("./DolfinExplorerKakao.html").resolve())
        print(url)
        webbrowser.open(url,new=2)

    def set_table_header(self):
        self.tblSubfolders.setColumnCount(5)
        header = self.tblSubfolders.horizontalHeader()
        self.tblSubfolders.setColumnWidth(0, 10)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.tblSubfolders.setColumnWidth(2, 100)
        self.tblSubfolders.setColumnWidth(3, 100)
        self.tblSubfolders.setColumnWidth(4, 100)
        header_item0 = QTableWidgetItem("")
        header_item1 = QTableWidgetItem("Folder Name")
        header_item2 = QTableWidgetItem("Fins with ID")
        header_item3 = QTableWidgetItem("Total Fins")
        header_item4 = QTableWidgetItem("Image files")
        self.tblSubfolders.setHorizontalHeaderItem(0,header_item0)
        self.tblSubfolders.setHorizontalHeaderItem(1,header_item1)
        self.tblSubfolders.setHorizontalHeaderItem(2,header_item2)
        self.tblSubfolders.setHorizontalHeaderItem(3,header_item3)
        self.tblSubfolders.setHorizontalHeaderItem(4,header_item4)
        self.tblSubfolders.verticalHeader().setVisible(False)


    def clear_table(self):
        self.tblSubfolders.clear()
        self.path_list = []
        self.tblSubfolders.setRowCount(0)
        self.set_table_header()

    def open_folder_function(self):
        parent_folder = str(self.working_folder.parent)
        open_dir = QFileDialog.getExistingDirectory(self, 'Open directory', parent_folder)
        #print( "dir:", open_dir )
        if open_dir == '':
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.edtFolder.setText(open_dir)
        self.working_folder = Path(open_dir)

        dir_list = [f for f in os.listdir(str(self.working_folder))]

        current_row = 0
        for item in dir_list:
            #print(item)
            full_path = self.working_folder.joinpath(item)
            if os.path.isdir(str(full_path)):
                image_name_list = []
                csv_path = full_path.joinpath( full_path.name + ".csv" )
                #icondb_path = full_path.joinpath( full_path.name + ".icondb" )
                #finicon_hash = load_and_unpickle_image_hash( icondb_path )
                #print( csv_path )

                if csv_path.exists():
                    self.path_list.append(full_path)
                    with open(str(csv_path), newline='',encoding='utf-8') as csvfile:
                        reader = csv.DictReader(csvfile)
                        row_count = 0
                        finid_count = 0
                        for row in reader:
                            row_count += 1
                            image_name = row['image_name']
                            if image_name not in image_name_list:
                                image_name_list.append(image_name)
                            fin_record  = DolfinRecord( row )
                            if fin_record.dolfin_id != '':
                                finid_count += 1

                    image_count = len(image_name_list)
                    table_row_count = self.tblSubfolders.rowCount()
                    checkbox = QCheckBox()
                    checkbox.setChecked(True)
                    cbx_widget = QWidget()
                    cbx_layout = QHBoxLayout(cbx_widget)
                    cbx_layout.addWidget(checkbox)
                    cbx_layout.setAlignment(Qt.AlignCenter)
                    cbx_layout.setContentsMargins(0,0,0,0)

                    item1 = QTableWidgetItem( full_path.name )
                    item1.setTextAlignment(int(Qt.AlignLeft|Qt.AlignVCenter))
                    item2 = QTableWidgetItem(str(finid_count))
                    item2.setTextAlignment(int(Qt.AlignRight|Qt.AlignVCenter))
                    item3 = QTableWidgetItem(str(row_count))
                    item3.setTextAlignment(int(Qt.AlignRight|Qt.AlignVCenter))
                    item4 = QTableWidgetItem(str(image_count))
                    item4.setTextAlignment(int(Qt.AlignRight|Qt.AlignVCenter))
                    self.tblSubfolders.insertRow(table_row_count)
                    self.checkbox_list.append(checkbox)
                    self.tblSubfolders.setCellWidget ( current_row, 0, cbx_widget)
                    self.tblSubfolders.setItem(current_row, 1, item1)
                    self.tblSubfolders.setItem(current_row, 2, item2)
                    self.tblSubfolders.setItem(current_row, 3, item3)
                    self.tblSubfolders.setItem(current_row, 4, item4)
                    current_row += 1


        QApplication.restoreOverrideCursor()

    def export_javascript(self):
        """
        docstring
        """
        QApplication.setOverrideCursor(Qt.WaitCursor)
        occurrence_hash = {}
        #lat_min, lon_min, lat_max, lon_max = 999,999,0,0
        for current_path in self.path_list:
            csv_path = current_path.joinpath( current_path.name + ".csv" )
            #icondb_path = p.joinpath( p.name + ".icondb" )
            #finicon_hash = load_and_unpickle_image_hash( icondb_path )
            #print( csv_path )

            if csv_path.exists():

                with open(str(csv_path), newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)

                    #prev_image_name = ''

                    for row in reader:
                        fin_record  = DolfinRecord( row )

                        if fin_record.dolfin_id == '':
                            continue

                        image_name = fin_record.image_name
                        image_datetime = fin_record.image_datetime
                        image_date, image_time = image_datetime.split(" ")
                        lat, lon = fin_record.get_decimal_latitude_longitude()
                        finid = fin_record.dolfin_id

                        if image_name not in occurrence_hash.keys():
                            occurrence_hash[image_name] = {'image_date': image_date,
                                                           'image_time': image_time,
                                                           'latitude': lat, 'longitude': lon,
                                                           'finid_list': []}

                        occurrence_hash[image_name]['finid_list'].append(finid)


        json_object = "var dolfinid_occurrence_data = " + json.dumps(occurrence_hash, indent = 4) + ";"
        #print( lat_min, lat_max, lon_min, lon_max )
        #print(json_object)

        with open("dolfinid_occurrence_data.js", 'w', newline='', encoding='utf-8') as jsfile:
            jsfile.write(json_object)
        jsfile.close()
        QApplication.restoreOverrideCursor()

    def load_and_unpickle_image_hash(self, filepath):
        image_hash = {}

        bytearray_hash = pickle.load(open(filepath, "rb"))

        for k in bytearray_hash.keys():
            byte_array = bytearray_hash[k]

            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.ReadOnly)
            reader = QImageReader(buffer)
            img = reader.read()
            image_hash[k] = img
        return image_hash

    def export_fin_images(self):
        """
        docstring
        """
        QApplication.setOverrideCursor(Qt.WaitCursor)
        finid_hash = {}
        finid_folder = "./finid_images"
        finid_basepath = Path(finid_folder)
        
        for current_path in self.path_list:
            csv_path = current_path.joinpath( current_path.name + ".csv" )
            icondb_path = current_path.joinpath( current_path.name + ".icondb" )
            finicon_hash = self.load_and_unpickle_image_hash( icondb_path )
            #print( csv_path )

            if csv_path.exists():

                with open(str(csv_path), newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)

                    #prev_image_name = ''

                    for row in reader:
                        fin_record  = DolfinRecord( row )
                        if fin_record.dolfin_id == '':
                            continue
                        
                        finid = fin_record.dolfin_id
                        if finid not in finid_hash.keys():
                            finid_hash[finid] = []
                        
                        finid_path = finid_basepath.joinpath(finid)
                        if not os.path.exists(str(finid_path)):
                            os.makedirs(finid_path) # make new output folder  

                        date_time_obj = datetime.strptime(fin_record.image_datetime, '%Y-%m-%d %H:%M:%S')
                        yyyymmdd = date_time_obj.strftime( '%Y%m%d')

                        finid_filename = "{}_{}.JPG".format(yyyymmdd, fin_record.get_finname()) 

                        finid_filepath = finid_path.joinpath(finid_filename)
                        icon_pixmap = QPixmap(finicon_hash[fin_record.get_finname()])
                        print(finid_filepath)
                        fin_img = icon_pixmap.toImage()
                        fin_img.save(str(finid_filepath))

        QApplication.restoreOverrideCursor()        



if __name__ == "__main__":
    #QApplication : 프로그램을 실행시켜주는 클래스
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('marc_icon.png'))

    #WindowClass의 인스턴스 생성
    myWindow = DolfinExtractorWindow()

    #프로그램 화면을 보여주는 코드
    myWindow.show()

    #프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()
