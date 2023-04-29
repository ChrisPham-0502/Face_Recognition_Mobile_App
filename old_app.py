import cv2
import pickle
import os
import face_recognition
import numpy as np
import cvzone
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred,{
    "databaseURL" : "https://faceattendancerealtime-32bb4-default-rtdb.firebaseio.com/",
    "storageBucket":"faceattendancerealtime-32bb4.appspot.com"
})

bucket = storage.bucket()

cam = cv2.VideoCapture(0)
'''
Trong hàm set(), tham số đầu tiên là các thuộc tính của VideoCapture, tham số thứ hai là giá trị tương ứng thuộc tính 
mà bạn muốn thiết lập. Một số thuộc tính tham số đầu tiên:
+ Chiều rộng khung hình: '3'
+ Chiều cao khung hình: '4'
'''
cam.set(3,731)  # Set up chiều rộng
cam.set(4,930)  # Set up chiều dài

imgBackground = cv2.imread("Resources/background1.jpg")

folderModepath = "Resources/Modes"
Modepath = os.listdir(folderModepath)
imgMode_list = []
for path in Modepath:
      imgMode_list.append(cv2.imread(os.path.join(folderModepath, path)))

# Mở file encode
file = open("encodefile.p", 'rb')
encodeList_with_Id = pickle.load(file)
file.close()
encodeList, studentID = encodeList_with_Id
print(studentID)

counter = 0
id = 0
studentInfo = None
imgStudent = []

while True:
    success, image = cam.read()

    imgS = cv2.resize(image, (0,0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    faceCurFrame = face_recognition.face_locations(imgS)
    encodeCurrentFrame = face_recognition.face_encodings(imgS, faceCurFrame)
    '''
    r = cv2.selectROI(imgBackground)
    Hàm trên giúp lựa chọn vùng mà ta muốn biết tọa độ. 
    Bước 1: Chạy camera
    Bước 2: vẽ hình chữ nhật vùng mà bạn muốn bằng cách kéo + thả chuột
    Bước 3: Nhấn Enter, hàm sẽ trả về 1 tuple chứa các tham số
    r = (góc trên bên trái x, góc trên bên trái y, chiều rộng, chiều cao)
    '''
    r = (79, 80, 576, 578)
    '''
    Vì máy của mình không thể tự scale khuôn mặt về kích thước khung hình index trong background được nên mình sẽ scale lại như hàm dưới.
    Nếu máy các bạn có thể chạy mà không cần dòng 28 thì càng tốt, còn nếu máy báo lỗi thì có thể thêm vô.'''
    image = cv2.resize(image, (578, 576))  
    imgBackground[r[1]:r[1]+r[2], r[0]:r[0]+r[3]] = image

    for encodeFace, faceloc in zip(encodeCurrentFrame, faceCurFrame):
        matches = face_recognition.compare_faces(encodeList, encodeFace)
        faceDis = face_recognition.face_distance(encodeList, encodeFace)

        matchesIndex = np.argmin(faceDis)
        if matches[matchesIndex]:
            #print("Match successful!")
            y1, x2, y2, x1 = faceloc
            y1, x2, y2, x1 = y1*4, x2*4, y2*4, x1*4
            bbox = (79+x1,80+y1, x2-x1, y2-y1)
            imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)
            id = studentID[matchesIndex]
            if counter == 0:
                counter = 1
        else:
            print("Match failed!")
    if counter !=0:
        if counter == 1: 
            # Lấy data từ database xuống
            studentInfo = db.reference(f'Students/{id}').get()
            print(studentInfo)
            # Lấy ảnh xuống
            blob = bucket.get_blob(f'Images/{id}.jpg')
            array = np.frombuffer(blob.download_as_string(), np.uint8)
            imgStudent = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)
            # Cập nhật số buổi học
            ref = db.reference(f'Students/{id}')
            studentInfo['Slots'] +=1
            ref.child('Slots').set(studentInfo['Slots'])
        '''
        Khi chèn nội dung vào ảnh theo tọa độ, máy sẽ biểu diễn dưới dạng tọa độ ngược như sau: 
      0 +------------------------->x
        |
        |  +-------------------+     
        |  |                   |
        |  |      Nội dung     |
        |  |                   |
        |  +-------------------+
        |
        V 
        y
        Vậy nên y càng tăng thì nội dung sẽ càng di chuyển xuống và ngược lại.
        '''
        # Ghi tên
        cv2.putText(imgMode_list[1], f'Name: {studentInfo["Name"]}', (19,441), cv2.FONT_HERSHEY_SCRIPT_COMPLEX, 1, (255,255,255), 1) 
        # Ghi số buổi học
        cv2.putText(imgMode_list[1], f'Slots: {str(studentInfo["Slots"])}', (19,500), cv2.FONT_HERSHEY_SCRIPT_COMPLEX, 1, (255,255,255), 1)  
        # Ghi kĩ năng
        cv2.putText(imgMode_list[1], f'Skill: {studentInfo["Skill"]}', (19,559), cv2.FONT_HERSHEY_SCRIPT_COMPLEX, 1, (255,255,255), 1) 
        # Ghi sđt phụ huynh
        cv2.putText(imgMode_list[1], f'Phone: {studentInfo["Phone"]}', (19,618), cv2.FONT_HERSHEY_SCRIPT_COMPLEX, 1, (255,255,255), 1)  
        counter+=1   
        # Dán ảnh vào kết quả
        imgStudent = cv2.resize(imgStudent, (347,327))
        imgMode_list[1][50:50+327, 120:120+347] = imgStudent

    cv2.imshow("Background", imgBackground)
    if cv2.waitKey(10) == ord('q'):
        cv2.destroyWindow("Background")
        cv2.imshow("Mode", imgMode_list[0])
        cv2.waitKey(2000)
        cv2.destroyWindow("Mode")
        cv2.imshow("Result", imgMode_list[1])
        cv2.waitKey(0)
        break
