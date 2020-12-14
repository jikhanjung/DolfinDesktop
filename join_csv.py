import os
import sys
import glob
from pathlib import Path
import csv
import imagesize

from DolfinRecord import DolfinRecord, fieldnames

if len(sys.argv) != 4:
    exit()

working_folder = Path(sys.argv[1])
basefile = sys.argv[2]
additionalfile = sys.argv[3]

print('Number of arguments:', len(sys.argv), 'arguments.')
print('Argument List:', str(sys.argv))

csv_path = [working_folder.joinpath(basefile), working_folder.joinpath(additionalfile)]
new_csv_path = working_folder.joinpath(str(Path(basefile).stem+"_new.csv"))
all_image_fin_list = [[],[]]
image_name_list = [[],[]]
new_image_fin_list = []
new_image_name_list = []

for csv_idx in range(len(csv_path)):
    with open(str(csv_path[csv_idx]), newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        row_count=0
        prev_image_name = ''
        image_index = 0
        for row in reader:
            #print(row)
            row_count+=1
            #if row_count==20:
            #    exit()
            fin_record = DolfinRecord(row)
            print(image_index, row_count, "is_fin", row['is_fin'], fin_record.is_fin)
            image_name = fin_record.image_name

            if image_name != prev_image_name:
                image_name_list[csv_idx].append(image_name)
                prev_image_name = image_name
                image_index = image_name_list[csv_idx].index(image_name)
                all_image_fin_list[csv_idx].append([])

            all_image_fin_list[csv_idx][image_index].append(fin_record)

prev_image_index = -1
image_index1 = -1
image_index2 = -1

for image_index1 in range(len(image_name_list[0])):
    image_name = image_name_list[0][image_index1]
    print("image name", image_name)
    prev_image_index2 = image_index2

    if image_name in image_name_list[1]:
        image_index2 = image_name_list[1].index(image_name)
    else:
        print("no such image in 2nd csv", image_name)
        #image_index2 = -1
    if prev_image_index2 + 1 < image_index2:
        print("missing image_index2", prev_image_index2, image_index2)
        for idx2 in range(prev_image_index2+1, image_index2):
            print("missing image", image_name_list[1][idx2])
            new_image_name_list.append(image_name_list[1][idx2])
            new_image_fin_list.append(all_image_fin_list[1][idx2])
    new_image_name_list.append(image_name_list[0][image_index1])
    new_image_fin_list.append(all_image_fin_list[0][image_index1])

for i in range(50):
    print(image_name_list[0][i], len(all_image_fin_list[0][i]), image_name_list[1][i], len(all_image_fin_list[1][i]), new_image_name_list[i], len(new_image_fin_list[i]))


print(new_csv_path)
with open(new_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for image_index in range(len(new_image_name_list)):
        #i += 1
        for fin_record in new_image_fin_list[image_index]:
            fin_record.image_width = 4928
            fin_record.image_height = 3280
            writer.writerow(fin_record.get_info())
