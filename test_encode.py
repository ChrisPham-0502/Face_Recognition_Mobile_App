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

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred,{
    "databaseURL" : "https://faceattendancerealtime-32bb4-default-rtdb.firebaseio.com/",
    "storageBucket":"faceattendancerealtime-32bb4.appspot.com"})

app = flask.Flask(__name__)

CORS(app)
app.config['CORS_HEADER'] = "Content-Type"

student_list = {'date':None}
'''
@app.route('/upload_image', methods=['POST'])
@cross_origin('*')
def base64_to_image():
    form = str(request.args.get('form'))
    # Remove the data:image/png;base64 prefix
    base64_string = form.replace('data:image/png;base64,', '')

    # Decode the base64 string
    image_data = base64.b64decode(base64_string)

    cv2.imshow('result', image_data)
    cv2.waitKey(0)
    return "Successful"
'''
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
    #global student_list
    counter = 0
    id = 0
    studentInfo = None
    '''
    if studentInfo['date'] != time.localtime()[0:3]:
        studentInfo.clear()
        studentInfo['date'] = time.localtime()[0:3]
        '''
    try:
        file = open('encodefile.p', 'rb')
        encodeList_with_Id = pickle.load(file)
        file.close()
        encodeList, studentId = encodeList_with_Id
        cam = cv2.VideoCapture(0)
        while True:
            '''
            success, image = cam.read()
            cv2.imshow('Result', image)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            '''
            name = request.args.get('Name')
            bucket = storage.bucket()
            blob = bucket.get_blob(f'Checkins/{name}.jpg')
            image = np.frombuffer(blob.download_as_string(), np.uint8)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            faceCurFrame = face_recognition.face_locations(image)
            encodeCurrentFrame = face_recognition.face_encodings(image, faceCurFrame)
            for encodeFace, faceloc in zip(encodeCurrentFrame, faceCurFrame):
                matches = face_recognition.compare_faces(encodeList, encodeFace)
                faceDis = face_recognition.face_distance(encodeList, encodeFace)
                matchesIndex = np.argmin(faceDis)
                if matches[matchesIndex]:
                    id = studentId[matchesIndex]
                    if counter==0:
                        counter=1

            if counter!=0:
                    if counter == 1:
                        studentInfo = db.reference(f'Students/{id}').get()
                        imgStudent[id] = studentInfo['Name']
                        student_list[f'{id}'] = studentInfo['Name']
                        if cv2.waitKey(10)==ord('q'):
                            cv2.destroyAllWindows()
                            studentInfo['Slots']+=1
                            db.reference(f'Students/{id}').child('Slots').set(studentInfo['Slots'])
                            return studentInfo
    except:
        return "Failed"
    
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