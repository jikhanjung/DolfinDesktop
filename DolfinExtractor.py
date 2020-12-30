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
from PyQt5.QtGui import QIcon, QImageReader, QPixmap, QPainter
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
        finid_sum = 0
        row_sum = 0
        image_sum = 0
        for item in dir_list:
            #print(item)
            full_path = self.working_folder.joinpath(item)
            if os.path.isdir(str(full_path)):
                image_name_list = []
                csv_path = full_path.joinpath( full_path.name + ".csv" )
                #icondb_path = full_path.joinpath( full_path.name + ".icondb" )
                #finicon_hash = load_and_unpickle_image_hash( icondb_path )
                print( csv_path )

                if csv_path.exists():
                    self.path_list.append(full_path)
                    with open(str(csv_path), newline='',encoding='utf-8') as csvfile:
                        reader = csv.DictReader(csvfile)
                        row_count = 0
                        finid_count = 0
                        for row in reader:
                            row_count += 1
                            row_sum += 1
                            image_name = row['image_name']
                            if image_name not in image_name_list:
                                image_name_list.append(image_name)
                            fin_record  = DolfinRecord( row )
                            if fin_record.dolfin_id != '':
                                finid_count += 1
                                finid_sum += 1

                    image_count = len(image_name_list)
                    image_sum += image_count
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

        table_row_count = self.tblSubfolders.rowCount()
        item0 = QTableWidgetItem( "" )
        item1 = QTableWidgetItem( "Total" )
        item1.setTextAlignment(int(Qt.AlignCenter|Qt.AlignVCenter))
        item2 = QTableWidgetItem(str(finid_sum))
        item2.setTextAlignment(int(Qt.AlignRight|Qt.AlignVCenter))
        item3 = QTableWidgetItem(str(row_sum))
        item3.setTextAlignment(int(Qt.AlignRight|Qt.AlignVCenter))
        item4 = QTableWidgetItem(str(image_sum))
        item4.setTextAlignment(int(Qt.AlignRight|Qt.AlignVCenter))
        self.tblSubfolders.insertRow(table_row_count)
        #self.checkbox_list.append(checkbox)
        self.tblSubfolders.setItem(current_row, 0, item0)
        self.tblSubfolders.setItem(current_row, 1, item1)
        self.tblSubfolders.setItem(current_row, 2, item2)
        self.tblSubfolders.setItem(current_row, 3, item3)
        self.tblSubfolders.setItem(current_row, 4, item4)


        QApplication.restoreOverrideCursor()

    def export_javascript(self):
        """
        docstring
        """
        QApplication.setOverrideCursor(Qt.WaitCursor)
        occurrence_hash = {}
        #lat_min, lon_min, lat_max, lon_max = 999,999,0,0
        path_index = 0
        for current_path in self.path_list:
            csv_path = current_path.joinpath( current_path.name + ".csv" )
            #print( csv_path )

            #icondb_path = p.joinpath( p.name + ".icondb" )
            #finicon_hash = load_and_unpickle_image_hash( icondb_path )

            if self.checkbox_list[path_index].isChecked() and csv_path.exists():
                print( csv_path )

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
            path_index += 1


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
        path_index = 0

        for current_path in self.path_list:
            csv_path = current_path.joinpath( current_path.name + ".csv" )
            icondb_path = current_path.joinpath( current_path.name + ".icondb" )
            finicon_hash = self.load_and_unpickle_image_hash( icondb_path )
            #print( csv_path )

            #if csv_path.exists():
            if self.checkbox_list[path_index].isChecked() and csv_path.exists():
                print( csv_path )

                with open(str(csv_path), newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)

                    prev_image_name = ''

                    for row in reader:
                        fin_record  = DolfinRecord( row )
                        if fin_record.dolfin_id == '':
                            continue

                        image_name = fin_record.image_name
                        image_path = current_path.joinpath(image_name)

                        if image_name != prev_image_name:
                            pixmap = None
                            prev_image_name = image_name
                            #i += 1
                            #label_text = "Processing {} of {} image files...".format(i, len(images))
                            #self.progress_dialog.pb_progress.setValue(int((i/float(len(images)))*100))
                            #self.progress_dialog.lbl_text.setText(label_text)
                            #self.progress_dialog.update()
                            #QApplication.processEvents()


                        if pixmap is None:
                            pixmap = QPixmap(str(image_path))
                        cropped_pixmap = self.get_cropped_fin_image(pixmap, fin_record, True)
                        scaled_pixmap = cropped_pixmap.scaledToWidth(224)
                        
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
                        #icon_pixmap = QPixmap(finicon_hash[fin_record.get_finname()])
                        #print(finid_filepath)
                        short_filepath = Path(finid).joinpath(finid_filename)

                        fin_img = scaled_pixmap.toImage()
                        fin_img.save(str(finid_filepath))
                        finid_hash[finid].append(short_filepath)
            path_index += 1
 
        csv_path = "./finid_images/dolfinid.csv"
        with open(str(csv_path), 'w', newline='', encoding='utf-8') as csvfile:
            for k in finid_hash.keys():
                for filepath in finid_hash[k]:
                    csvfile.write(",".join([k, str(filepath.as_posix())]))
                    csvfile.write("\n")
        #csvfile.close()


        QApplication.restoreOverrideCursor()        

    def get_cropped_fin_image(self, pixmap, fin_record, square=True):

        orig_pixmap = pixmap #self.orig_pixmap_list[image_index]
        orig_width = orig_pixmap.size().width()
        orig_height = orig_pixmap.size().height()
        finbbox = {}
        finview = {}

        if fin_record.confidence > 0:
            cls, center_x, center_y, fin_width, fin_height, conf = fin_record.get_detection_info()

            finbbox['width'] = int(fin_width * orig_width)
            finbbox['height'] = int(fin_height * orig_height)
            #print("fin bbox", finbbox)
            if square:
                finbbox['width'] = max(int(fin_width*orig_width), int(fin_height*orig_height))
                finbbox['height'] = finbbox['width']
            #print("fin bbox", finbbox)
            finbbox['x1'] = int(center_x * orig_width - (finbbox['width'] / 2))
            finbbox['y1'] = int(center_y * orig_height - (finbbox['height']  / 2))
            #print("fin bbox", finbbox)
            finbbox['x2'] = finbbox['x1'] + finbbox['width']
            finbbox['y2'] = finbbox['y1'] + finbbox['height']
            #print("finbbox", finbbox)
            #print("fin bbox", finbbox)

            finview['width'] = finbbox['width']
            finview['height'] = finbbox['height']
            finview['x1'] = max(int(center_x * orig_width  - (finview['width']  / 2)), 0)
            finview['y1'] = max(int(center_y * orig_height - (finview['height'] / 2)), 0)
            finview['x2'] = finview['x1'] + finview['width']
            finview['y2'] = finview['y1'] + finview['height']

        cropped_pixmap = orig_pixmap.copy(finview['x1'], finview['y1'], finview['width'], finview['height'])
        p_width, p_height = cropped_pixmap.width(), cropped_pixmap.height()

        if square and p_width != p_height:
            p_size = max(p_width, p_height)
            empty_pixmap = QPixmap(p_size, p_size)
            empty_pixmap.fill(Qt.gray)
            l_painter = QPainter(empty_pixmap)
            l_painter.drawPixmap(cropped_pixmap.rect(), cropped_pixmap)
            cropped_pixmap = empty_pixmap

        return cropped_pixmap


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
