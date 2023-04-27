import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred,{
    "databaseURL" : "https://faceattendancerealtime-32bb4-default-rtdb.firebaseio.com/"
})

ref = db.reference("Students")

data = {
    "H050203":{
            "Name":"Phạm Anh Huy",
            "Slots": 4,
            "Skill": "Back snake",
            "Phone": "0989249973"
            },
    "T211003":{
            "Name":"Phạm Anh Thư",
            "Slots":6,
            "Skill": "Back stroll",
            "Phone":"0832432534"
            },
    "T221003":{
            "Name":"Nguyễn Hữu Tài",
            "Slots": 7,
            "Skill": "Cross Nelson",
            "Phone":"0565676856"
    }
}
    
for key, value in data.items():
    ref.child(key).set(value)