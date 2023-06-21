import flask
from flask_cors import CORS, cross_origin
import cv2
import face_recognition
import pickle
import numpy as np
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
import firebase_admin
from flask import request
from datetime import datetime

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred,{
    "databaseURL" : "https://faceattendancerealtime-32bb4-default-rtdb.firebaseio.com/",
    "storageBucket":"faceattendancerealtime-32bb4.appspot.com"})

app = flask.Flask(__name__)

CORS(app)
app.config['CORS_HEADER'] = "Content-Type"

student_list = {'date':str(datetime.now().date())}  # danh sách các học viên đã được điểm danh trong hôm nay
date = str(datetime.now().date())
if student_list['date'] != date:
    student_list['date'] = date
id = None

@app.route("/create_database", methods=['POST', 'GET'])
@cross_origin(origin='*')
def open_file():
    ref = db.reference("Students")
    id = request.args.get('id')
    img_student = []
    file = 'encodefile.p'
    bucket = storage.bucket()
    blob = bucket.get_blob(f'Images/{id}.jpg')
    array = np.frombuffer(blob.download_as_string(), np.uint8)
    imgStudent = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)

    imgStudent = cv2.cvtColor(imgStudent, cv2.COLOR_BGR2RGB)
    new = open(file, 'wb')
    encode = face_recognition.face_encodings(imgStudent)[0]
    img_student.append(encode)
    encode_Known_With_Id = [img_student, id]
    pickle.dump(encode_Known_With_Id, new)
    new.close()
    name = request.args.get('Name')
    phone = request.args.get('Phone')
    Skill = 'Beginner'
    Slots = 1
    data = {id:{
                'Name': name,
                'Slots': Slots, 
                'Skill': Skill,
                'Phone': phone}}
    for key, value in data.items():
        ref.child(key).set(value)
    return "sucessful"


@app.route('/checkin', methods=['POST', 'GET'])
@cross_origin(origins='*')
def test_load():
    global student_list
    global id
    global name
    file = open('encodefile.p', 'rb')
    encodeList_with_Id = pickle.load(file)
    file.close()
    encodeList, studentId = encodeList_with_Id

    name = request.args.get('Name')
    bucket = storage.bucket()
    blob = bucket.get_blob(f'Checkins/{name}.jpg')
    image = np.frombuffer(blob.download_as_string(), np.uint8)
    img = cv2.imdecode(image, cv2.COLOR_BGRA2RGB)

    faceCurFrame = face_recognition.face_locations(img)
    encodeCurrentFrame = face_recognition.face_encodings(img, faceCurFrame)
        
    for encodeFace in encodeCurrentFrame:
        matches = face_recognition.compare_faces(encodeList, encodeFace)
        faceDis = face_recognition.face_distance(encodeList, encodeFace)
        matchesIndex = np.argmin(faceDis)
        if matches[matchesIndex]:
            id = studentId[matchesIndex]
            studentInfo = db.reference(f'Students/{id}').get()
            studentAll = studentInfo.copy()
            studentAll['ImgPath'] = f'Checkins/{id}.jpg'
            student_list[id] = studentAll
            return studentInfo

@app.route('/update', methods=['POST', 'GET'])
@cross_origin(origins='*')
def update():
    global id
    global name
    studentInfo = db.reference(f'Students/{id}').get()
    studentInfo['Slots'] +=1
    ref = db.reference('Students')
    ref.child(id).set(studentInfo)
    bucket = storage.bucket()
    blob = bucket.blob(f'Checkins/{name}.jpg')
    blob.delete()
    return "Successful"

@app.route('/list_student', methods=['POST', 'GET'])
@cross_origin(origins='*')
def list_student():
    global student_list
    return student_list


if __name__=="__main__":
    app.run(host='0.0.0.0', port='8000')