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

from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtGui import *
from PyQt5.QtCore import *

from DolfinRecord import DolfinRecord, fieldnames
#from DolfinNote import DolfinNoteWindow
import pickle

fsock = open('error.log', 'w')
sys.stderr = fsock    

PROGRAM_NAME = "DolfinNote"
PROGRAM_VERSION = "0.1.0"

FV_VIEW = 0
FV_DRAGREADY = 1
FV_DRAG = 2
FV_ADDNEWFIN = 3
FV_NEWFIN_DRAG = 4
FV_NOFINIMAGE = 5
FV_PAN = 6
FV_MODE = [ "FV_VIEW", "FV_DRAGREADY", "FV_DRAG", "FV_ADDNEWFIN", "FV_NEWFIN_DRAG", "FV_NOFINIMAGE", "FV_PAN" ]

BTN_NOT_ASSIGNED = "Not Assigned"
BTN_NO_FIN = "No Fin"
DEFAULT_FINID_BUTTONS = [ BTN_NOT_ASSIGNED, BTN_NO_FIN ]

bbox_threshold = 5
red_color = QColor(255,0,0)
green_color = QColor( 0,255,0)
blue_color = QColor( 0,0,255)
normal_bbox_color = red_color
near_cursor_bbox_color = blue_color

ICON_VIEW = 0
CLOSEUP_VIEW = 1
VIEW_MODE = [ "ICON_VIEW", "CLOSEUP_VIEW" ]

form_class = uic.loadUiType("DolfinNote.ui")[0]
#form_class2 = uic.loadUiType("ProgressWindow.ui")[0]
#form_class3 = uic.loadUiType("ImageViewDialog.ui")[0]

#form_class3 = uic.loadUiType("FinWindow.ui")[0]

class ImageViewDlg(QWidget) :
    def __init__(self) :
        super().__init__()
        #self.setupUi(self)
        self.lblMainView = QLabel()
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.lblMainView)
        self.setLayout(self.layout)
        self.setGeometry( QRect(100,100,800,600))
        self.setWindowTitle("ImageView")
        self.lblMainView.setMinimumSize(400,300)

    def closeEvent(self, event):
        self.parent.mainview_dlg = None
        self.parent.lblMainView.show()
        self.parent.refresh_mainview()

    def resizeEvent(self,e):
        #self.lstFinListChanged()
        #print( self.geometry())
        #self.lblMainView.setGeometry(self.geometry())
        if( self.parent.current_image_index >= 0):
            self.parent.refresh_mainview()

class ProgressDialog(QDialog):
    def __init__(self) :
        super().__init__()
        #self.setupUi(self)
        self.lblText = QLabel(self)
        self.lblText.setGeometry(100,50,300,20)
        #self.pbProgress = QProgressBar(self)
        self.pbProgress = QProgressBar(self)
        self.pbProgress.setGeometry(50,120,320,40)
        self.pbProgress.setValue(0)
        self.setGeometry(600,400,400,210)


class DolfinNoteWindow(QMainWindow, form_class) :
    def __init__(self) :
        super().__init__()
        self.setupUi(self)
        #self = QApplication.instance()
        #print( "app:", self )
        #self.btnMatch.clicked.connect(self.btnMatchFunction)
        self.btnOpenFolder.clicked.connect(self.btnOpenFolderFunction)
        self.btnNewID.clicked.connect(self.btnNewIDFunction)
        #self.btnSaveData.clicked.connect(self.btnSaveDataFunction)
        self.btnRemoveID.clicked.connect(self.btnRemoveIDFunction)
        self.btnRenameID.clicked.connect(self.btnRenameIDFunction)
        self.btnIconZoomIn.clicked.connect(self.btnIconZoomInFunction)
        self.btnIconZoomOut.clicked.connect(self.btnIconZoomOutFunction)
        #self.btnSaveFins.clicked.connect(self.btnSaveFinsFunction2)
        #self.btnViewToggle.clicked.connect(self.btnViewToggleFunction)
        self.btnNextFin.clicked.connect(self.btnNextFinFunction)
        self.btnPrevFin.clicked.connect(self.btnPrevFinFunction)
        self.actionOpenFolder.triggered.connect(self.btnOpenFolderFunction)
        self.actionSaveData.triggered.connect(self.btnSaveDataFunction)
        self.actionIconView.triggered.connect(self.setIconView)
        self.actionCloseupView.triggered.connect(self.setCloseupView)
        self.actionExportFins.triggered.connect(self.exportFins)
        self.actionExportYOLO.triggered.connect(self.exportYOLO)
        self.actionAbout.triggered.connect(self.about)
        self.btnMainView.clicked.connect(self.btnMainViewFunction)
        self.btnAddNewFin.clicked.connect(self.btnAddNewFinFunction)

        self.chkShowBbox.clicked.connect(self.chkShowBboxClicked)
        self.rbIsFinYes.clicked.connect(self.rbIsFinFunction)
        self.rbIsFinNo.clicked.connect(self.rbIsFinFunction)
        self.edtLocation.textEdited.connect(self.edtLocationEditedFunction)
        self.edtDolfinID.textEdited.connect(self.edtDolfinIDEditedFunction)
        self.edtDolfinID.editingFinished.connect(self.edtDolfinIDEditFinishedFunction)
        self.edtObservedBy.textEdited.connect(self.edtObservedByEditedFunction)
        self.edtModifiedBy.textEdited.connect(self.edtModifiedByEditedFunction)
        self.edtComment.textChanged.connect(self.edtCommentChangedFunction)

        self.finModel = QStandardItemModel(self.lstFinList)
        self.finModel.setColumnCount(2)
        self.proxyModel = QSortFilterProxyModel()
        self.proxyModel.setSourceModel(self.finModel)

        self.lstFinList.setModel(self.proxyModel)
        self.lstFinList2.setModel(self.proxyModel)
        self.selModel = self.lstFinList.selectionModel()
        self.selModel2 = self.lstFinList2.selectionModel()
        self.selModel.selectionChanged.connect(self.finModelSelectionChanged)
        self.selModel2.selectionChanged.connect(self.finModel2SelectionChanged)

        self.lstFinList.setViewMode(QListView.IconMode)
        self.lstFinList.setResizeMode(QListView.Adjust)
        self.lstFinList.doubleClicked.connect(self.lstFinListDoubleClicked)
        self.lstFinList.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.view_mode = ICON_VIEW
        #self.view_mode = CLOSEUP_VIEW
        
        self.trFinIDTree.currentItemChanged.connect(self.trFinIDTreeChanged)
        self.trFinIDTree.setAlternatingRowColors(True)
        self.trFinIDTree.setHeaderHidden(True)

        self.last_x, self.last_y = None, None
        self.temp_bbox = None
        self.show_bbox = True
        self.zoom_ratio = 1
        self.zoom_factor = 1.0
        self.current_finbbox_coords = { 'x1': -1, 'y1': -1, 'x2': -1, 'y2': -1 }
        self.current_finview_coords = { 'x1': -1, 'y1': -1, 'x2': -1, 'y2': -1 }
        self.bbox_color = { 'x1': QColor(255,0,0), 'x2': QColor(255,0,0), 'y1': QColor(255,0,0), 'y2': QColor(255,0,0) }
        self.begin_x = -1
        self.begin_y = -1

        self.mainview_width = -1
        self.mainview_height = -1
        self.mainview_dlg = None
        self.current_modifier = ''


        self.working_folder = Path("./")
        self.widget = QWidget()
        self.vbox = QVBoxLayout()
        self.finid_base_text = 'JTA'

        self.BUTTON_WIDTH = 100
        self.BUTTON_HEIGHT = 100
        #self.btnNoFin.resize( 75,40 )

            #btn = self.add_new_button( txt )
            #self.finid_button_hash[txt] = btn

        self.widget.setLayout(self.vbox)
        self.scrollArea.setWidget(self.widget)
        self.scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scrollArea.setAlignment(Qt.AlignTop)
        self.vbox.setAlignment(Qt.AlignTop)
        
        self.edtNewID.setText( self.finid_base_text)
        self.edtNewID.setCursorPosition( len(self.finid_base_text) )
        self.edtNewID.returnPressed.connect(self.btnNewIDFunction)


        self.current_image_index = -1
        self.current_fin_index0 = -1
        self.current_item = None
        self.current_fin_record = None

        self.fin_record_hash = {}
        self.finid_info = {}
        self.finicon_hash = {}
        self.image_path_list = []
        self.pan_delta_x = 0
        self.pan_delta_y = 0

        self.initialize_finid_info()
        #QApplication.restoreOverrideCursor()
        #self.setCursor(Qt.ArrowCursor)
        #QApplication.setOverrideCursor(Qt.WaitCursor)
        self.chkShowOutline.setEnabled(False)
        self.chkShowMask.setEnabled(False)
        self.chkShowBbox.setChecked(True)
        self.sldZoomRatio.setRange(1,20)
        #self.zoom_ratio = 10

        self.edtImageName.setEnabled(False)
        self.edtFinIndex.setEnabled(False)
        self.edtConfidence.setEnabled(False)
        self.edtLatitude.setEnabled(False)
        self.edtLongitude.setEnabled(False)
        self.edtMapDatum.setEnabled(False)
        #self.edtImageDateTime.setEnabled(False)
        self.edtImageDateTime.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        self.edtCreatedBy.setEnabled(False)
        self.edtCreatedOn.setEnabled(False)
        self.edtCreatedOn.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        self.edtModifiedOn.setEnabled(False)
        self.edtModifiedOn.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        self.reset_input_fields()
        self.setIconView()

        self.setMouseTracking(True)
        self.centralWidget().setMouseTracking(True)
        self.lblFinView.setMouseTracking(True)
        #self.lblFinView2.setMouseTracking(True)
        self.lblFinView.installEventFilter(self)
        self.lblZoom.hide()
        self.sldZoomRatio.hide()
        self.lblZoomRatio.hide()
        #self.btnSaveFins.hide()
        #self.btnSaveData.hide()
        #self.btnViewToggle.hide()
        self.setWindowTitle( PROGRAM_NAME + " " + PROGRAM_VERSION )


    def finview_mouse_event(self, event):
        #print("finview mouse event")
        curr_pixmap = self.orig_pixmap_list[self.current_image_index]
        image_width = curr_pixmap.size().width()
        image_height = curr_pixmap.size().height()
        widget_width = self.lblFinView.size().width()
        pic_width = self.current_finview_coords['x2'] - self.current_finview_coords['x1']
        pic_height = self.current_finview_coords['y2'] - self.current_finview_coords['y1']
        #print("pic width:", pic_width)
        self.zoom_ratio = zoom_ratio = float( widget_width ) / float( pic_width )
        #self.lblZoomRatio.setText( str( int(self.zoom_ratio * 100)/100.0 ))
        #print("zoom_ratio:", zoom_ratio, "pic_width:", pic_width)
        #print(self.current_finview_coords)
        local_x = math.floor(event.x()/zoom_ratio)
        local_y = math.floor(event.y()/zoom_ratio)
        bbox_pos = self.current_finbbox_coords
        finview_pos = self.current_finview_coords
        temp_bbox = {}
        #event.type() in [ QEvent.MouseMove, QEvent.MouseButtonPress, QEvent.MouseButtonRelease ] 

        if( event.type() == QEvent.MouseButtonPress and event.buttons() == Qt.LeftButton ):
            self.begin_x = local_x + finview_pos['x1']
            self.begin_y = local_y + finview_pos['y1']
            if( self.finview_mode == FV_DRAGREADY ):
                #print("from dragready to drag")
                self.finview_mode = FV_DRAG
            elif( self.finview_mode == FV_ADDNEWFIN ):
                #print("from addnewfin to newfin drag")
                self.finview_mode = FV_NEWFIN_DRAG
                #print( "bbox", bbox_pos )
                #print( "finview", finview_pos )
                #print( "begin_x, y", self.begin_x, self.begin_y)
                #temp_bbox

        elif( event.type() == QEvent.MouseButtonPress and event.buttons() == Qt.RightButton ):
            self.begin_x = local_x
            self.begin_y = local_y
            self.prev_finview_mode = self.finview_mode
            self.finview_mode = FV_PAN
        elif( event.type() == QEvent.MouseMove and self.finview_mode in [ FV_PAN  ] ):
            #print( "pan mode begin_x, local_x:", self.begin_x, local_x )
            #print( "pan mode begin_y, local_y:", self.begin_y, local_y )
            x_move = local_x - self.begin_x
            y_move = local_y - self.begin_y
            #print( "xy move", x_move, y_move, "pic wh", pic_width, pic_height)
            no_move = False
            if 'x1' in self.current_finbbox_coords.keys():
                if self.current_finview_coords['x1'] > self.current_finbbox_coords['x1'] + x_move:
                    x_move = self.current_finview_coords['x1'] - self.current_finbbox_coords['x1'] 
                if self.current_finview_coords['x2'] < self.current_finbbox_coords['x2'] + x_move:
                    x_move = self.current_finbbox_coords['x2'] - self.current_finview_coords['x2']
                if self.current_finview_coords['y1'] > self.current_finbbox_coords['y1'] + y_move:
                    y_move = self.current_finview_coords['y1'] - self.current_finbbox_coords['y1']
                if self.current_finview_coords['y2'] < self.current_finbbox_coords['y2'] + y_move:
                    y_move = self.current_finbbox_coords['y2'] - self.current_finview_coords['y2']

            if self.current_finview_coords['x1'] < x_move:
                x_move = self.current_finview_coords['x1']
            if self.current_finview_coords['x2'] - x_move > image_width:
                x_move = image_width - self.current_finview_coords['x2']
            if self.current_finview_coords['y1'] < y_move:
                y_move = self.current_finview_coords['y1']
            if self.current_finview_coords['y2'] - y_move > image_height:
                y_move = image_height - self.current_finview_coords['y2']

            self.pan_delta_x += x_move
            self.pan_delta_y += y_move 
            self.begin_x = local_x
            self.begin_y = local_y
            

        elif( event.type() == QEvent.MouseMove and self.finview_mode in [ FV_ADDNEWFIN, FV_NOFINIMAGE ]):
            #print("mouse move in addnewfin")
            if( self.finview_mode == FV_ADDNEWFIN ):
                self.lblFinView.setCursor( Qt.CrossCursor )

            self.temp_bbox = None
            #print( zoom_ratio, local_x, local_y, self.current_finview_coords )
                
        elif( event.type() == QEvent.MouseMove and self.finview_mode in [ FV_NEWFIN_DRAG  ] ):
            #print("mouse move in newfin drag")
            x1, x2 = self.begin_x, finview_pos['x1'] + local_x
            y1, y2 = self.begin_y, finview_pos['y1'] + local_y
            if x1 > x2:
                x1, x2 = x2, x1
            if y1 > y2:
                y1, y2 = y2, y1
            self.temp_bbox = { 'x1': max( x1, 0 ), 'y1': max( y1, 0 ), 'x2':min( x2, image_width ), 'y2':min( y2, image_height ) }

        elif( event.type() == QEvent.MouseMove and self.finview_mode in [ FV_VIEW, FV_DRAGREADY ] ):
                
            #print("mouse move in view or dragready mode")
            #check cursor-bbox distance
            dist = {}
            #print( dist, bbox_pos, local_x, finview_pos )
            #print(self.current_image_index, self.current_fin_index0 )
            #print( )
            pos_to_move = []
            dist['x1'] = abs( bbox_pos['x1'] - ( local_x + finview_pos['x1'] ) )
            dist['x2'] = abs( ( bbox_pos['x2'] ) - ( local_x + finview_pos['x1'] ) )
            dist['y1'] = abs( bbox_pos['y1'] - ( local_y + finview_pos['y1'] ) )
            dist['y2'] = abs( ( bbox_pos['y2'] ) - ( local_y + finview_pos['y1'] ) )
            if( dist['x1'] <= dist['x2'] ):
                min_x = 'x1'
            else:
                min_x = 'x2'
            if( dist['y1'] <= dist['y2'] ):
                min_y = 'y1'
            else:
                min_y = 'y2'

            if dist[min_x] < bbox_threshold:
                pos_to_move.append(min_x)
            if dist[min_y] < bbox_threshold:
                pos_to_move.append(min_y)
            
            if( len( pos_to_move ) > 0 ):
                self.finview_mode = FV_DRAGREADY
                self.pos_to_move = pos_to_move
                if( len( self.pos_to_move ) == 1 ) :
                    if self.pos_to_move[0][0] == 'x':
                        self.lblFinView.setCursor( Qt.SizeHorCursor )
                    else:
                        self.lblFinView.setCursor( Qt.SizeVerCursor )
                else:
                    if( self.pos_to_move[0][1] == self.pos_to_move[1][1] ):
                        self.lblFinView.setCursor( Qt.SizeFDiagCursor )
                    else:
                        self.lblFinView.setCursor( Qt.SizeBDiagCursor )
            else:
                self.finview_mode = FV_VIEW
                self.lblFinView.setCursor( Qt.ArrowCursor )
                #self.lblFinView.setCursor(  )
                self.pos_to_move = pos_to_move = []

            for pos in self.bbox_color.keys():
                if pos in pos_to_move:
                    self.bbox_color[pos] = near_cursor_bbox_color
                else:
                    self.bbox_color[pos] = normal_bbox_color

        elif( event.type() == QEvent.MouseMove and self.finview_mode == FV_DRAG ):
            diff = {}
            diff['x'] = finview_pos['x1'] + local_x - self.begin_x
            diff['y'] = finview_pos['y1'] + local_y - self.begin_y
            #print("in drag mode ["+self.nearby_bbox_line+"] from ("+str(self.begin_x)+","+str(self.begin_y)+")")
            if( len( self.pos_to_move ) > 0 ):
                self.temp_bbox = {}
                for k in bbox_pos.keys():
                    self.temp_bbox[k] = bbox_pos[k]
                for k in self.pos_to_move:
                    self.temp_bbox[k] += diff[k[0]]

                # sanity check
                self.temp_bbox['x1'] = max( self.temp_bbox['x1'], finview_pos['x1'] )
                self.temp_bbox['y1'] = max( self.temp_bbox['y1'], finview_pos['y1'] )
                self.temp_bbox['x2'] = min( self.temp_bbox['x2'], finview_pos['x2'] -1 )
                self.temp_bbox['y2'] = min( self.temp_bbox['y2'], finview_pos['y2'] -1)

        elif( event.type() == QEvent.MouseButtonRelease ):
            #print("mouse release")
            if( self.finview_mode == FV_DRAG ):
                #print("mode was drag")
                self.finview_mode = FV_VIEW
                self.begin_x = -1
                self.begin_y = -1
                for k in self.pos_to_move:
                    self.bbox_color[k] = normal_bbox_color
                orig_pixmap = self.orig_pixmap_list[self.current_image_index]
                image_width = orig_pixmap.size().width()
                image_height = orig_pixmap.size().height()
                self.current_fin_record.center_x = ( float( self.temp_bbox['x1'] + self.temp_bbox['x2'] ) / 2.0 ) / image_width
                self.current_fin_record.center_y = ( float( self.temp_bbox['y1'] + self.temp_bbox['y2'] ) / 2.0 ) / image_height
                self.current_fin_record.width = float( self.temp_bbox['x2'] - self.temp_bbox['x1'] ) / image_width
                self.current_fin_record.height = float( self.temp_bbox['y2'] - self.temp_bbox['y1'] ) / image_height
                self.temp_bbox = None

                fin_record = self.current_fin_record
                fin_index0 = fin_record.fin_index - 1
                finname = fin_record.get_finname()

                icon_pixmap = self.get_cropped_fin_image( orig_pixmap, self.current_image_index, self.current_fin_index0, False, None, {}, True ).scaledToWidth(200)
                icon_image = icon_pixmap.toImage()
                self.finicon_hash[finname] = icon_image
                if fin_record.dolfin_id != '':
                    icon_pixmap = self.write_finid_on_icon( icon_pixmap, fin_record.dolfin_id)
                self.current_fin_record.items[0].setIcon(QIcon(icon_pixmap))

                self.update_modification_info()

            elif( self.finview_mode == FV_PAN ):
                self.finview_mode = self.prev_finview_mode

            elif( self.finview_mode == FV_NEWFIN_DRAG ):
                #print("newfin drag")
                #QApplication.restoreOverrideCursor()
                self.finview_mode = FV_VIEW
                self.begin_x = -1
                self.begin_y = -1
                image_index = self.current_image_index
                #self.bbox_color[self.pos_to_move] = normal_bbox_color
                orig_pixmap = self.orig_pixmap_list[self.current_image_index]
                image_width = orig_pixmap.size().width()
                image_height = orig_pixmap.size().height()
                prev_fin_record = self.current_fin_record
                
                fin_record = DolfinRecord()
                fin_record.set_info( prev_fin_record.get_info() )

                if fin_record.confidence < 0  :
                    fin_count -= 1
                    #self.lstFinList.takeItem( fin_count )
                    self.all_image_fin_list[image_index] = []
                    self.finModel.removeRow( self.current_item.row() )
                    del self.finicon_hash[fin_record.get_finname()]

                #print( image_index, "fin_info:", fin_info)
                fin_record.is_fin = True
                fin_record.confidence = 1
                fin_record.fin_index = -1
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                fin_record.created_on = now
                fin_record.created_by = self.current_modifier
                if fin_record.created_by == '':
                    fin_record.created_by = "DolfinNote_v0.0.2"
                fin_record.dolfin_id = ''
                fin_record.modified_on = ''
                fin_record.modified_by = ''
                fin_record.center_x = ( float( self.temp_bbox['x1'] + self.temp_bbox['x2'] ) / 2.0 ) / image_width
                fin_record.center_y = ( float( self.temp_bbox['y1'] + self.temp_bbox['y2'] ) / 2.0 ) / image_height
                fin_record.width = float( self.temp_bbox['x2'] - self.temp_bbox['x1'] ) / image_width
                fin_record.height = float( self.temp_bbox['y2'] - self.temp_bbox['y1'] ) / image_height
                self.zoom_ratio = float( widget_width ) / float( self.temp_bbox['x2'] - self.temp_bbox['x1'] )
                #print( "zoom ratio:", self.zoom_ratio)
                self.temp_bbox = None
                #self.zoom_ratio = zoom_ratio = float( widget_width ) / float( pic_width )

                self.current_fin_record = fin_record
                self.all_image_fin_list[image_index].append( fin_record )

                fin_record.fin_index = len( self.all_image_fin_list[image_index] )
                fin_index0 = fin_record.fin_index - 1

                finname = fin_record.get_finname()

                icon_pixmap = self.get_cropped_fin_image( orig_pixmap, image_index, fin_index0, False, None, {}, True ).scaledToWidth(200)
                icon_image = icon_pixmap.toImage()
                self.finicon_hash[finname] = icon_image
                self.fin_record_hash[finname] = fin_record

                item1 = QStandardItem( QIcon(icon_pixmap), fin_record.get_finname() )
                item2 = QStandardItem( '' )
                fin_record.items = [ item1, item2 ]

                self.finModel.appendRow( fin_record.items )

                self.proxyModel.sort(0, Qt.AscendingOrder)
                item_index = self.finModel.indexFromItem( item1 )
                new_index = self.proxyModel.mapFromSource(item_index)
                self.selModel2.setCurrentIndex(new_index,QItemSelectionModel.ClearAndSelect)

            self.lblFinView.setCursor( Qt.ArrowCursor )
            self.refresh_mainview()

        #print( FV_MODE[self.finview_mode], "local_x,y", local_x, local_y, "begin_x,y", self.begin_x, self.begin_y, "event_x,y", event.x(), event.y(), "zoom_ratio", zoom_ratio )
        #print( "finbbox", self.current_finbbox_coords )
        #print( "finview", self.current_finview_coords)
        self.refresh_finview()

    def eventFilter(self, source, event):
        #print( event.type(), source)
        if( event.type() in [ QEvent.MouseMove, QEvent.MouseButtonPress, QEvent.MouseButtonRelease ] ):
            if( source == self.lblFinView ):
                if( self.current_image_index < 0):
                    return QMainWindow.eventFilter(self, source, event)
                self.finview_mouse_event(event)
        #elif( event.type() in [ QEvent.Wheel ] ):
            #print( "wheel event")
            #if( source == self.lstFinList ):
                #print( "wheel event in lstFinList")
        return QMainWindow.eventFilter(self, source, event)

    def messageBox(self,message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(message)
        msg.setWindowTitle("Information")
        msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        #msg.show()
        #msg.setDetailedText("The details are as follows:")        
        retval = msg.exec_()
        #print( "value of pressed message box button:", retval)
	
    #def msgbtn(i):
        #print( "Button pressed is:",i.text() )
    def exportFins(self):
        self.messageBox( "Export Fins function will be here someday.")

    def exportYOLO(self):
        self.messageBox( "Export YOLO function will be here someday.")

    def about(self):
        self.messageBox( PROGRAM_NAME + " " + PROGRAM_VERSION )


    def wheelEvent(self, event):
        #print("wheel event")
        angle_delta = event.angleDelta().y()
        if self.view_mode == ICON_VIEW:
            #print("angle delta", angle_delta)
            if event.modifiers() & Qt.ControlModifier:
                if angle_delta > 0:
                    self.btnIconZoomInFunction()
                else:
                    self.btnIconZoomOutFunction()
                #print("control")
        else:
            prev_zoom_factor = self.zoom_factor
            zf = 1.0 + (angle_delta / 8.0) * 0.01

            curr_pixmap = self.orig_pixmap_list[self.current_image_index]
            image_width = curr_pixmap.size().width()
            image_height = curr_pixmap.size().height()
            widget_width = self.lblFinView.size().width()
            pic_width = self.current_finview_coords['x2'] - self.current_finview_coords['x1']
            if pic_width == image_width and zf < 1:
                zf = 1

            self.zoom_factor *= zf
            if self.finview_mode == FV_ADDNEWFIN:
                if self.zoom_factor < 1:
                    self.zoom_factor = 1
            elif self.zoom_factor > 1.5:
                self.zoom_factor = 1.5

            self.zoom_ratio = zoom_ratio = float( widget_width ) / float( pic_width )
            self.refresh_finview()


    def mousePressEvent(self, e):
        return

    def mouseMoveEvent(self, e):
        #print( e.x(), e.y() )
        if( self.current_fin_index0 < 0):
            return

        curr_x = e.x() - self.stackedWidget.pos().x()
        curr_y = e.y() - self.stackedWidget.pos().y()
        #self.lblStatus.setText( "curr pos (" + str(curr_x)+","+str(curr_y)+")")
        self.update()

        if self.last_x is None: # First event.
            self.last_x = curr_x
            self.last_y = curr_y
            return # Ignore the first time.

        #painter = QPainter(self.lblFinView.pixmap())
        #painter.drawLine(self.last_x, self.last_y, curr_x, curr_y)
        #painter.end()
        self.update()

        # Update the origin for next time.
        self.last_x = curr_x
        self.last_y = curr_y

    def mouseReleaseEvent(self, e):
        self.last_x = None
        self.last_y = None

    def resizeEvent(self,e):
        self.refresh_finview()
        if( self.current_image_index >= 0):
            self.refresh_mainview()

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

    def btnAddNewFinFunction(self):
        if( self.current_image_index < 0 ):
            return
        self.current_fin_index0 = -1
        self.zoom_factor = 1.0
        pixmap = self.get_fit_pixmap_to_view( self.orig_pixmap_list[self.current_image_index], self.lblFinView )
        w = self.orig_pixmap_list[self.current_image_index].size().width()
        h = self.orig_pixmap_list[self.current_image_index].size().height()
        self.current_finview_coords = { 'x1': 0, 'y1': 0, 'x2': w, 'y2': h }
        self.lblFinView.setPixmap( pixmap )
        self.finview_mode = FV_ADDNEWFIN
        #print("finview mode now add new fin")
        #self.prev_finlist_index = self.lstFinList.currentRow()

    def btnMainViewFunction(self):
        if( self.mainview_dlg == None ):
            self.mainview_dlg = ImageViewDlg()
            self.mainview_dlg.parent = self
            self.mainview_dlg.show()
            self.lblMainView.hide()
            self.refresh_mainview()


    def refresh_mainview(self):
        #print( "pixmap 0:", self.orig_pixmap_list[image_index] )
        image_index = self.current_image_index
        if( self.orig_pixmap_list[image_index] == None):
            self.orig_pixmap_list[image_index] = QPixmap(self.image_path_list[image_index])

        pixmap = self.orig_pixmap_list[image_index].copy()

        view_list = []

        view_list.append( self.lblMainView )
        if( self.mainview_dlg != None ):
            view_list.append( self.mainview_dlg.lblMainView )

        #print("pixmap 1:", pixmap)

        for view in view_list:

            l_pixmap = self.get_fit_pixmap_to_view( pixmap, view )
            #print("pixmap 2:", l_pixmap)

            l_painter = QPainter( l_pixmap )
            l_painter.setPen(QColor(255, 0,0))
            pixmap_width = l_pixmap.width()
            pixmap_height = l_pixmap.height()

            for fin_record in self.all_image_fin_list[image_index]:
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
            view.setPixmap(l_pixmap)

    def keyPressEvent(self, event):
        numpad_mod = int(event.modifiers()) & Qt.KeypadModifier
        #print("key press")
        if event.key() == Qt.Key_Up:
            self.edtDolfinIDEditFinishedFunction()
            self.btnPrevFinFunction()
        elif event.key() == Qt.Key_Down:  
            self.edtDolfinIDEditFinishedFunction()
            self.btnNextFinFunction()
        elif event.key() == Qt.Key_Plus and numpad_mod:
            self.btnIconZoomInFunction()
            #print("numpad plus")
        elif event.key() == Qt.Key_Minus and numpad_mod:
            #print("numpad minus")
            self.btnIconZoomOutFunction()
        return
        #elif event.key() == Qt.Key_1 and event.modifiers() & Qt.AltModifier: 
        #    #print('Alt 1')
        #    self.setIconView()
        #elif event.key() == Qt.Key_2 and event.modifiers() & Qt.AltModifier: 
        #    #print('Alt 2')
        #    self.setCloseupView()
        #elif event.key() == Qt.Key_S and event.modifiers() & Qt.ControlModifier: 
        #    #print('Alt 2')
        #    self.btnSaveDataFunction()


        #self.up()    

    def btnPrevFinFunction(self):
        index = self.lstFinList2.currentIndex()
        if index == None or index.model() == None:
            return
        #print(index)
        curr_row = index.row()
        #print(curr_row)
        if( curr_row == 0 ):
            return
        prev_index = index.model().sibling(curr_row-1,0,index)
        #print(prev_index.row())
        self.lstFinList2.setCurrentIndex(prev_index)
        return

    def btnNextFinFunction(self):
        index = self.lstFinList2.currentIndex()
        if index == None or index.model() == None:
            return
        #print(index)
        curr_row = index.row()
        rowcount = index.model().rowCount()
        #print(curr_row, rowcount)
        if( curr_row == rowcount - 1):
            return

        next_index = index.model().sibling(curr_row+1,0,index)
        #print(next_index.row())
        self.lstFinList2.setCurrentIndex(next_index)
        return

    def chkShowBboxClicked(self):
        if self.chkShowBbox.isChecked():
            self.show_bbox = True
        else:
            self.show_bbox = False
        #print("show bbox", self.show_bbox)
        self.refresh_finview()

    def trFinIDTreeChanged(self,current,previous):
        #print( current.text(0) )
        if current != None:
            self.filter_finlist( current.text(0) )
        return


    def lstFinListDoubleClicked(self):
        index = self.lstFinList.currentIndex()
        self.setCloseupView()
        self.lstFinList2.setCurrentIndex(index)
        #self.stackedWidget.setCurrentIndex(CLOSEUP_VIEW)

    def filter_finlist( self, text ):
        #print( "filter:", text)
        if( text == 'All'):
            self.proxyModel.setFilterRegExp(QRegExp('', Qt.CaseInsensitive,QRegExp.FixedString))
            self.proxyModel.setFilterKeyColumn(1)
        elif( text == BTN_NOT_ASSIGNED):
            # find fins without whitespace
            #self.proxyModel
            self.proxyModel.setFilterRegExp(QRegExp('^$', Qt.CaseInsensitive,QRegExp.RegExp))
            self.proxyModel.setFilterKeyColumn(1)
            #pass
        elif( text[0:3] == self.finid_base_text or text == BTN_NO_FIN):
            self.proxyModel.setFilterRegExp(QRegExp(text, Qt.CaseInsensitive,QRegExp.FixedString))
            self.proxyModel.setFilterKeyColumn(1)

    def update_toolbutton_icon(self,fin_id):
        #print("update tool button", fin_id)
        btn = self.finid_info[fin_id]['button']
        fin_record_hash = self.finid_info[fin_id]['fin_record_hash'] 
        finname_list = self.finid_info[fin_id]['finname_list']
        #print( fin_record_hash )
        #print( finname_list )

        if len(fin_record_hash.keys()) == 0:
            self.finid_info[fin_id]['button'].setText(fin_id)
            self.finid_info[fin_id]['button'].setIcon( QIcon())
            #self.finid_info[btn_id]['button'].setIconSize(QSize(16,16))
        else:
            finname = finname_list[-1]
            item1, item2 = fin_record_hash[finname].items
            button_icon = self.make_toolbutton_icon( fin_id, QIcon(QPixmap(self.finicon_hash[finname])) )
            self.finid_info[fin_id]['button'].setIcon( item1.icon() )
            #self.finid_button_hash[btn_id].setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            self.finid_info[fin_id]['button'].setIconSize(QSize(92,92))
            self.finid_info[fin_id]['button'].setText('')
        return

    def make_toolbutton_icon( self, fin_id, icon ):
        pixmap = icon.pixmap(QSize(200,200)).copy(25,25,150,150).scaled(QSize(88,88))
        painter = QPainter( pixmap )
        pen = QPen(Qt.black)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(Qt.white)
        path = QPainterPath()
        font = QFont("Arial",12)
        font.setBold(True)
        path.addText(8,84,font,fin_id)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawPath(path)
        #painter.setFont(font)
        #painter.drawText( 10, 80, btn_id)
        painter.end()
        return QIcon(pixmap)

    def write_finid_on_icon( self, icon_pixmap, item2_text ):
        new_pixmap = icon_pixmap.copy()
        painter = QPainter( new_pixmap )
        pen = QPen( Qt.black )
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(Qt.white)
        path = QPainterPath()
        font = QFont("Arial",24)
        font.setBold(True)
        path.addText(45,180,font,item2_text)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawPath(path)
        painter.end()
        return new_pixmap


    def make_btnClicked(self,new_finid):
        def btnClicked():
            #print(btn_id)

            #this is proxy index
            selected_index_list = self.selModel.selection().indexes()
            if len( selected_index_list ) == 0:
                return
            #print( selected_index_list)

            new_index_list = []
            model = selected_index_list[0].model()
            if hasattr(model, 'mapToSource'):
                for index in selected_index_list:
                    new_index = model.mapToSource(index)
                    new_index_list.append( new_index )
            #print( new_index_list)
            #print(selected_index_list[0])
            #item = self.selModel.selection().indexes()[0]
            selection = self.selModel.selectedRows()
            #print(selection)
            #fins = self.finModel.getSelectedItems(selection)
            #print(fins)
            for index in new_index_list:
                #print(self.finModel.itemFromIndex(index))
                #print(self.finModel.itemFromIndex(index).data())
                item = self.finModel.itemFromIndex(index)
                finname = item.data(Qt.DisplayRole)
                fin_record = self.fin_record_hash[finname]
                #fin_record = self.finid_info[]
                item1, item2 = fin_record.items
                #finname = fin_record.get_finname()

                old_finid = fin_record.dolfin_id
                #print("old:", fin_record.dolfin_id)

                if new_finid == BTN_NO_FIN:
                    fin_record.is_fin = False
                    fin_record.dolfin_id = ''
                elif new_finid == BTN_NOT_ASSIGNED:
                    fin_record.is_fin = True
                    fin_record.dolfin_id = ''
                else:
                    fin_record.is_fin = True
                    #fin_record.dolfin_id = btn_id

                self.process_finid_change( fin_record, new_finid, old_finid )
                #print("new:", fin_record.dolfin_id)


        return btnClicked


    def btnNewIDFunction(self):
        new_id = self.edtNewID.text()
        if new_id in self.finid_info.keys() or new_id == self.finid_base_text:
            return

        btn = self.add_new_finid_info(new_id)
        
        self.edtNewID.setText( self.finid_base_text)
        self.edtNewID.setCursorPosition( len(self.finid_base_text) )

    def btnOpenFolderFunction(self):
        dir = QFileDialog.getExistingDirectory(self, 'Open directory', str(self.working_folder.parent))

        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.edtFolder.setText(dir)
        self.working_folder = Path(dir)
        result_path = Path( self.working_folder ).joinpath( "result" )
        result_dir = str( result_path )
        if not result_path.exists():
            result_path.mkdir()

        if os.path.isdir(dir):
            self.fin_record_hash = {}
            self.image_path_list = []
            self.orig_pixmap_list = []
            self.all_image_fin_list = [[],[]]
            self.current_image_index = -1
            self.current_fin_index0 = -1
            self.current_item = None
            self.current_fin_record = None

            self.initialize_finid_info()

            img_formats = ['.bmp', '.jpg', '.jpeg', '.png', '.tif', '.tiff', '.dng']

            files = sorted(glob.glob(os.path.join(dir, '*.*')))  # dir
            images = [x for x in files if os.path.splitext(x)[-1].lower() in img_formats]

            #print("images:", images )
            self.progressDlg = ProgressDialog()
            self.progressDlg.setModal(True)
            self.progressDlg.lblText.setText("Loading 0 of " + str( len( images ) ) + " image files...")
            self.progressDlg.pbProgress.setValue( 0 ) 
            self.progressDlg.show()


            i = 0
            for img in images:
                #print("loading", img, i )
                image_path = self.working_folder.joinpath( img )
                self.image_path_list.append( image_path )
                self.all_image_fin_list.append([])
                self.orig_pixmap_list.append( None )
                #time.sleep(1)
                #self.progressDlg.pbProgress.update()

                #self.processed_pixmap_list.append( None )

            csv_path = self.working_folder.joinpath( self.working_folder.name + ".csv" )
            icondb_path = self.working_folder.joinpath( self.working_folder.name + ".icondb" )
            if( not csv_path.exists() ):
                self.working_folder = ''
                return

            if icondb_path.exists():
                self.finicon_hash = self.load_and_unpickle_image_hash( icondb_path )
            else:
                self.finicon_hash = {}
                #self.finicon_hash = pickle.load( open( icondb_path, "rb" ) )

            i = 0
            with open(str(csv_path), newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                prev_image_name = ''
                prev_index = -1
                pixmap = None

                for row in reader:
                    image_index = -1
                    image_path = self.working_folder.joinpath(row['image_name'])

                    if image_path in self.image_path_list:
                        image_index = self.image_path_list.index( image_path )
                    image_name = row['image_name']
                    #filepath_stem = ''
                    #pixmap = None
                    if image_name != prev_image_name:
                        pixmap = None
                        prev_image_name = image_name
                        i += 1
                        self.progressDlg.pbProgress.setValue( int( ( i / float(len(images)) ) * 100 ) ) 
                        self.progressDlg.lblText.setText("Loading " + str( i ) + " of " + str( len( images ) ) + " image files...")
                        self.progressDlg.update()
                        QApplication.processEvents() 


                    fin_record  = DolfinRecord( row )
                    self.all_image_fin_list[image_index].append( fin_record )

                    if( fin_record.image_width == 0 ):
                        image_width, image_height = imagesize.get(str(image_path))
                        #print(width, height)
                        fin_record.image_width = image_width
                        fin_record.image_height = image_height
                    
                    if fin_record.dolfin_id != '':
                        if fin_record.dolfin_id not in self.finid_info.keys():
                            self.add_new_finid_info(fin_record.dolfin_id)

                    fin_index0 = int(row['fin_index']) - 1
                    old_iconfile_name = "{}_{:02d}.JPG".format( Path( fin_record.image_name ).stem, int( fin_record.fin_index ) ) 
                    finname = fin_record.get_finname()
                    iconfile_name = finname + ".JPG"

                    new_finid = fin_record.dolfin_id
                    if fin_record.is_fin == False:
                        new_finid = BTN_NO_FIN

                    if new_finid != '' and new_finid not in self.finid_info.keys():
                        self.add_new_finid_info( new_finid )

                    if len(self.finicon_hash.keys()) > 0 and finname in self.finicon_hash.keys():
                        # already got icon:
                        icon_pixmap = QPixmap( self.finicon_hash[finname] )
                    else:
                        #print("find ", old_iconfile_name)
                        if old_iconfile_name in self.finicon_hash.keys():
                            #print("converting old hash to new hash")
                            self.finicon_hash[finname] = self.finicon_hash[old_iconfile_name]
                            icon_pixmap = QPixmap( self.finicon_hash[finname] )
                            del self.finicon_hash[old_iconfile_name]
                        else:
                            if pixmap == None:
                                pixmap = QPixmap(str(image_path))
                            icon_pixmap = self.get_cropped_fin_image( pixmap, image_index, fin_index0, False, None, {}, True ).scaledToWidth(200)
                            icon_image = icon_pixmap.toImage()
                            self.finicon_hash[finname] = icon_image
                            icon_pixmap = QPixmap( icon_image )

                    self.fin_record_hash[finname] = fin_record

                    item1 = QStandardItem( finname )
                    #item1.setData(fin_record)
                    item2 = QStandardItem( new_finid )
                    fin_record.items = [ item1, item2 ]

                    #print( self.finid_info )

                    if new_finid != '':
                        self.process_finid_change( fin_record, new_finid )
                    else:
                        item1.setIcon(QIcon(icon_pixmap))

                    self.finModel.appendRow(  fin_record.items )
                    self.lstFinList.update()
                    self.update()
                    QApplication.processEvents() 

            self.progressDlg.close()

        QApplication.restoreOverrideCursor()

    def finModelSelectionChanged(self):
        #print("selection changed, in icon_view")
        return

    def finModel2SelectionChanged(self):
        #print("selection changed, in closeup_view", self.view_mode)
        if self.view_mode == ICON_VIEW:
            return

        #print("closeup view")
        current_item = None

        selected_index_list = self.selModel2.selection().indexes()
        #print("selected:",selected_index_list)
        if len( selected_index_list ) == 0:
            self.lblMainView.clear()
            self.lblFinView.clear()
            self.reset_input_fields()
            return

        new_index_list = []
        model = selected_index_list[0].model()
        if hasattr(model, 'mapToSource'):
            for index in selected_index_list:
                new_index = model.mapToSource(index)
                new_index_list.append( new_index )

        for index in new_index_list:
            #print(self.finModel.itemFromIndex(index))
            #print(self.finModel.itemFromIndex(index).data())
            self.current_item = current_item = self.finModel.itemFromIndex(index)
            finname = current_item.text()
            fin_record = self.fin_record_hash[finname]
            self.current_fin_record = fin_record
            #self.current_item = 
            #print("item text:", item_text)
            #print("fin_record:", fin_record)

        #print("closeup view")
        #self.current_fin_record = fin_record
        image_name = fin_record.image_name
        image_path = self.working_folder.joinpath(image_name)
        #print("fin coords:", fin_record.get_x1y1x2y2())

        self.zoom_factor = 1.0
        self.pan_delta_x = self.pan_delta_y = 0
        self.is_record_changed = False
        fin_text = fin_record.get_itemname()
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
            #print( "image_index", image_index, "fin_index0", fin_index0)
            fin_record = self.current_fin_record = self.all_image_fin_list[image_index][fin_index0]
            self.finview_mode = FV_VIEW
        else:
            image_name = fin_text
            image_path = self.working_folder.joinpath( image_name )
            image_index = self.image_path_list.index( image_path)
            fin_index0 = self.current_fin_index0 = 0
            fin_record = self.current_fin_record = self.all_image_fin_list[image_index][fin_index0]
            #pixmap = self.get_fit_pixmap_to_view( self.orig_pixmap_list[self.current_image_index], self.lblFinView )
            if( self.orig_pixmap_list[image_index] == None ):
                self.orig_pixmap_list[image_index] = QPixmap(str(image_path))
            w = self.orig_pixmap_list[image_index].size().width()
            h = self.orig_pixmap_list[image_index].size().height()
            self.current_finview_coords = { 'x1': 0, 'y1': 0, 'x2': w, 'y2': h }
            self.finview_mode = FV_NOFINIMAGE
            #print("finview:", self.current_finview_coords)
            #fin_index = -1

        #print("imagename:", image_name)
        #print(image_path)

        if( self.current_image_index != image_index ): # new image
            self.current_image_index = image_index
            if( self.orig_pixmap_list[image_index] == None ):
                self.orig_pixmap_list[image_index] = QPixmap(str(image_path))
            self.refresh_mainview()

        self.refresh_finview()
        self.reset_input_fields()

        if( fin_record != None ):

            #기타 field 작업
            self.edtImageName.setText(str(fin_record.image_name))
            self.edtFinIndex.setText(str(fin_record.fin_index))
            self.edtConfidence.setText(str(fin_record.confidence))
            #print("is fin", fin_record.is_fin)
            if( fin_record.is_fin ):
                self.rbIsFinYes.setChecked(True)
                self.rbIsFinNo.setChecked(False)
            else:
                self.rbIsFinYes.setChecked(False)
                self.rbIsFinNo.setChecked(True)
            self.edtImageDateTime.setDateTime(QDateTime.fromString(fin_record.image_datetime,"yyyy-MM-dd hh:mm:ss"))
            self.edtLocation.setText(str(fin_record.location))
            self.edtLatitude.setText(str(fin_record.latitude))
            self.edtLongitude.setText(str(fin_record.longitude))
            self.edtMapDatum.setText(str(fin_record.map_datum))
            self.edtDolfinID.setText(str(fin_record.dolfin_id))
            self.edtObservedBy.setText(str(fin_record.observed_by))
            self.edtCreatedBy.setText(str(fin_record.created_by))
            self.edtCreatedOn.setDateTime(QDateTime.fromString(fin_record.created_on,"yyyy-MM-dd hh:mm:ss"))
            self.edtModifiedBy.setText(str(fin_record.modified_by))
            self.edtModifiedOn.setDateTime(QDateTime.fromString(fin_record.modified_on,"yyyy-MM-dd hh:mm:ss"))

            wasBlocked = self.edtComment.blockSignals(True)
            self.edtComment.setPlainText(fin_record.comment)
            self.edtComment.blockSignals(wasBlocked)

        return

    def get_cropped_fin_image(self, pixmap, image_index, fin_index0, draw_bbox = False, widget = None, temp_bbox = {}, square = False ):
        #print( "draw bbox", draw_bbox)
        start = time.perf_counter()

        orig_pixmap = pixmap #self.orig_pixmap_list[image_index]
        orig_width = orig_pixmap.size().width()
        orig_height = orig_pixmap.size().height()
        draw_fin_box = False
        finbbox = {}
        finview = {}
        fin_record = None

        if( fin_index0 >= 0 ):
            fin_record = self.all_image_fin_list[image_index][fin_index0]

        if( fin_index0 >= 0 and fin_record.confidence > 0 ):
            cls, center_x, center_y, fin_width, fin_height, conf = fin_record.get_detection_info()

            finbbox['width'] = int( fin_width * orig_width )
            finbbox['height'] = int( fin_height * orig_height )
            if square == True:
                finbbox['width'] = max( int( fin_width * orig_width ), int( fin_height * orig_height ) )
                finbbox['height'] = finbbox['width']
            finbbox['x1'] = int( center_x * orig_width - ( finbbox['width'] / 2 ) )
            finbbox['y1'] = int( center_y * orig_height - ( finbbox['height']  / 2 ) )
            finbbox['x2'] = finbbox['x1'] + finbbox['width']
            finbbox['y2'] = finbbox['y1'] + finbbox['height']
            #print("finbbox", finbbox)

            if widget == None:
                finview['width'] = int( finbbox['width'] * 1.5 / self.zoom_factor )
                finview['height'] = int( finbbox['height'] * 1.5 / self.zoom_factor )
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
                    finview['width']  = int( finbbox['width'] * 1.5 / self.zoom_factor )
                    finview['height'] = int( finbbox['width'] * 1.5 / self.zoom_factor / widget_wh_ratio )
                else:
                    # fit to widget height
                    finview['height'] = int( finbbox['height'] * 1.5 / self.zoom_factor )
                    finview['width']  = int( finbbox['height'] * 1.5 / self.zoom_factor * widget_wh_ratio )
                finview['x1'] = max( int( center_x * orig_width  - ( finview['width']  / 2 ) ), 0 )
                finview['y1'] = max( int( center_y * orig_height - ( finview['height'] / 2 ) ), 0 )
                finview['x2'] = finview['x1'] + finview['width']
                finview['y2'] = finview['y1'] + finview['height']
                if( finview['x2'] > orig_width ):
                    finview['x1'] = max( finview['x1'] - ( finview['x2'] - orig_width ), 0 ) 
                    #finview['x1'] = finview['x1'] - ( finview['x2'] - orig_width )
                    finview['x2'] = orig_width
                if( finview['y2'] > orig_height ):
                    finview['y1'] = max( finview['y1'] - ( finview['y2'] - orig_height ), 0 )
                    #finview['y1'] = finview['y1'] - ( finview['y2'] - orig_height )
                    finview['y2'] = orig_height
                finview['x1'] -= self.pan_delta_x
                finview['x2'] -= self.pan_delta_x
                finview['y1'] -= self.pan_delta_y
                finview['y2'] -= self.pan_delta_y
        else:
            center_x = int( orig_width / 2 ) - self.pan_delta_x
            center_y = int( orig_height / 2 ) - self.pan_delta_y
            #print("zoom factor:", self.zoom_factor, "finbbox:", finbbox )
            view_width = orig_width
            view_height = orig_height

            rect_wh_ratio = view_width / view_height
            widget_wh_ratio = rect_wh_ratio
            if widget != None:
                widget_width = widget.size().width()
                widget_height = widget.size().height()
                widget_wh_ratio = widget_width / widget_height
            if( widget_wh_ratio < rect_wh_ratio ):
                # fit to widget width
                finview['width']  = int( view_width / self.zoom_factor )
                finview['height'] = int( view_width / self.zoom_factor / widget_wh_ratio )
            else:
                # fit to widget height
                finview['height'] = int( view_height / self.zoom_factor )
                finview['width']  = int( view_height / self.zoom_factor * widget_wh_ratio )
            
            finview['x1'] = max( int(center_x  - ( finview['width']  / 2 )), 0 )
            finview['y1'] = max( int(center_y - ( finview['height'] / 2 )), 0 )
            finview['x2'] = finview['x1'] + finview['width']
            finview['y2'] = finview['y1'] + finview['height']
            if( finview['x2'] > orig_width ):
                finview['x1'] = max( finview['x1'] - ( finview['x2'] - orig_width ), 0 ) 
                finview['x2'] = orig_width
            if( finview['y2'] > orig_height ):
                finview['y1'] = max( finview['y1'] - ( finview['y2'] - orig_height ), 0 )
                finview['y2'] = orig_height
            #finview['x1'] -= self.pan_delta_x
            #finview['x2'] -= self.pan_delta_x
            #finview['y1'] -= self.pan_delta_y
            #finview['y2'] -= self.pan_delta_y

        self.current_finbbox_coords = finbbox
        self.current_finview_coords = finview
        #print("image_index", image_index, "fin_index0", fin_index0 )
        #print("finbbox", self.current_finbbox_coords)
        #print("zoom_factor", self.zoom_factor, "finview", self.current_finview_coords)

        local_bbox = {}
        for k in finbbox.keys():
            local_bbox[k] = finbbox[k]
        if( self.temp_bbox != None ):
            for k in self.temp_bbox.keys():
                local_bbox[k] = self.temp_bbox[k]
        

        cropped_pixmap = orig_pixmap.copy( finview['x1'], finview['y1'], finview['width'], finview['height'] )
        #if finview['x2'] 

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
                pen_width = int( 2.0 / self.zoom_ratio )
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

    def rbIsFinFunction(self):
        if( self.rbIsFinYes.isChecked() ):
            self.current_fin_record.is_fin = True
        else:
            self.current_fin_record.is_fin = False
        self.update_modification_info()
            
    def edtLocationEditedFunction(self,text):
        self.current_fin_record.location = text
        self.update_modification_info()

    def edtDolfinIDEditedFunction(self,text):
        return

    def edtDolfinIDEditFinishedFunction(self):
        new_finid = self.edtDolfinID.text()
        #print("text:", text, text[0:3])
        if new_finid == '':
            return
        if new_finid == self.finid_base_text:
            self.edtDolfinID.setText("")
            self.edtDolfinIDEditedFunction("")
            return
        if new_finid[0:3] != self.finid_base_text:
            self.edtDolfinID.setText("")
            self.edtDolfinIDEditedFunction("")
            return

        if new_finid not in self.finid_info.keys():
            self.add_new_finid_info(new_finid)

        #self.current_item.setData( self.current_fin_record.get_itemname_with_dolfin_id(), Qt.DisplayRole)
        fin_record = self.current_fin_record
        old_finid = fin_record.dolfin_id
        if old_finid != new_finid:
            self.process_finid_change( fin_record, new_finid, old_finid )
            fin_record.dolfin_id = new_finid

        self.update_modification_info()

        return

    def process_finid_change(self, fin_record, new_finid='', old_finid = ''):
        item1, item2 = fin_record.items

        icon_pixmap = QPixmap( self.finicon_hash[fin_record.get_finname()] )
        new_pixmap = self.write_finid_on_icon( icon_pixmap, new_finid )
        item1.setIcon(QIcon(new_pixmap))
        item2.setData( new_finid, Qt.DisplayRole )
        #item2.setText( new_finid )

        finname = fin_record.get_finname()
        #print( "process finid change", finname, old_finid, new_finid )

        if new_finid != '':
            new_fin_record_hash = self.finid_info[new_finid]['fin_record_hash']
            new_fin_record_hash[finname] = fin_record

            new_finname_list = self.finid_info[new_finid]['finname_list']
            new_finname_list.append( finname )

            self.update_toolbutton_icon( new_finid )

        if old_finid != '':
            old_fin_record_hash = self.finid_info[old_finid]['fin_record_hash']
            del old_fin_record_hash[finname]
            old_finname_list = self.finid_info[old_finid]['finname_list']
            old_finname_list.remove( finname )
            self.update_toolbutton_icon( old_finid )

        fin_record.dolfin_id = new_finid

    def edtObservedByEditedFunction(self,text):
        self.current_fin_record.observed_by = text
        self.update_modification_info()

    def edtCommentChangedFunction(self):
        text = self.edtComment.toPlainText()
        if( self.current_fin_record.comment != text):
            self.current_fin_record.comment = text
            self.update_modification_info()

    def edtModifiedByEditedFunction(self,text):
        self.current_modifier = self.current_fin_record.modified_by = text
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.current_fin_record.modified_on = now
        self.edtModifiedOn.setDateTime(QDateTime.fromString(now,"yyyy-MM-dd hh:mm:ss"))

    def update_modification_info(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.current_fin_record.modified_on = now
        self.edtModifiedOn.setDateTime(QDateTime.fromString(now,"yyyy-MM-dd hh:mm:ss"))

        if( self.current_modifier != '' ):
            self.edtModifiedBy.setText( self.current_modifier )
            self.edtModifiedByEditedFunction( self.current_modifier )

    def btnRenameIDFunction(self):
        curr_item = self.trFinIDTree.currentItem()
        if curr_item == None:
            return

        old_finid = self.trFinIDTree.currentItem().text(0)
        if( old_finid in DEFAULT_FINID_BUTTONS ):
            return

        new_finid = self.edtNewID.text()
        if new_finid in self.finid_info.keys() or new_finid == self.finid_base_text:
            return

        # 새 폴더, 버튼 추가 
        self.add_new_finid_info( new_finid )
        self.edtNewID.setText( self.finid_base_text)
        self.edtNewID.setCursorPosition( len(self.finid_base_text) )

        fin_record_hash = self.finid_info[old_finid]['fin_record_hash']
        finname_list = self.finid_info[old_finid]['finname_list'].copy()
        # item 처리
        for finname in finname_list:
            fin_record = fin_record_hash[finname]
            self.process_finid_change( fin_record, new_finid, old_finid )

        self.finid_info[old_finid]['fin_record_hash'] = {}
        self.finid_info[old_finid]['finname_list'] = []

        # button, folder 삭제
        self.remove_finid_info(old_finid)
        return

    def btnRemoveIDFunction(self):
        curr_item = self.trFinIDTree.currentItem()
        if curr_item == None:
            return
        old_finid = curr_item.text(0)
        if( old_finid == BTN_NOT_ASSIGNED ):
            return

        #fin_record = curr_item.data()

        #item 처리
        finname_list = self.finid_info[old_finid]['finname_list'].copy()
        for finname in finname_list:
            fin_record = fin_record_hash[finname]
            self.process_finid_change( fin_record, '', old_finid )

        self.finid_info[old_finid]['fin_record_hash'] = {}
        self.remove_finid_info(old_finid)
        self.trFinIDTree.setCurrentItem(self.top_folder)
        return

    def remove_finid_info(self, finid):
        # button, folder 삭제
        #print( "remove finid:["+str(finid)+"]")
        self.vbox.removeWidget(self.finid_info[finid]['button'])
        self.finid_info[finid]['button'].deleteLater()
        self.finid_info[finid]['button'] = None
        del self.finid_info[finid]['button']
        del self.finid_info[finid]['fin_record_hash']
        del self.finid_info[finid]
        items = self.trFinIDTree.findItems( finid, Qt.MatchContains)
        #print( "will remove:", items, "from", self.trFinIDTree )
        root = self.top_folder
        #print("root:", root, root.text(0))
        for i in range( root.childCount() ):
            #print("i:", i)
            child = root.child(i)
            if child != None:
                text = child.text(0)
                #print("child:", text)
                if text == finid:
                    #print("remove", text)
                    root.removeChild( child )
            #if 
        #for item in items:
        #    item.parent().removeChild( item )

    def btnIconZoomInFunction(self):
        #print("zoom in")
        if self.view_mode == ICON_VIEW:
            width = self.lstFinList.iconSize().width()
            new_width = min( width + 20, 200 )
            self.lstFinList.setIconSize( QSize( new_width, new_width ))

    def btnIconZoomOutFunction(self):
        if self.view_mode == ICON_VIEW:
        #print("zoom out")
            width = self.lstFinList.iconSize().width()
            new_width = max( width - 20 , 40 )
            self.lstFinList.setIconSize( QSize( new_width, new_width ))

    def setIconView(self):
        self.stackedWidget.setCurrentIndex(0)
        self.view_mode = ICON_VIEW
    def setCloseupView(self):
        self.stackedWidget.setCurrentIndex(1)
        self.view_mode = CLOSEUP_VIEW
    def btnViewToggleFunction(self):
        current_index = 1 - self.stackedWidget.currentIndex()
        self.view_mode = 1 - self.view_mode
        self.stackedWidget.setCurrentIndex(current_index)
        #self.stk_w.setCurrentIndex

    def btnSaveDataFunction(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        folder_name = self.working_folder.name
        save_path = str( self.working_folder.joinpath( folder_name + ".csv" ))

        with open(save_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            #print("images:", images )

            #i = 0
            for image_index in range( len( self.image_path_list ) ):
                #i += 1
                for fin_record in self.all_image_fin_list[image_index]:
                    if fin_record.image_width == 0:
                        image_width, image_height = imagesize.get(str(self.image_path_list[image_index]))
                        #print(width, height)
                        fin_record.image_width = image_width
                        fin_record.image_height = image_height
                    writer.writerow({'folder_name':fin_record.folder_name,'image_name': fin_record.image_name, 'image_width': fin_record.image_width,
                                     'image_height': fin_record.image_height,'class_id': int(fin_record.class_id), 
                                     'fin_index': fin_record.fin_index, 'center_x': fin_record.center_x, 'center_y': fin_record.center_y, 
                                     'width': fin_record.width, 'height': fin_record.height, 'confidence': fin_record.confidence,
                                     'is_fin': fin_record.is_fin, 'image_datetime': fin_record.image_datetime, 
                                     'location': fin_record.location, 'latitude': fin_record.latitude, 'longitude': fin_record.longitude,
                                     'map_datum': fin_record.map_datum, 'dolfin_id': fin_record.dolfin_id, 'observed_by': fin_record.observed_by, 
                                     'created_by': fin_record.created_by, 'created_on': fin_record.created_on,
                                     'modified_by': fin_record.modified_by, 'modified_on': fin_record.modified_on, 'comment': fin_record.comment})
        self.btnSaveFinsFunction2()
        QApplication.restoreOverrideCursor()

    def pickle_and_save_image_hash(self,image_hash,filepath):

        bytearray_hash = {}

        for k in image_hash.keys():
            if k[-4:] == '.JPG':
                continue
            q_image = image_hash[k]
            byte_array = QByteArray()
            # Bind the byte array to the output stream
            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.WriteOnly)
            # Save the data in png format
            q_image.save(buffer, "jpg", quality=95)
            bytearray_hash[k] = byte_array

        pickle.dump( bytearray_hash, open( filepath, "wb"))

    def load_and_unpickle_image_hash(self, filepath):
        image_hash = {}

        bytearray_hash = pickle.load( open( filepath, "rb" ) )
        
        for k in bytearray_hash.keys():
            byte_array = bytearray_hash[k]

            buffer = QBuffer(byte_array)
            buffer.open(QIODevice.ReadOnly)
            reader = QImageReader(buffer)
            img = reader.read()
            image_hash[k] = img
        return image_hash

    def btnSaveFinsFunction2(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)

        icondb_path = self.working_folder.joinpath( self.working_folder.name + ".icondb" )

        self.pickle_and_save_image_hash( self.finicon_hash, str( icondb_path ) )

        QApplication.restoreOverrideCursor()

    def btnSaveFinsFunction(self):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        fin_info_list = []


        result_dir = str( Path( self.working_folder ).joinpath( "result" ) )
        self.progressDlg = ProgressDialog()
        self.progressDlg.setModal(True)
        self.progressDlg.lblText.setText("Saving fin images from 0 of " + str( len( self.image_path_list ) ) + " files...")
        self.progressDlg.pbProgress.setValue( 0 ) 
        self.progressDlg.show()


        i = 0
        for img_idx in range( len( self.image_path_list ) ):

            i += 1
            self.progressDlg.pbProgress.setValue( int( ( i / float(len(self.image_path_list)) ) * 100 ) ) 
            self.progressDlg.lblText.setText("Saving fin images from " + str( i ) + " of " + str( len( self.image_path_list ) ) + " files...")
            self.progressDlg.update()
            QApplication.processEvents() 

            if( self.orig_pixmap_list[img_idx] == None ):
                img_path = self.working_folder.joinpath( self.image_path_list[img_idx] )
                pixmap = QPixmap(str(img_path))

            filepath_stem = str( Path(result_dir).joinpath( Path(self.image_path_list[img_idx]).stem ) )
            for fin_idx in range( len( self.all_image_fin_list[img_idx] ) ):
                fin_pixmap = self.get_cropped_fin_image( pixmap, img_idx, fin_idx )
                fin_img = fin_pixmap.toImage()
                fin_idx_str = "00" + str(fin_idx+1)
                filename = filepath_stem + "_" + fin_idx_str[-2:] + ".JPG"
                #fin_info = {}
                #fin_info['filename'] = filename
                #fin_info['image'] = fin_img
                #fin_info_list.append( fin_info )
                fin_img.save( filename )

        #store_many_lmdb( self.working_folder, fin_info_list )
        self.progressDlg.close()

        QApplication.restoreOverrideCursor()

    def reset_input_fields(self):
        self.edtFinIndex.setText('')
        self.edtConfidence.setText('')
        self.rbIsFinYes.setChecked(False)
        self.rbIsFinNo.setChecked(False)
        self.edtImageDateTime.setDateTime(QDateTime.fromString('1900-01-01 00:00:00',"yyyy-MM-dd hh:mm:ss"))
        self.edtLocation.setText('')
        self.edtLatitude.setText('')
        self.edtLongitude.setText('')
        self.edtMapDatum.setText('')
        self.edtDolfinID.setText('')
        self.edtObservedBy.setText('')
        self.edtCreatedBy.setText('')
        self.edtCreatedOn.setDateTime(QDateTime.fromString('1900-01-01 00:00:00',"yyyy-MM-dd hh:mm:ss"))
        self.edtModifiedBy.setText('')
        self.edtModifiedOn.setDateTime(QDateTime.fromString('1900-01-01 00:00:00',"yyyy-MM-dd hh:mm:ss"))
        wasBlocked = self.edtComment.blockSignals(True)
        self.edtComment.setPlainText('')
        self.edtComment.blockSignals(wasBlocked)

    def refresh_finview(self):
        fin_record = self.current_fin_record
        if fin_record == None:
            return
        image_index = self.current_image_index
        if image_index < 0:
            return
        fin_index0 = self.current_fin_index0
        image_path = self.image_path_list[image_index]
        item = self.current_item

        self.lblFinView.clear()

        if( self.orig_pixmap_list[image_index] == None ):
            self.orig_pixmap_list[image_index] = QPixmap(str(image_path))
        #orig_pixmap = QPixmap( str(self.image_path_list[image_index]))
        #print("refresh_finview zoom_factor:", self.zoom_factor)
        pixmap = self.get_cropped_fin_image( self.orig_pixmap_list[image_index], image_index, fin_index0, self.show_bbox, self.lblFinView )

        #icon = item.icon()
        #pixmap = QPixmap( icon.pixmap(icon.actualSize(QSize(256,256))) )

        pixmap2 = self.get_fit_pixmap_to_view( pixmap, self.lblFinView )
            
        zoom_factor = int( ( float(pixmap2.width()) / float(pixmap.width()) ) * 10 )
        #self.sldZoom.setValue( self.zoom_factor )
        #print("zoom:", zoom_factor)
        self.lblFinView.setPixmap(pixmap2)
        return

    def initialize_finid_info(self):

        key_list = list(self.finid_info.keys())
        for k in key_list:
            self.remove_finid_info(k)

        self.finid_info = {}
        self.finModel.removeRows( 0, self.finModel.rowCount() )

        self.trFinIDTree.clear()

        self.top_folder = QTreeWidgetItem(["All"])
        self.top_folder.setIcon( 0, QIcon("folder-icon.png") )
        self.trFinIDTree.insertTopLevelItem(0,self.top_folder)
        self.top_folder.setExpanded(True)

        for txt in DEFAULT_FINID_BUTTONS:
            self.add_new_finid_info( txt )


    def add_new_finid_info( self, fin_id ):
        if fin_id in self.finid_info.keys() or fin_id == self.finid_base_text:
            return None

        btn = QToolButton()
        btn.setText(fin_id)
        btn.setMinimumSize(self.BUTTON_WIDTH,self.BUTTON_HEIGHT)
        btn.clicked.connect(self.make_btnClicked(fin_id))

        key_list = list(self.finid_info.keys())

        i = 0

        if len(key_list) >= 2:
            #print(key_list)
            key_list.append(fin_id)
            key_list.remove(BTN_NOT_ASSIGNED)
            key_list.remove(BTN_NO_FIN)
            key_list.sort()
            #finid_list = sorted( key_list.append(fin_id) )
            index = key_list.index(fin_id)
            self.vbox.insertWidget(index+2,btn)
        else:
            self.vbox.addWidget(btn)

        item = QTreeWidgetItem(self.top_folder, [fin_id])
        item.setIcon( 0, QIcon("folder-icon.png") )

        self.finid_info[fin_id] = {} 
        self.finid_info[fin_id]['button'] = btn
        self.finid_info[fin_id]['fin_record_hash'] = {}
        self.finid_info[fin_id]['finname_list'] = []
        self.finid_info[fin_id]['tree_item'] = item
        self.sort_finid()

    def sort_finid(self):
        removed_items = []
        for i in range(2):
            item = self.top_folder.child(0)
            removed_items.append(item)
            self.top_folder.removeChild(item)
        self.top_folder.sortChildren(0,Qt.AscendingOrder)
        for i in range(2):
            self.top_folder.insertChild(i,removed_items[i])

    def closeEvent(self, event):
        if( self.mainview_dlg != None ):
            self.mainview_dlg.close()

if __name__ == "__main__" :
    #QApplication : 프로그램을 실행시켜주는 클래스
    app = QApplication(sys.argv) 

    #WindowClass의 인스턴스 생성
    myWindow = DolfinNoteWindow() 

    #프로그램 화면을 보여주는 코드
    myWindow.show()

    #프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()
