import os
from datetime import datetime

from firebase import Firebase
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import initialize_app


class UserAccess:
    config = \
        {
            "apiKey": "AIzaSyDOTg1HlOHMzRf47ze3OIIVBrZhIhNz7kY",
            "authDomain": "dafnaproject-bcf0f.firebaseapp.com",
            "databaseURL": "https://dafnaproject-bcf0f.firebaseio.com",
            "storageBucket": "dafnaproject-bcf0f.appspot.com"
            # "serviceAccount": "path/to/serviceAccountCredentials.json"
        }
    __instance = None

    @staticmethod
    def getInstance():
        """ Static access method. """
        if UserAccess.__instance is None:
            UserAccess()
        return UserAccess.__instance

    def __init__(self):
        """ Virtually private constr
        uctor. """
        if UserAccess.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            UserAccess.__instance = self
            firebase_obj = Firebase(self.config)  # connect to fire base by config
            # Gets a reference to the auth service
            self.auth = firebase_obj.auth()  # create an authentication connection to the firebase
            os.chdir(os.path.dirname(__file__))
            path = os.getcwd()
            initialize_app(
                credentials.Certificate(path + r'\dafnaproject-bcf0f-firebase-adminsdk-pvlxz-fc63fe5ca5.json'))
            self.database = firestore.client()
            self.sign_in = False

    def check_profile(self, email, passw):
        # and false if not
        try:
            # tries to log the user in (checks if the email and password exist in the database)
            self.auth.sign_in_with_email_and_password(email, passw)
            self.sign_in = True
            return True, ''  # the username and password exist
        except Exception as ex:
            # if there was an exception it means that the login try failed and the email and password don't exist
            ex = str(ex).split(':')[6]
            return False, ex.split(',')[0]

    def add_profile(self, u1):
        docs = self.database.collection('users').where("email", "==", u1.email).get()
        if docs:
            return False, 'email already used'
        valid, err = self.check_profile(u1.email, u1.password)
        if not valid:
            try:
                self.auth.create_user_with_email_and_password(u1.email, u1.password)
                self.auth.sign_in_with_email_and_password(u1.email, u1.password)
                userId = self.auth.current_user.get('localId')
                user_doc_ref = self.database.collection('users').document(userId)
                user_doc_ref.set({
                    'name': u1.name,
                    'rooms': u1.rooms,
                    'email': u1.email
                })
                self.sign_in = False
                return True, ''
            except Exception as ex:
                ex = str(ex).split(':')[6]
                return False, ex.split(',')[0]
        return False, 'user is already exist'

    def getUserName(self):
        if self.sign_in:
            userId = self.auth.current_user.get('localId')
            user_doc_ref = self.database.collection('users').document(userId)
            return user_doc_ref.get(field_paths={'name'}).to_dict().get('name')
        return None

    def get_name(self, userId):
        dict = self.database.collection('users').document(userId).get().to_dict()
        return dict['name']

    def getUserRooms(self):
        if self.sign_in:
            userId = self.auth.current_user.get('localId')
            user_doc_ref = self.database.collection('users').document(userId)
            return user_doc_ref.get(field_paths={'rooms'}).to_dict().get('rooms')
        return None

    def get_email(self):
        if self.sign_in:
            userId = self.auth.current_user.get('localId')
            user_doc_ref = self.database.collection('users').document(userId)
            return user_doc_ref.get(field_paths={'email'}).to_dict().get('email')
        return None

    def get_passw(self):
        if self.sign_in:
            userId = self.auth.current_user.get('localId')
            user_doc_ref = self.database.collection('users').document(userId)
            return user_doc_ref.get(field_paths={'passw'}).to_dict().get('passw')
        return None

    def get_room_participants(self, doc_id):
        dict = self.database.collection('rooms').document(doc_id).get().to_dict()
        return dict['users']

    def add_message(self, username, message, roomId):
        try:
            user_doc_ref = self.database.collection('messages').document(roomId)
            item = {
                datetime.now().strftime("%Y%m%d %H:%M:%S"):
                {
                    'username': username,
                    'message': message,
                }
            }
            user_doc_ref.update(item)
            return True
        except Exception as ex:
            print("Error - ", ex)
            return False

    def get_chat_history(self, doc_id):
        dict = self.database.collection('messages').document(doc_id).get().to_dict()
        del dict['room']
        return dict

    def add_room(self, doc_id):
        if self.sign_in:
            userId = self.auth.current_user.get('localId')
            user_doc_ref = self.database.collection('users').document(userId)
            dict = self.database.collection('rooms').document(doc_id).get().to_dict()
            room = dict["room"]
            self.database.collection('rooms').document(doc_id).update({"users": firestore.firestore.ArrayUnion([userId])})
            room = room.replace(" ", "_")
            dict = {room: doc_id}
            user_doc_ref.update({"rooms": dict})

    def delete_room(self, doc_id):
        dict = self.database.collection('rooms').document(doc_id).get().to_dict()
        users = dict['users']
        for user in users:
            self.database.collection('users').document(user).update({"rooms": firestore.firestore.ArrayRemove([doc_id])})
        self.database.collection('messages').document(doc_id).delete()
        self.database.collection('rooms').document(doc_id).delete()

    def set_admin(self, doc_id):
        userId = self.auth.current_user.get('localId')
        dict = {'admin': userId}
        self.database.collection('rooms').document(doc_id).update(dict)

    def am_i_admin(self, doc_id):
        userId = self.auth.current_user.get('localId')
        user_doc_ref = self.database.collection('rooms').document(doc_id)
        dict = user_doc_ref.get().to_dict()
        admin = dict['admin']
        if admin == userId:
            return True
        return False

    def does_exist(self, roomId):
        docs = self.database.collection('rooms').get()
        for doc in docs:
            key = doc.id
            key = key.strip()
            roomId = roomId.strip()
            if key == roomId:
                return True
        return False

    def is_in_room(self, doc_id):
        userId = self.auth.current_user.get('localId')
        userId = userId.strip()
        doc = self.database.collection('rooms').document(doc_id).get().to_dict()
        users = doc['users']
        for user in users:
            user = user.strip()
            if user == userId:
                return True
        return False

    def create_room(self, room):
        try:
            userId = self.auth.current_user.get('localId')
            dict = {'room': room}
            doc_ref = self.database.collection('messages').document()
            doc_id = doc_ref.id
            doc_ref.set(dict)
            dict = {
                'room': room,
                'users': [userId]
            }
            self.database.collection('rooms').document(doc_id).set(dict)
            dict = {room: doc_id}
            doc_ref = self.database.collection('users').document(userId)
            doc = doc_ref.get().to_dict()
            og_dict = doc['rooms']
            og_dict.update(dict)
            print(og_dict)
            self.database.collection('users').document(userId).update({"rooms": og_dict})
            return True, doc_id
        except Exception as ex:
            print("create Error - ", ex)
            return False, None
