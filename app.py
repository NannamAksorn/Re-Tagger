import os
import csv
import cv2
import glob
from PIL import Image
from datetime import datetime, timedelta

font                   = cv2.FONT_HERSHEY_SIMPLEX
bottomLeftCornerOfText = (10,20)
fontScale              = 0.4
fontColor              = (255,255,255)
lineType               = 1
                
key_files = glob.glob('key/*/*.csv')
key_files.sort()
#video_files = glob.glob('/Volumes/MIMAMORI_101/FFOutput/video/*.mp4')
#video_file = video_files[0]

def getFrame(myFrameNumber = 0):
    '''return cv2 frame at frame number'''
    cap.set(cv2.CAP_PROP_POS_AVI_RATIO,1)
    totalFrames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    if myFrameNumber >= 0 and myFrameNumber <= totalFrames:
        cap.set(cv2.CAP_PROP_POS_FRAMES,myFrameNumber)
    return totalFrames
def clean_data(csv_data):
    temp = csv_data.copy()
    temp.sort(key = lambda x: int(x[0]))
    for i in range(len(temp)):
        try:
            while temp[i][1] == temp[i+1][1]:
                if i+1 == len(temp) -1: 
                    break
                del(temp[i+1])
        except Exception as e:
            pass
    return temp
def parse_date(filePath):
    '''parse video date from filename'''
    filePath = os.path.basename(filePath)
    if filePath.endswith('csv'):
        date_str = filePath[18:33]
        csv_date = datetime.strptime(date_str, '%Y%m%d_%H%M%S')
        csv_date  = csv_date.replace(year=csv_date.year-543)
        return csv_date
    else:
        date_str = filePath[4:-4]
        video_date = datetime.strptime(date_str, '%Y%m%d_%H-%M-%S')
        return video_date
        
def get_delta_frame(csv_date, video_date):
    delta = csv_date - video_date
    delta_frame = delta.total_seconds() * 30
    return delta_frame
def isBetween(csv_date, videofile):
    start = parse_date(videofile)
    if csv_date < start:
        return False
    
    cap = cv2.VideoCapture(video_file)
    cap.set(cv2.CAP_PROP_POS_AVI_RATIO,1)
    duration = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
    end = start + timedelta(seconds=duration)

    if start <= csv_date <= end:
        return True
    else:
        return False
total_tag = 0
for key_file in key_files:
    with open(key_file, 'r') as csv_file:
        reader = csv.reader(csv_file)
        csv_data = list(reader)
    temp = csv_data.copy()
    temp = clean_data(temp)
    csv_date = parse_date(key_file)
    
    #get videofiles
    room_number = key_file.split('/')[1][:3]
    next_date = csv_date - timedelta(days=1)
    m = csv_date.month
    mdd = '{}{:02d}'.format(csv_date.month,csv_date.day)
    mdd2 = '{}{:02d}'.format(next_date.month,next_date.day)
    path = '/Volumes/MIMAMORI_101/FFOutput/video/{}-20160{}*.mp4'.format(room_number,mdd)
    path2 = '/Volumes/MIMAMORI_101/FFOutput/video/{}-20160{}*.mp4'.format(room_number,mdd2)
    video_files = glob.glob(path) + glob.glob(path2)
    video_file = video_files[0]
    for index, tag in enumerate(temp):
        if tag[1] == '3' and index != len(temp)-1:
            print(tag)
            total_tag += 1
            #get Video
            csv_date_new = csv_date + timedelta(seconds=int(tag[0])/30)
            if not isBetween(csv_date_new, video_file):
                for video_file in video_files:
                    if isBetween(csv_date_new, video_file):
                        break
            try:
                #get frame
                cap = cv2.VideoCapture(video_file)
                frame = getFrame(get_delta_frame(csv_date, parse_date(video_file)) + int(tag[0]))
                img = cap.read()[1]

                cv2.putText(img,'room:{}|{} datetime:{}'.format(room_number,video_file.split('/')[5][:3],str(csv_date_new)), 
                    bottomLeftCornerOfText, 
                    font, 
                    fontScale,
                    fontColor,
                    lineType)
                cv2.imshow('frame', img)
                k = cv2.waitKey(0)
                for i in range(6):
                    if k == ord(str(i)):
                        new_tag = str(i)
                        print(i)
                cap.release()
                #new_tag = input('Enter new tag@{}: '.format(csv_date))
                if new_tag in ('0', '1', '2', '3', '4','5'):
                    temp[index][1] = new_tag
                    if index != 0 and len(temp[index-1][1]) == 2:
                        if temp[index-1][1][0] == new_tag:
                            temp[index-1][1] = new_tag    
                        else:
                            temp[index-1][1] = temp[index-1][1][0] + new_tag
                    if index != len(temp)-1 and len(temp[index+1][1]) == 2:
                        if temp[index+1][1][1] == new_tag:
                            temp[index+1][1] = new_tag    
                        else:
                            temp[index+1][1] = new_tag + temp[index+1][1][1]
            except Exception:
                pass
    temp = clean_data(temp)
    with open(key_file + '_edit.csv', 'w') as resultFile:
        wr = csv.writer(resultFile,dialect='excel')
        for row in temp:
            wr.writerow(row)

    print('write ',key_file, 'edit')
print(total_tag)