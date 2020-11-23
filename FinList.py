from PIL import Image
import pickle
import os
from os import listdir
from os.path import isfile, join
from pathlib import Path
import csv
from DolfinRecord import DolfinRecord, fieldnames
from datetime import datetime

basedir = "D:/Dropbox/DolFinID/monitoring_2016"
basepath = Path( basedir )
finbasepath = basepath.joinpath( "fins" )

dir_list = [f for f in listdir(basedir)]

path_list = []

for dir in dir_list:
    path_list.append( basepath.joinpath( dir ) )

for p in path_list:
    csv_path = p.joinpath( p.name + ".csv" )
    icondb_path = p.joinpath( p.name + ".icondb" )
    #finicon_hash = load_and_unpickle_image_hash( icondb_path )
    print( csv_path )

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
            cropped_image = current_image.crop( ( x1, y1, x2, y2 ) )
            resized_image = cropped_image.resize( ( 200, 200 ) )

            date_time_obj = datetime.strptime(fin_record.image_datetime, '%Y-%m-%d %H:%M:%S')
            yyyymmdd = date_time_obj.strftime( '%Y%m%d')


            finpath = finbasepath.joinpath( fin_record.dolfin_id )
            if not os.path.isdir(str(finpath)):
                print("making path", str(finpath))
                os.makedirs(str(finpath))

            finfilepath_stem = str( Path(finpath).joinpath( yyyymmdd + '_' + image_path.stem ) )

            fin_index0 = int(row['fin_index']) - 1
            fin_idx_str = "00" + row['fin_index']
            icon_filepath = Path( finfilepath_stem + "_" + fin_idx_str[-2:] + ".JPG" )
            print( icon_filepath)
            resized_image.save( str( icon_filepath ) )
            #exit()

            #icon_filename = icon_filepath.name

