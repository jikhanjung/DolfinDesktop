import os
import sys
import glob
from pathlib import Path
import csv
from datetime import datetime
import time
import math
from operator import itemgetter, attrgetter

#from PIL import Image
#from PIL.ExifTags import TAGS

import argparse

from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from DolfinRecord import DolfinRecord, fieldnames

form_class = uic.loadUiType("DolfinCompare.ui")[0]

GROUND_TRUTH = 0
DETECTION_RESULT = 1

class DolfinCompareWindow(QMainWindow, form_class) :
    def __init__(self) :
        super().__init__()
        self.setupUi(self)
        self.btnMatch.clicked.connect(self.btnMatchFunction)
        self.btnGetmAP.clicked.connect(self.btnGetmAPFunction)
        self.btnOpenFolder.clicked.connect(self.btnOpenFolderFunction)
        self.btnOpenGroundTruth.clicked.connect(self.btnOpenGroundTruthFunction)
        self.btnOpenDetectionResult.clicked.connect(self.btnOpenDetectionResultFunction)
        self.lstGroundTruth.currentItemChanged.connect(self.lstGroundTruthChanged)
        self.lstDetectionResult.currentItemChanged.connect(self.lstDetectionResultChanged)

        self.respond_to_list_selection_change = True
        self.image_path_list = []
        self.match_list = []
        self.all_image_fin_list = [[],[]]
        self.csv_path = [None, None]
        self.listwidget_list = [ self.lstGroundTruth, self.lstDetectionResult]
        self.labelwidget_list = [ self.lblGroundTruthView, self.lblDetectionResultView]
        self.mainwidget_list = [ self.lblGTMainView, self.lblDRMainView]

        self.show_bbox = True
        self.current_folder = './'
        self.current_image_index = -1
        self.temp_bbox = {}
        self.zoom_ratio = 1
        self.bbox_color = { 'x1': QColor(255,0,0), 'x2': QColor(255,0,0), 'y1': QColor(255,0,0), 'y2': QColor(255,0,0) }
        self.match_list = [ {}, {} ]

    def get_mAP_at_iou( self, record_list, match_list, iou_threshold ):
        detection_list = record_list[DETECTION_RESULT]
        truth_list = record_list[GROUND_TRUTH]

        detection_list = sorted(detection_list, key=attrgetter('confidence'), reverse=True)

        #for rec in detection_list:
        #    print( rec.get_itemname(), rec.confidence )

        # mAP@.5 먼저 구하기
        #print( "mAP@.5")

        stats = {}
        bins = {}
        stats['ground_truth'] = len( truth_list )
        stats['total_detection'] = 0
        stats['true_positive'] = 0
        stats['false_positive'] = 0
        stats['false_negative'] = 0


        for rec2 in detection_list:
            stats['total_detection'] += 1
            rec1, iou = self.match_list[DETECTION_RESULT][rec2.get_itemname()]
            if iou > 0.5 :
                stats['true_positive'] += 1
            else:
                stats['false_positive'] += 1
        stats['total_positive'] = stats['true_positive'] + stats['false_negative']
        stats['false_negative'] = stats['ground_truth'] - stats['true_positive']
        #print( stats )


        stats['true_positive'] = 0
        stats['false_positive'] = 0
        stats['total_detection'] = 0
        prcurve = []
        for rec2 in detection_list:
            stats['total_detection'] += 1
            rec1, iou = match_list[DETECTION_RESULT][rec2.get_itemname()]
            if iou > iou_threshold :
                stats['true_positive'] += 1
            else:
                stats['false_positive'] += 1
            prcurve.append( [ float(stats['true_positive']) / float(stats['total_detection']), float(stats['true_positive'])/float(stats['ground_truth']) ] )
            #print( iou, "Precision:", float(stats['true_positive']) / float(stats['total_detection']), "Recall:", float(stats['true_positive'])/float(stats['ground_truth']) )

        #for pr in prcurve:
        #    print( "1", pr )
        prcurve.reverse()
        #for pr in prcurve:
        #    print( "2", pr )

        prev_precision = 0
        area_list = []
        for i in range(len(prcurve)):
            #print( "21", prcurve[i], prev_precision )
            precision, recall = prcurve[i]
            if precision < prev_precision:
                prcurve[i][0] = prev_precision
            if precision > prev_precision:
                area_list.append( prcurve[i] )

            prev_precision = prcurve[i][0]
            #print( "22", prcurve[i], prev_precision )

        #for pr in prcurve:
        #    print( "3", pr )
        prcurve.reverse()
        #for pr in prcurve:
        #    print( "4", pr )

        area_list.reverse()
        #for pr in area_list:
        #    print( "5", pr)
        prev_recall = 0
        area = 0
        for precision, recall in area_list:
            curr_area = precision * ( recall - prev_recall )

            area += curr_area
            #print( area, curr_area )
            prev_recall = recall
        print( "mAP@:", area)
        return area


    def btnGetmAPFunction(self):
        #print( "mAP@[.5:.95]")

        detection_list = []
        truth_list = []

        # detection result 
        with open(str(self.csv_path[DETECTION_RESULT]), newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                new_fin_record  = DolfinRecord( row )
                if( new_fin_record.is_fin == True ):
                    detection_list.append( new_fin_record )

        with open(str(self.csv_path[GROUND_TRUTH]), newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                new_fin_record  = DolfinRecord( row )
                if( new_fin_record.is_fin == True ):
                    truth_list.append( new_fin_record )

        iou_list = []
        map_at_iou = {}
        for i in range( 10 ):
            iou_list.append( 0.5 + i * 0.05)

        for iou in iou_list:
            map_val = self.get_mAP_at_iou( [ truth_list, detection_list ], self.match_list, iou )
            map_at_iou[iou] = map_val
        print( map_at_iou )
        total_map = 0
        for k in map_at_iou.keys():
            total_map += map_at_iou[k]
        
        final_mapval = total_map / len( map_at_iou.keys() )
        print( "mAP@[.5:.95]:", final_mapval )
        #for rec in detection_list:
        #    print( rec.get_itemname(), rec.confidence )

    def btnMatchFunction(self):
        if( len( self.all_image_fin_list[0] ) == 0 and len( self.all_image_fin_list[1] ) == 0 ):
            return
        image_count = len ( self.all_image_fin_list[0] )
        #match_list = 
        for image_index in range( image_count ):
            for rec1 in self.all_image_fin_list[GROUND_TRUTH][image_index]:
                rec1_name = rec1.get_itemname()
                #print('rec1:', rec1_name)
                rec2, iou = rec1.find_matching_record( self.all_image_fin_list[DETECTION_RESULT][image_index] )
                if rec2 != None:    

                    rec2_name = rec2.get_itemname()
                    #print( 'matching rec2 exist', rec2_name, iou)
                    if rec2_name in self.match_list[DETECTION_RESULT]:
                        prev_rec1_name, prev_iou = self.match_list[DETECTION_RESULT][rec2_name]
                        if iou > prev_iou:
                            self.match_list[GROUND_TRUTH][prev_rec1_name] = [ '', prev_iou ]
                            self.match_list[GROUND_TRUTH][rec1_name] = [ rec2_name, iou ]
                            self.match_list[DETECTION_RESULT][rec2_name] = [ rec1_name, iou ]
                        else:
                            self.match_list[GROUND_TRUTH][rec1_name] = [ '', iou ]
                    else:
                        self.match_list[GROUND_TRUTH][rec1_name] = [ rec2_name, iou ]
                        self.match_list[DETECTION_RESULT][rec2_name] = [ rec1_name, iou ]
                else:
                    #print( 'rec2 none')
                    self.match_list[GROUND_TRUTH][rec1_name] = [ '', 0 ]

        i = 0
        for hash in self.match_list:
            #print(i)
            i+= 1
            for k in hash.keys():
                pass
                #print( k, hash[k])

        # GT <- DR 이 없는 record 를 찾아서 세팅.

        for image_index in range( image_count ):
            for rec2 in self.all_image_fin_list[DETECTION_RESULT][image_index]:
                rec2_name = rec2.get_itemname()
                #print('rec2:', rec2_name)

                if rec2_name not in self.match_list[DETECTION_RESULT]:
                    self.match_list[DETECTION_RESULT][rec2_name] = [ '', 0 ]

        i = 0
        for hash in self.match_list:
            #print(i)
            i+= 1
            for k in hash.keys():
                pass
                #print( k, hash[k])
            #print( match )

        #print( self.match_list )

    def btnOpenFolderFunction(self):
        dir = QFileDialog.getExistingDirectory(self, 'Open directory', './')
        self.edtFolder.setText(dir)
        self.working_folder = Path(dir)

        if os.path.isdir(dir):
            self.image_path_list = []
            self.orig_pixmap_list = []
            self.all_image_fin_list = [[],[]]
            self.lstGroundTruth.clear()
            self.lstDetectionResult.clear()

            img_formats = ['.bmp', '.jpg', '.jpeg', '.png', '.tif', '.tiff', '.dng']

            files = sorted(glob.glob(os.path.join(dir, '*.*')))  # dir
            images = [x for x in files if os.path.splitext(x)[-1].lower() in img_formats]

            #print("images:", images )
            for img in images:
                self.image_path_list.append( self.working_folder.joinpath( img ) )
                self.orig_pixmap_list.append( None )
                for image_fin_list in self.all_image_fin_list:
                    image_fin_list.append([])
                
            self.btnOpenGroundTruthFunction()
            self.btnOpenDetectionResultFunction()

    def load_csvfile_into_listwidget(self, csv_index):
        with open(str(self.csv_path[csv_index]), newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            prev_image_name = ''
            for row in reader:
                new_fin_record  = DolfinRecord( row )

                finlist_item_text = ''
                if new_fin_record.confidence < 0:
                    finlist_item_text = row['image_name']
                #elif new_fin_record.is_fin == False:
                #    continue
                else:
                    finlist_item_text = row['image_name'] + "-" + row['fin_index']
                
                self.listwidget_list[csv_index].addItem( finlist_item_text )
                image_index = -1
                image_path = self.working_folder.joinpath(row['image_name'])
                if image_path in self.image_path_list:
                    image_index = self.image_path_list.index( image_path )

                self.all_image_fin_list[csv_index][image_index].append( new_fin_record )

    def btnOpenGroundTruthFunction(self):
        filename, filetype = QFileDialog.getOpenFileName(self, 'Open ground truth file', str(self.working_folder), "CSV file (*.csv)")
        pathname = Path( filename )        
        if pathname.is_file():
            self.csv_path[GROUND_TRUTH] = pathname
            self.edtGroundTruth.setText(self.csv_path[GROUND_TRUTH].name)
            self.load_csvfile_into_listwidget( GROUND_TRUTH  )
        else:
            self.csv_path[GROUND_TRUTH] = None
            self.edtGroundTruth.setText('')
            self.listwidget_list[GROUND_TRUTH].clear()
            #self.load_csvfile_into_listwidget( GROUND_TRUTH  )
        if( self.csv_path[GROUND_TRUTH] != None and self.csv_path[DETECTION_RESULT] != None):
            self.btnMatchFunction()

    def btnOpenDetectionResultFunction(self):
        filename, filetype = QFileDialog.getOpenFileName(self, 'Open detection result file', str(self.working_folder), "CSV file (*.csv)")
        pathname = Path( filename )        
        if pathname.is_file():
            self.csv_path[DETECTION_RESULT] = pathname
            self.edtDetectionResult.setText(self.csv_path[DETECTION_RESULT].name)
            self.load_csvfile_into_listwidget( DETECTION_RESULT  )
        else:
            self.csv_path[DETECTION_RESULT] = None
            self.edtDetectionResult.setText('')
            self.listwidget_list[DETECTION_RESULT].clear()
        if( self.csv_path[GROUND_TRUTH] != None and self.csv_path[DETECTION_RESULT] != None):
            self.btnMatchFunction()

    def lstGroundTruthChanged(self):
        if self.respond_to_list_selection_change == False:
            self.respond_to_list_selection_change = True
            return

        self.set_imageview_with_listitem( GROUND_TRUTH )

    def lstDetectionResultChanged(self):
        if self.respond_to_list_selection_change == False:
            self.respond_to_list_selection_change = True
            return
        
        self.set_imageview_with_listitem( DETECTION_RESULT )

    def set_imageview_with_listitem( self, panel_index ):
        fin_item = self.listwidget_list[panel_index].currentItem()

        if fin_item == None:
            return
        #print( fin_item )

        fin_text = fin_item.text()
        splitter = "-"
        fin_index0 = -1
        fin_record = None
        if splitter in fin_text:
            # image has fin(s).
            image_name, fin_index = fin_text.split( "-" )
            #print( "fin_text:", fin_text )
            image_path = self.working_folder.joinpath( image_name )
            image_index = self.image_path_list.index( image_path)
            fin_index0 = self.current_fin_index0 = int(fin_index) - 1
            print( "panel_index", panel_index, "image_index", image_index, "image_path", image_path, "fin_index0", fin_index0)
            #print()
            fin_record = self.current_fin_record = self.all_image_fin_list[panel_index][image_index][fin_index0]
        else:
            image_name = fin_text
            image_path = self.working_folder.joinpath( image_name )
            image_index = self.image_path_list.index( image_path)
            fin_index0 = self.current_fin_index0 = 0
            fin_record = self.current_fin_record = self.all_image_fin_list[panel_index][image_index][fin_index0]
            #pixmap = self.get_fit_pixmap_to_view( self.orig_pixmap_list[self.current_image_index], self.lblFinView )
            if( self.orig_pixmap_list[image_index] == None ):
                self.orig_pixmap_list[image_index] = QPixmap(str(image_path))
            w = self.orig_pixmap_list[image_index].size().width()
            h = self.orig_pixmap_list[image_index].size().height()

        if( self.current_image_index != image_index ): # new image
            self.current_image_index = image_index
            if( self.orig_pixmap_list[image_index] == None ):
                self.orig_pixmap_list[image_index] = QPixmap(str(image_path))
            #self.setMainView(image_index)

        self.refresh_finview( panel_index )
        self.setMainView( panel_index, image_index )
        self.respond_to_list_selection_change = True

        recname, iou = self.match_list[panel_index][fin_record.get_itemname()]
        items = self.listwidget_list[1-panel_index].findItems( recname, Qt.MatchExactly )
        if len(items) > 0:
            self.listwidget_list[1-panel_index].setCurrentItem( items[0] )
        else:
        #print( item_list )
            self.labelwidget_list[1-panel_index].clear()
            self.listwidget_list[1-panel_index].clearSelection()
        return

    def setMainView(self, panel_index, image_index ):
        #print( "pixmap 0:", self.orig_pixmap_list[image_index] )
        #if( self.processed_pixmap_list[image_index] == None):
        pixmap = self.orig_pixmap_list[image_index].copy()

        l_pixmap = self.get_fit_pixmap_to_view( pixmap, self.mainwidget_list[panel_index] )
        #print("pixmap 2:", l_pixmap)

        l_painter = QPainter( l_pixmap )
        l_painter.setPen(QColor(255, 0,0))
        pixmap_width = l_pixmap.width()
        pixmap_height = l_pixmap.height()

        for fin_record in self.all_image_fin_list[panel_index][image_index]:
            cls, x, y, w, h, conf = fin_record.get_detection_info()
            if( conf > 0 ):
                fin_index = fin_record.fin_index 
                #print( cls, x, y, w, h )
                w = float(w)
                h = float(h)

                center_x = round( float(x) * pixmap_width )
                center_y = round( float(y) * pixmap_height )
                w = bbox_width = round( w * pixmap_width )
                h = bbox_height = round( h * pixmap_height )
                x = center_x - int( bbox_width / 2 ) 
                y = center_y - int( bbox_height / 2 ) 

                l_text = "#"+str( fin_index )
                text_height = 15
                l_painter.drawRect( x, y, w, h )
                l_painter.drawText( x, y-2, l_text)

        l_painter.end()
        self.mainwidget_list[panel_index].setPixmap(l_pixmap)

    def resizeEvent(self,e):
        self.lstDetectionResultChanged()
        self.lstGroundTruthChanged()
        if( self.current_image_index >= 0):
            for i in range(2):
                self.setMainView( i, self.current_image_index )

    def refresh_finview(self, panel_index ):
        image_index = self.current_image_index
        fin_index0 = self.current_fin_index0
        fin_record = self.current_fin_record

        self.labelwidget_list[panel_index].clear()

        pixmap = self.get_cropped_fin_image( panel_index, image_index, fin_index0, self.show_bbox, self.labelwidget_list[panel_index] )
        pixmap2 = self.get_fit_pixmap_to_view( pixmap, self.labelwidget_list[panel_index] )
            
        zoom_factor = int( ( float(pixmap2.width()) / float(pixmap.width()) ) * 10 )
        #self.sldZoom.setValue( self.zoom_factor )
        #print("zoom:", zoom_factor)
        self.labelwidget_list[panel_index].setPixmap(pixmap2)
        return

    def get_cropped_fin_image(self, panel_index, image_index, fin_index0, draw_bbox = False, widget = None, temp_bbox = {} ):
        start = time.perf_counter()

        orig_pixmap = self.orig_pixmap_list[image_index]
        orig_width = orig_pixmap.size().width()
        orig_height = orig_pixmap.size().height()
        draw_fin_box = False
        finbbox = {}
        finview = {}
        fin_record = None

        if( fin_index0 >= 0 ):
            fin_record = self.all_image_fin_list[panel_index][image_index][fin_index0]

        if( fin_index0 >= 0 and fin_record.confidence > 0 ):
            cls, center_x, center_y, fin_width, fin_height, conf = fin_record.get_detection_info()

            finbbox['width'] = int( fin_width * orig_width )
            finbbox['height'] = int( fin_height * orig_height )
            finbbox['x1'] = int( center_x * orig_width - ( finbbox['width'] / 2 ) )
            finbbox['y1'] = int( center_y * orig_height - ( finbbox['height']  / 2 ) )
            finbbox['x2'] = finbbox['x1'] + finbbox['width']
            finbbox['y2'] = finbbox['y1'] + finbbox['height']
            #print("finbbox", finbbox)

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

if __name__ == "__main__" :
    #QApplication : 프로그램을 실행시켜주는 클래스
    app = QApplication(sys.argv) 

    #WindowClass의 인스턴스 생성
    myWindow = DolfinCompareWindow() 

    #프로그램 화면을 보여주는 코드
    myWindow.show()

    #프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()
