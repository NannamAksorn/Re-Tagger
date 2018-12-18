import os
import csv
import cv2
import glob
import io
import sys
import numpy as np
from matplotlib import pyplot as plt
from PIL import Image
from datetime import datetime, timedelta



font                   = cv2.FONT_HERSHEY_SIMPLEX
bottomLeftCornerOfText = (20,40)
fontScale              = 0.4
fontColor              = (255,255,255)
lineType               = 1

VIDEO_PATH = 'video'
CSV_PATH = 'key2/*'
SENDAT_PATH = 'sendat_data/'

key_files = glob.glob('{}/*sendat.csv'.format(CSV_PATH))
key_files.sort()

def estimate_pos(start, end):
    gap = (np.mean(norm_w0[start:end]) - np.mean(norm_w1[start:end]))/np.mean(norm_w1[start:end])
    if (gap < -0.15):
        pos = 'lelf (4)'
    elif(gap > 0.15):
        pos = 'right (5)'
    else:
        pos = 'center (3)'
    print(pos)
    print(gap)
    return 'p:' + pos + ' | dw:' +str(gap)[:7]

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
    out_frame = np.zeros([480, 1280, 3], dtype = np.uint8)
#     sendat_files = glob.glob(SENDAT_PATH + key_file.split('/')[-1][:-4])
    sendat_files = glob.glob(SENDAT_PATH + '*.sendat')
    print(SENDAT_PATH + key_file.split('/')[-1][:-4])
    if len(sendat_files) <= 0:
        continue
    sendat_file = np.fromfile(sendat_files[0], np.uint8)
    p0 = []
    p1 = []
    w0 = []
    w1 = []
    for i in range(len(sendat_file) // 45):
        index = i * 45
        p_temp = sendat_file[index + 10 : index + 18]
        p_sub = [p - 127 for p in p_temp]
        p0.extend(p_sub)

        w_temp = sendat_file[index + 18 : index + 26]
        w0.extend(w_temp)

        p_temp = sendat_file[index + 26 : index + 34]
        p_sub = [p - 127 for p in p_temp]
        p1.extend(p_sub)

        w_temp = sendat_file[index + 34 : index + 42]
        w1.extend(w_temp)
    norm_p0 = p0 / np.linalg.norm(p0)
    norm_w0 = w0 / np.linalg.norm(w0)
    norm_p1 = p1 / np.linalg.norm(p1)
    norm_w1 = w1 / np.linalg.norm(w1)
    
    temp = csv_data.copy()
    temp = clean_data(temp)
    csv_date = parse_date(key_file)
   
    #get videofiles
    room_number = key_file.split('/')[-2][:3]
    next_date = csv_date - timedelta(days=1)
    m = csv_date.month
    mdd = '{}{:02d}'.format(csv_date.month,csv_date.day)
    mdd2 = '{}{:02d}'.format(next_date.month,next_date.day)
    path = '{}/{}-20160{}*.mp4'.format(VIDEO_PATH,room_number,mdd)
    path2 = '{}/{}-20160{}*.mp4'.format(VIDEO_PATH,room_number,mdd2)
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
                ret, img = cap.read()
                if not ret: continue
                img = cv2.resize(img, (640,480))
                
                #get data
                mid = int(tag[0])
                if mid < 60 : mid = 60
                elif mid > len(p0)-60 : mid = len(p0) - 60 

                print(mid)   
                start = mid - 60
                end = mid + 60
                x_ = np.arange(start,end,1)
                plt.subplot(211)
                plt.xticks([])
                plt.title(estimate_pos(start, end))
                plt.axvline(mid, color='black')
                plt.plot(x_,norm_p0[start:end],color = 'red', label='P0')
                plt.plot(x_,norm_p1[start:end],color = 'blue',label='P1')
                plt.legend()
                plt.subplot(212)
                plt.xticks(np.arange(start,end+1,30))
                plt.axvline(mid, color='black')
                plt.plot(x_,norm_w0[start:end], color = 'red', label = 'W0')
                plt.plot(x_,norm_w1[start:end], color = 'blue', label = 'W1')
                plt.legend()

                buf = io.BytesIO()
                plt.savefig(buf, format='jpg',dpi=300)
                buf.seek(0)
                im = Image.open(buf)
                im = im.resize((640,480))
                plot = np.array(im)
                plt.gcf().clear()
                
                out_frame[:480,640:,:] = plot
                buf.close()
                
                cv2.putText(img,'room:{}|{} datetime:{}'.format(room_number,video_file.split('/')[-1][:3],str(csv_date_new)), 
                    bottomLeftCornerOfText, 
                    font, 
                    fontScale,
                    fontColor,
                    lineType)
                out_frame[:480,:640,:] = img
                cv2.imshow('frame', out_frame)
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
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
    temp = clean_data(temp)
    with open(key_file + '_edit.csv', 'w') as resultFile:
        wr = csv.writer(resultFile,dialect='excel')
        for row in temp:
            wr.writerow(row)

    print('write ',key_file, 'edit')
print(total_tag)