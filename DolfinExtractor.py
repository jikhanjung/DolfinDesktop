import webbrowser
from PIL import Image
import pickle
import json  

import imagesize
import os
import sys
import glob
from pathlib import Path
import csv
from datetime import datetime
import time
import math
from operator import itemgetter, attrgetter
import webbrowser
from chardet.universaldetector import UniversalDetector

from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from DolfinRecord import DolfinRecord, fieldnames

form_class = uic.loadUiType("DolfinExtractor.ui")[0]

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
        self.btnExportFinImages.setEnabled(False)
        self.path_list = []
        self.checkbox_list = []
        self.working_folder = Path("./")

        self.set_table_header()

    def export_fin_images(self):
        pass


    def show_in_map(self):
        url = "file://" + str(Path("./DolfinExplorerKakao.html").resolve())
        print(url)
        webbrowser.open(url,new=2)


    def set_table_header(self):
        self.tblSubfolders.setColumnCount(4)
        header = self.tblSubfolders.horizontalHeader()
        self.tblSubfolders.setColumnWidth(0, 10)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.tblSubfolders.setColumnWidth(2, 100)
        self.tblSubfolders.setColumnWidth(3, 100)
        header_item0 = QTableWidgetItem("")
        header_item1 = QTableWidgetItem("Folder Name")
        header_item2 = QTableWidgetItem("DolfinID")
        header_item3 = QTableWidgetItem("Total")
        self.tblSubfolders.setHorizontalHeaderItem(0,header_item0)
        self.tblSubfolders.setHorizontalHeaderItem(1,header_item1)
        self.tblSubfolders.setHorizontalHeaderItem(2,header_item2)
        self.tblSubfolders.setHorizontalHeaderItem(3,header_item3)
        self.tblSubfolders.verticalHeader().setVisible(False)


    def clear_table(self):
        self.tblSubfolders.clear()
        self.path_list = []
        self.tblSubfolders.setRowCount(0)
        self.set_table_header()

    def open_folder_function(self):
        parent_folder = str(self.working_folder.parent)
        open_dir = QFileDialog.getExistingDirectory(self, 'Open directory', parent_folder)

        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.edtFolder.setText(open_dir)
        self.working_folder = Path(open_dir)

        dir_list = [f for f in os.listdir(str(self.working_folder))]

        current_row = 0
        for item in dir_list:
            #print(item)
            full_path = self.working_folder.joinpath(item)
            if os.path.isdir(str(full_path)):
                csv_path = full_path.joinpath( full_path.name + ".csv" )
                icondb_path = full_path.joinpath( full_path.name + ".icondb" )
                #finicon_hash = load_and_unpickle_image_hash( icondb_path )
                #print( csv_path )

                if csv_path.exists():
                    self.path_list.append(full_path)
                    with open(str(csv_path), newline='') as csvfile:
                        reader = csv.DictReader(csvfile)
                        row_count = 0
                        finid_count = 0
                        for row in reader:
                            row_count += 1
                            image_name = row['image_name']
                            fin_record  = DolfinRecord( row )
                            if fin_record.dolfin_id != '':
                                finid_count += 1


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
                    self.tblSubfolders.insertRow(table_row_count)
                    self.checkbox_list.append(checkbox)
                    self.tblSubfolders.setCellWidget ( current_row, 0, cbx_widget)
                    self.tblSubfolders.setItem(current_row, 1, item1)
                    self.tblSubfolders.setItem(current_row, 2, item2)
                    self.tblSubfolders.setItem(current_row, 3, item3)
                    current_row += 1


        QApplication.restoreOverrideCursor()

    def export_javascript(self):
        """
        docstring
        """
        QApplication.setOverrideCursor(Qt.WaitCursor)
        finid_hash = {}
        lat_min, lon_min, lat_max, lon_max = 999,999,0,0
        for p in self.path_list:
            csv_path = p.joinpath( p.name + ".csv" )
            icondb_path = p.joinpath( p.name + ".icondb" )
            #finicon_hash = load_and_unpickle_image_hash( icondb_path )
            print( csv_path )

            if csv_path.exists():

                with open(str(csv_path), newline='') as csvfile:
                    reader = csv.DictReader(csvfile)

                    prev_image_name = ''
                    prev_index = -1
                    pixmap = None

                    for row in reader:
                        image_index = -1
                        image_path = csv_path.parent.joinpath(row['image_name'])

                        image_name = row['image_name']
                        #filepath_stem = ''
                        #pixmap = None

                        fin_record  = DolfinRecord( row )

                        if fin_record.dolfin_id == '':
                            continue
                        
                        if prev_image_name != image_name:
                            current_image = Image.open( str(image_path) )

                        finview_ratio = 1.5
                        fin_coord = fin_record.get_x1y1x2y2()
                        fin_width = fin_coord['x2'] - fin_coord['x1'] + 1
                        fin_height = fin_coord['y2'] - fin_coord['y1'] + 1
                        fin_wh = max( fin_width, fin_height )
                        fin_center_x, fin_center_y = fin_record.center_x * fin_record.image_width, fin_record.center_y * fin_record.image_height
                        x1, y1, x2, y2 = fin_center_x - int( finview_ratio * fin_wh / 2 ), fin_center_y - int( finview_ratio * fin_wh / 2 ), fin_center_x + int( finview_ratio * fin_wh / 2 ), fin_center_y + int( finview_ratio * fin_wh / 2 )
                        #cropped_image = current_image.crop( ( x1, y1, x2, y2 ) )
                        #resized_image = cropped_image.resize( ( 200, 200 ) )

                        date_time_obj = datetime.strptime(fin_record.image_datetime, '%Y-%m-%d %H:%M:%S')
                        yyyymmdd = date_time_obj.strftime( '%Y%m%d')


                        #finpath = finbasepath.joinpath( fin_record.dolfin_id )
                        #if not os.path.isdir(str(finpath)):
                        #    print("making path", str(finpath))
                            #os.makedirs(str(finpath))

                        #finfilepath_stem = str( Path(finpath).joinpath( yyyymmdd + '_' + image_path.stem ) )

                        fin_index0 = int(row['fin_index']) - 1
                        fin_idx_str = "00" + row['fin_index']
                        #icon_filepath = Path( finfilepath_stem + "_" + fin_idx_str[-2:] + ".JPG" )
                        #print( icon_filepath)
                        
                        #resized_image.save( str( icon_filepath ) )
                        finid = fin_record.dolfin_id

                        if finid not in finid_hash.keys():
                            finid_hash[finid] = []
                        lat, lon = fin_record.get_decimal_latitude_longitude()
                        if lat > 0:
                            lat_max = max(lat_max, lat)
                            lat_min = min(lat_min, lat)
                            lon_max = max(lon_max, lon)
                            lon_min = min(lon_min, lon)

                        finid_hash[finid].append({'iconname': fin_record.get_finname(), 'datetime': fin_record.image_datetime,
                                                'latitude': lat, 'longitude': lon})


        json_object = "var finid_hash = " + json.dumps(finid_hash, indent = 4) + ";"
        #print( lat_min, lat_max, lon_min, lon_max )
        #print(json_object)

        with open("dolfinid_data.js", 'w', newline='', encoding='utf-8') as jsfile:
            jsfile.write(json_object)
        jsfile.close()
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
