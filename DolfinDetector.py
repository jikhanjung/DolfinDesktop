import imagesize
import os
import sys
import glob
from pathlib import Path
import csv
from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime
import time

import argparse
import torch
from utils.general import strip_optimizer
import Yolo5Detector2

from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from DolfinRecord import DolfinRecord, fieldnames

PROGRAM_NAME = "DolfinDetector"
PROGRAM_VERSION = "0.0.1"

#UI파일 연결
#단, UI파일은 Python 코드 파일과 같은 디렉토리에 위치해야한다.
form_class = uic.loadUiType("DolfinDetector.ui")[0]

#화면을 띄우는데 사용되는 Class 선언
class DolfinDetectorWindow(QMainWindow, form_class) :
    def __init__(self) :
        super().__init__()
        self.setupUi(self)
        self.btnOpenFolder.clicked.connect(self.btnOpenFolderFunction)
        self.btnWeights.clicked.connect(self.btnWeightsFunction)
        #self.btnDetectSingle.clicked.connect(self.btnDetectSingleFunction)
        self.btnDetectAll.clicked.connect(self.btnDetectAllFunction)
        #self.btnSaveFins.clicked.connect(self.btnSaveFinsFunction)
        self.btnSaveAllFins.clicked.connect(self.btnSaveAllFinsFunction)
        self.btnSaveData.clicked.connect(self.btnSaveDataFunction)
        #size = self.label.size()
        #print(size.width())
        self.image_path_list = []
        self.orig_pixmap_list = []
        self.processed_pixmap_list = []
        self.all_image_fin_list = []
        self.is_detected_list = []
        self.current_image_index = -1
        self.current_fin_index0 = -1
        self.current_fin_record = None
        self.pixmap1 = None
        self.working_folder = ''
        self.mainview_width = -1
        self.mainview_height = -1
        self.wh_ratio = 0.6656
        #$self.lstDetection.clicked.connect(self.selectRegion)
        self.lstDetectionList.currentItemChanged.connect(self.detectionListChanged)
        self.lstFileList.currentItemChanged.connect(self.fileListChanged)
        self.fit_to_width = False
        #self.progressBar1.hide()
        self.btnDetectSingle.hide()
        self.btnSaveFins.hide()
        self.open_folder_progress = -1
        self.open_folder_maxval = -1
        self.edtImageSize.setText('1280')
        self.edtWeights.setText('dolfin_1280_s_100.pt')
        self.detection_done = False
        self.show_bbox = True
        self.temp_bbox = None
        self.zoom_ratio = 2
        self.bbox_color = { 'x1': QColor(255,0,0), 'x2': QColor(255,0,0), 'y1': QColor(255,0,0), 'y2': QColor(255,0,0) }

    def refresh_finview(self):
        image_index = self.current_image_index
        fin_index0 = self.current_fin_index0
        fin_record = self.current_fin_record

        self.lblFinView.clear()

        pixmap = self.get_cropped_fin_image( image_index, fin_index0, self.show_bbox, self.lblFinView )
        pixmap2 = self.get_fit_pixmap_to_view( pixmap, self.lblFinView )
            
        #self.zoom_factor = int( ( float(final_pixmap.width()) / float(cropped_pixmap.width()) ) * 10 )
        #self.sldZoom.setValue( self.zoom_factor )
        #print("zoom:", self.zoom_factor)
        self.lblFinView.setPixmap(pixmap2)
        return

    def get_cropped_fin_image(self, image_index, fin_index0, draw_bbox = False, widget = None, temp_bbox = {} ):
        start = time.perf_counter()
        #print("get cropped fin image for image", image_index, "fin", fin_index0 )
        #print( self.orig_pixmap_list[image_index] )

        orig_pixmap = self.orig_pixmap_list[image_index]
        orig_width = orig_pixmap.size().width()
        orig_height = orig_pixmap.size().height()
        draw_fin_box = False
        finbbox = {}
        finview = {}

        if( fin_index0 >= 0 ):
            fin_record = self.all_image_fin_list[image_index][fin_index0]
            cls, center_x, center_y, fin_width, fin_height, conf = fin_record.get_detection_info()

            finbbox['width'] = int( fin_width * orig_width )
            finbbox['height'] = int( fin_height * orig_height )
            finbbox['x1'] = int( center_x * orig_width - ( finbbox['width'] / 2 ) )
            finbbox['y1'] = int( center_y * orig_height - ( finbbox['height']  / 2 ) )
            finbbox['x2'] = finbbox['x1'] + finbbox['width']
            finbbox['y2'] = finbbox['y1'] + finbbox['height']

            if widget == None:
                finview['width'] = int( finbbox['width'] * 1.5 )
                finview['height'] = int( finbbox['height'] * 1.5 )
                finview['x1'] = max( int( center_x * orig_width  - ( finview['width']  / 2 ) ), 0 )
                finview['y1'] = max( int( center_y * orig_height - ( finview['height'] / 2 ) ), 0 )
                finview['x2'] = finview['x1'] + finview['width']
                finview['y2'] = finview['y1'] + finview['height']
            else:
                widget_width = widget.size().width()
                widget_height = widget.size().height()
                widget_wh_ratio = widget_width / widget_height
                rect_wh_ratio = finbbox['width'] / finbbox['height']
                if( widget_wh_ratio < rect_wh_ratio ):
                    # fit to widget width
                    finview['width']  = int( finbbox['width'] * 1.5 )
                    finview['height'] = int( finbbox['width'] * 1.5 / widget_wh_ratio )
                else:
                    # fit to widget height
                    finview['height'] = int( finbbox['height'] * 1.5 )
                    finview['width']  = int( finbbox['height'] * 1.5 * widget_wh_ratio )
                finview['x1'] = max( int( center_x * orig_width  - ( finview['width']  / 2 ) ), 0 )
                finview['y1'] = max( int( center_y * orig_height - ( finview['height'] / 2 ) ), 0 )
                finview['x2'] = finview['x1'] + finview['width']
                finview['y2'] = finview['y1'] + finview['height']
                if( finview['x2'] > orig_width ):
                    finview['x1'] = finview['x1'] - ( finview['x2'] - orig_width )
                    finview['x2'] = orig_width
                if( finview['y2'] > orig_height ):
                    finview['y1'] = finview['y1'] - ( finview['y2'] - orig_height )
                    finview['y2'] = orig_height
        else:
            finview['x1'] = finview['y1'] = 0
            finview['x2'] = finview['width'] = orig_width
            finview['y2'] = finview['height'] = orig_height

        self.current_finbbox_coords = finbbox
        self.current_finview_coords = finview
        #print("image_index", image_index, "fin_index0", fin_index0 )
        #print("finbbox", self.current_finbbox_coords)
        #print("finview", self.current_finview_coords)

        local_bbox = {}
        for k in finbbox.keys():
            local_bbox[k] = finbbox[k]
        if( self.temp_bbox != None ):
            for k in self.temp_bbox.keys():
                local_bbox[k] = self.temp_bbox[k]
        

        cropped_pixmap = orig_pixmap.copy( finview['x1'], finview['y1'], finview['width'], finview['height'] )
        if( draw_bbox and 'x1' in local_bbox.keys() ):
            qpainter = QPainter( cropped_pixmap )
            #qpainter.setPen(QColor(255, 0, 0))
            #qpainter.drawRect( rect_x - view_x, rect_y - view_y, rect_width, rect_height )
            actual_box = { 'x1': local_bbox['x1'] - finview['x1'],
                           'y1': local_bbox['y1'] - finview['y1'],
                           'x2': local_bbox['x2'] - finview['x1'],
                           'y2': local_bbox['y2'] - finview['y1'],
                         }
            #print("local_bbox", local_bbox )
            pen = {}
            pen_width = 2
            if( self.zoom_ratio < 1 ):
                pen_width = int( 5.0 / self.zoom_ratio )
            #print( "zoom ratio:", self.zoom_ratio, "pen width:", pen_width)
            for k in ['x1', 'x2', 'y1', 'y2' ]:
                pen[k] = QPen( self.bbox_color[k] )
                pen[k].setWidth( pen_width )
            qpainter.setPen(pen['y1'])
            qpainter.drawLine( actual_box['x1'], actual_box['y1'], actual_box['x2'], actual_box['y1'] )
            qpainter.setPen(pen['x2'])
            qpainter.drawLine( actual_box['x2'], actual_box['y1'], actual_box['x2'], actual_box['y2'] )
            qpainter.setPen(pen['x1'])
            qpainter.drawLine( actual_box['x1'], actual_box['y1'], actual_box['x1'], actual_box['y2'] )
            qpainter.setPen(pen['y2'])
            qpainter.drawLine( actual_box['x1'], actual_box['y2'], actual_box['x2'], actual_box['y2'] )

            qpainter.end()

        end = time.perf_counter()
        #print("elapsed time:", end - start )

        return cropped_pixmap

    def btnSaveAllFinsFunction(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)

        result_dir = str( Path( self.working_folder ).joinpath( "result" ) )
        for img_idx in range( len( self.image_path_list ) ):
            if( self.orig_pixmap_list[img_idx] == None ):
                img_path = self.working_folder.joinpath( self.image_path_list[img_idx] )
                self.orig_pixmap_list[img_idx] = QPixmap(str(img_path))
            filename_stem = str( Path(result_dir).joinpath( Path(self.image_path_list[img_idx]).stem ) )
            for fin_idx in range( len( self.all_image_fin_list[img_idx] ) ):
                fin_pixmap = self.get_cropped_fin_image( img_idx, fin_idx )
                fin_img = fin_pixmap.toImage()
                fin_idx_str = "00" + str(fin_idx+1)
                filename = filename_stem + "_" + fin_idx_str[-2:] + ".JPG"
                fin_img.save( filename )

        QApplication.restoreOverrideCursor()

        '''
            latitude, longitude, map_datum = self.get_gps_data(  )
            #print(gps_data)
            #return
            
            image_date, image_time = self.get_datetime_exif( str(self.image_path_list[image_idx]) )
            if image_date == '':
                str1 = time.ctime(os.path.getmtime(str(self.image_path_list[image_idx])))
                datetime_object = datetime.strptime(str1, '%a %b %d %H:%M:%S %Y')
                image_date = datetime_object.strftime("%Y-%m-%d")
                image_time = datetime_object.strftime("%H-%M-%S")

            image_date = "-".join( image_date.split(":") )
            image_datetime = image_date + " " + image_time
        '''
    def get_image_info(self, filename):
        image_info = {'date':'','time':'','latitude':'','longitude':'','map_datum':''}
        i = Image.open(filename)
        ret = {}
        #print(filename)
        try:
            info = i._getexif()
            for tag, value in info.items():
                decoded=TAGS.get(tag, tag)
                ret[decoded]= value
                #print("exif:", decoded, value)
            try:
                if ret['GPSInfo'] != None:
                    gps_info = ret['GPSInfo']
                    #print("gps info:", gps_info)
                degree_symbol = "°"
                minute_symbol = "'"
                longitude = str(int(gps_info[4][0])) + degree_symbol + str(gps_info[4][1]) + minute_symbol + gps_info[3]
                latitude = str(int(gps_info[2][0])) + degree_symbol + str(gps_info[2][1]) + minute_symbol + gps_info[1]
                map_datum = gps_info[18]
                image_info['latitude'] = latitude
                image_info['longitude'] = longitude
                image_info['map_datum'] = map_datum

            except KeyError:
                print( "GPS Data Don't Exist for", Path(filename).name)

            try:
                if ret['DateTimeOriginal'] != None:
                    exifTimestamp=ret['DateTimeOriginal']
                    #print("original:", exifTimestamp)
                    image_info['date'], image_info['time'] = exifTimestamp.split()
            except KeyError:
                print( "DateTimeOriginal Don't Exist")
            try:
                if ret['DateTimeDigitized'] != None:
                    exifTimestamp= ret['DateTimeDigitized']
                    image_info['date'], image_info['time'] = exifTimestamp.split()
            except KeyError:
                print( "DateTimeDigitized Don't Exist")
            try:
                if ret['DateTime'] != None:
                    exifTimestamp= ret['DateTime']
                    image_info['date'], image_info['time'] = exifTimestamp.split()
            except KeyError:
                print( "DateTime Don't Exist")

        except Exception as e:
            print(e)
        
        if image_info['date'] == '':
            str1 = time.ctime(os.path.getmtime(filename))
            datetime_object = datetime.strptime(str1, '%a %b %d %H:%M:%S %Y')
            image_info['date'] = datetime_object.strftime("%Y-%m-%d")
            image_info['time'] = datetime_object.strftime("%H:%M:%S")
        else:
            image_info['date'] = "-".join( image_info['date'].split(":") )
        image_info['datetime'] = image_info['date'] + ' ' + image_info['time']
        return image_info

    def btnSaveDataFunction(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        folder_name = self.working_folder.name
        save_path = str( self.working_folder.joinpath( folder_name + ".csv" ))

        with open(save_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for img_idx in range( len( self.image_path_list ) ):
                
                fin_record.image_width, fin_record.image_height = imagesize.get(str(self.image_path_list[img_idx]))

                for fin_record in self.all_image_fin_list[img_idx]:
                    writer.writerow({'folder_name':fin_record.folder_name,'image_name': fin_record.image_name, 'image_width': fin_record.image_width,
                                     'image_height': fin_record.image_height,'class_id': int(fin_record.class_id), 
                                     'fin_index': fin_record.fin_index, 'center_x': fin_record.center_x, 'center_y': fin_record.center_y, 
                                     'width': fin_record.width, 'height': fin_record.height, 'confidence': fin_record.confidence,
                                     'is_fin': fin_record.is_fin, 'image_datetime': fin_record.image_datetime, 
                                     'location': fin_record.location, 'latitude': fin_record.latitude, 'longitude': fin_record.longitude,
                                     'map_datum': fin_record.map_datum, 'dolfin_id': fin_record.dolfin_id, 'observed_by': fin_record.observed_by, 
                                     'created_by': fin_record.created_by, 'created_on': fin_record.created_on,
                                     'modified_by': fin_record.modified_by, 'modified_on': fin_record.modified_on})
        QApplication.restoreOverrideCursor()
        return

    def fileListChanged(self):

        image_index = self.lstFileList.currentRow()
        #print( "image index:", image_index)
        if image_index < 0:
            return
        self.current_image_index = image_index
        QApplication.setOverrideCursor(Qt.WaitCursor)

        if( self.orig_pixmap_list[image_index] == None ):
            img_path = self.working_folder.joinpath( self.image_path_list[image_index] )
            self.orig_pixmap_list[image_index] = QPixmap(str(img_path))
        pixmap = self.orig_pixmap_list[image_index]
        
        self.lstDetectionList.clear()
        self.lblFinView.clear()
        self.setMainView(image_index)
        
        for fin_record in self.all_image_fin_list[image_index]:
            i = fin_record.fin_index
            x = fin_record.center_x
            y = fin_record.center_y
            self.lstDetectionList.addItem( "#" + str(i) + " (" + str(x) + "," + str(y)+ ")" )
        #print("file list changed. original pixmap for image #" + str( image_index ) + " is", self.orig_pixmap_list[image_index] )
        QApplication.restoreOverrideCursor()

    def detectionListChanged(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        #print(self.lstDetectionList.currentItem().text())
        fin_index0 = self.current_fin_index0 = self.lstDetectionList.currentRow()
        #print( "detection list changed", self.current_image_index, self.current_fin_index0 )

        self.refresh_finview()
        QApplication.restoreOverrideCursor()

    def getOpt(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--weights', nargs='+', type=str, default='dolfin_1280_s_100.pt', help='model.pt path(s)')
        parser.add_argument('--source', type=str, default='inference/images', help='source')  # file/folder, 0 for webcam
        parser.add_argument('--output', type=str, default='inference/output', help='output folder')  # output folder
        parser.add_argument('--img-size', type=int, default=640, help='inference size (pixels)')
        parser.add_argument('--conf-thres', type=float, default=0.4, help='object confidence threshold')
        parser.add_argument('--iou-thres', type=float, default=0.5, help='IOU threshold for NMS')
        parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
        parser.add_argument('--view-img', action='store_true', default=False, help='display results')
        parser.add_argument('--save-txt', action='store_true', default=True, help='save results to *.txt')
        parser.add_argument('--classes', nargs='+', type=int, help='filter by class: --class 0, or --class 0 2 3')
        parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
        parser.add_argument('--augment', action='store_true', help='augmented inference')
        parser.add_argument('--update', action='store_true', default=False, help='update all models')
        opt = parser.parse_args()
        opt.weights = self.edtWeights.text()
        opt.img_size = int(self.edtImageSize.text())
        return opt


    def btnDetectSingleFunction(self) :

        opt = self.getOpt()
        idx = self.current_image_index
        filename = self.image_path_list[idx]

        opt.source = filename
        single_image_detection_list = []

        with torch.no_grad():
            #if opt.update:  # update all models (to fix SourceChangeWarning)
            #    for opt.weights in ['yolov5s.pt', 'yolov5m.pt', 'yolov5l.pt', 'yolov5x.pt']:
            #        all_result = Yolo5Detector2.detect(opt)
            #        strip_optimizer(opt.weights)
            #else:
            all_result = Yolo5Detector2.detect(opt)
        
        self.all_image_fin_list[idx] = all_result[0]
        self.all_image_fin_list[idx].sort()
        self.setDetectionResult(idx)

        return

    def btnDetectAllFunction(self) :
        QApplication.setOverrideCursor(Qt.WaitCursor)
        opt = self.getOpt()

        opt.source = str(self.working_folder)
        opt.output = str(self.working_folder.joinpath('result'))
        self.all_image_fin_list = []
        folder_name = self.working_folder.name
        #print(type(folder_name),folder_name)

        if "_" in folder_name:
            obs_list = folder_name.split("_",2)
            #print(obs_list)
            if len(obs_list)==2:
                obs_date, obs_location = obs_list
            else:
                obs_date, obs_location, obs_by = obs_list
        else:
            obs_date = folder_name
            obs_location, obs_by = '', ''


        #if "_" in self.working_folder.name:
        #    obs_date, obs_location, obs_by = self.working_folder.name.split("_",maxsplit=2)
        #else:
        #    obs_date, obs_location, obs_by = '', '', ''
        #print(obs_date, obs_location, obs_by)
        #return

        with torch.no_grad():
            if opt.update:  # update all models (to fix SourceChangeWarning)
                for opt.weights in ['yolov5s.pt', 'yolov5m.pt', 'yolov5l.pt', 'yolov5x.pt']:
                    all_result = Yolo5Detector2.detect(opt)
                    strip_optimizer(opt.weights)
            else:
                all_result = Yolo5Detector2.detect(opt)
        #print("detection done. all result:" ,all_result )
        for result in all_result:
            result.sort()

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        #print(now)

        i = 0
        for image_idx in range(len(all_result)):
            single_image_result = all_result[image_idx]

            image_info = self.get_image_info( str(self.image_path_list[image_idx]) )

            self.all_image_fin_list.append([])

            fin_count = len(single_image_result)
            if fin_count == 0:
                single_image_result = [ [ 0, 0, 0, 1, 1, -1 ] ]

            for fin_index in range(len(single_image_result)):
                #print( single_image_result[fin_index], image_info )
                cls, x, y, w, h, conf = single_image_result[fin_index]
                is_fin = True
                if conf < 0:
                    is_fin = False
                fin_info = { 'folder_name': self.working_folder.name, 'image_name': Path( self.image_path_list[image_idx] ).name,
                            'fin_index': fin_index+1, 'class_id': cls, 'center_x':x, 'center_y':y, 'width':w, 'height':h, 'confidence':conf, 
                            'is_fin': is_fin, 'image_datetime': image_info['datetime'], 'location': obs_location, 
                            'latitude':image_info['latitude'], 'longitude': image_info['longitude'], 'map_datum': image_info['map_datum'], 'dolfin_id':'', 
                            'observed_by': obs_by, 'created_by':'DolfinDetector_v0.0.1', 'created_on': now,
                            'modified_by': '', 'modified_on':'', 'comment': ''
                            }
                fin_record = DolfinRecord( fin_info )
                self.all_image_fin_list[image_idx].append( fin_record )
                #print( fin_record )
        #self.all_image_detection_list = all_result
        self.lstDetectionList.clear()
        self.lblMainView.clear()
        self.lblFinView.clear()
        self.detection_done = True
        self.lstFileList.clearSelection()

        QApplication.restoreOverrideCursor()
        return

    def btnOpenFolderFunction(self):
        dir = QFileDialog.getExistingDirectory(self, 'Open directory', './')

        self.image_path_list = []
        self.detection_list = []
        self.pixmap_list = []
        self.orig_pixmap_list = []
        self.lstFileList.clear()

        img_formats = ['.bmp', '.jpg', '.jpeg', '.png', '.tif', '.tiff', '.dng']

        p = str(Path(dir))
        p = os.path.abspath(p)  # absolute path
        self.working_folder = Path(p)
        
        if os.path.isdir(p):
            self.lineEdit.setText(p)
            files = sorted(glob.glob(os.path.join(p, '*.*')))  # dir
            images = [x for x in files if os.path.splitext(x)[-1].lower() in img_formats]

            self.open_folder_progress = 0
            self.open_folder_maxval = len(images)
            for img in images:
                #print(img)
                self.image_path_list.append( img )
                #print(Path(img).name)
                self.lstFileList.addItem( Path(img).name )
                self.orig_pixmap_list.append( None )
                self.is_detected_list.append( False )
                self.processed_pixmap_list.append( None )
                self.all_image_fin_list.append([])
                self.open_folder_progress += 1
                #self.processed_pixmap_list.append( l_pixmap.copy() )
        return

    def btnWeightsFunction(self):
        weights_filename, filter = QFileDialog.getOpenFileName(self, 'Select Weights File', './', '*.pt')
        #print( weights_filename )
        #return

        p = str(Path(weights_filename))
        p = os.path.abspath(p)  # absolute path
        
        if os.path.exists(p):
            self.edtWeights.setText(p)
        return

    def get_fit_pixmap_to_view( self, pixmap, view, zoom_ratio = -1 ):

        view_width = view.size().width()
        view_height = view.size().height()
        view_wh_ratio = view_width / view_height
        pixmap_wh_ratio = pixmap.width() / pixmap.height()

        if( view_wh_ratio < pixmap_wh_ratio ):
            #self.zoom_ratio = int(view_width / pixmap.width() )
            if( zoom_ratio > 0 ):
                final_pixmap = pixmap.scaledToWidth( int( pixmap.width() * zoom_ratio * 0.1 ) )
            else:
                final_pixmap = pixmap.scaledToWidth(view_width)
        else: 
            if( zoom_ratio > 0 ):
                final_pixmap = pixmap.scaledToWidth( int( pixmap.height() * zoom_ratio * 0.1 ) )
            #self.zoom_ratio = int( view_height / pixmap.height() )
            else:
                final_pixmap = pixmap.scaledToHeight(view_height)
        #print( "zoom factor:", self.zoom_ratio)
        
        return final_pixmap

    def setMainView(self, image_index ):
        if( self.processed_pixmap_list[image_index] == None):
            pixmap = self.orig_pixmap_list[image_index]
            
        l_pixmap = self.get_fit_pixmap_to_view( pixmap, self.lblMainView )
        l_painter = QPainter( l_pixmap )
        l_painter.setPen(QColor(255, 0,0))
        l_width = l_pixmap.width()
        l_height = l_pixmap.height()

        for fin_record in self.all_image_fin_list[image_index]:
            cls, x, y, w, h, conf = fin_record.get_detection_info()
            fin_index = fin_record.fin_index 
            #print( cls, x, y, w, h )
            w = float(w)
            h = float(h)

            center_x = round( float(x) * l_width )
            center_y = round( float(y) * l_height )
            w = region_width = round( w * l_width )
            h = region_height = round( h * l_height )
            x = center_x - int( region_width / 2 ) 
            y = center_y - int( region_height / 2 ) 

            l_text = "#"+str( fin_index )
            text_height = 15
            l_painter.drawRect( x, y, w, h )
            l_painter.drawText( x, y-2, l_text)

        l_painter.end()
        self.lblMainView.setPixmap(l_pixmap)

        return
if __name__ == "__main__" :
    #QApplication : 프로그램을 실행시켜주는 클래스
    app = QApplication(sys.argv) 

    #WindowClass의 인스턴스 생성
    myWindow = DolfinDetectorWindow() 

    #프로그램 화면을 보여주는 코드
    myWindow.show()

    #프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()