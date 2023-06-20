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

@app.route("/create_database", methods=['POST', 'GET'])
@cross_origin(origin='*')
def open_file():
    ref = db.reference("Students")
    id = request.args.get('id')
    img_student = []
    file = 'encode.p'
    bucket = storage.bucket()
    blob = bucket.get_blob(f'Images/{id}.jpg')
    array = np.frombuffer(blob.download_as_string(), np.uint8)
    imgStudent = cv2.imdecode(array, cv2.COLOR_BGRA2BGR)
    try:
        new = open(file, 'wb')
        img = cv2.cvtColor(imgStudent, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
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
    except:
        return 'failed'

@app.route('/checkin', methods=['POST', 'GET'])
@cross_origin(origins='*')
def test_load():
    global student_list
    Json = {"StudentInfo":None,
            "StudentList":None}   # Dict trả về chứa 2 dict con: dict 1 chứa thông tin học viên, dict 2 chứa danh sách các học viên đã điểm danh

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
            student_list[id] = studentInfo['Name']
            Json['StudentInfo'] = studentInfo
            Json['StudentList'] = student_list
            return Json
    
@app.route('/update', methods=['POST', 'GET'])
@cross_origin(origins='*')
def update_info():
    global imgStudent
    id = request.args.get('id')
    skill = request.args.get('skill')
    studentInfo = db.reference(f'Students/{id}').get()
    studentInfo['Skill'] = skill

@app.route('/student_info', methods=['POST', 'GET'])
@cross_origin(origins='*')
def info():
    global student_list
    return student_list

if __name__=="__main__":
    app.run(host='0.0.0.0', port='8000')