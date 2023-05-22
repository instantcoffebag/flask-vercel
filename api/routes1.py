from flask import Flask, render_template, request, redirect, url_for
from project.MyApp.UserApi.UserAccess import *
from project.MyApp.errors import *
from project.MyApp.User import *
from flask_socketio import SocketIO, join_room, leave_room
from email.message import EmailMessage
import ssl
import smtplib

app = Flask(__name__)
# connects sockets to said object
socketio = SocketIO(app)

EMAIL_SENDER = 'cyberchatproject@gmail.com'
EMAIL_PASSW = 'xmxxyjpbehthvjpz'

# region -----------------pageerror-----------------
@app.route('/pageerror/<message>', methods=['POST', 'GET'])
def pageerror(message):
    mes = error_message(message)
    if mes is None:
        mes = message
    # puts up the login template again with the error message recieved
    return render_template('login.html', message=mes)
# endregion


# region ---------------index----------------
@app.route('/index/<params>', methods=['GET', 'POST'])
def index(params):
    if params == "signOut":
        return redirect(url_for('login'))
    if params == "create" or params == "join":
        dict = request.form["dict"]
        dict = create_dict(dict)
        if params == "create":
            room = request.form["room"]
            valid, doc_id = create_room(room)

            email_reciever = UserAccess.getInstance().get_email()
            subject = 'you created a room'
            body = 'share this code with your friends so they can join the room:\n' + doc_id
            em = EmailMessage()
            em['From'] = EMAIL_SENDER
            em['To'] = email_reciever
            em['subject'] = subject
            em.set_content(body)
            contex = ssl.create_default_context()
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=contex) as smtp:
                smtp.login(EMAIL_SENDER, EMAIL_PASSW)
                smtp.sendmail(EMAIL_SENDER, email_reciever, em.as_string())

            UserAccess.getInstance().set_admin(doc_id)
            newRooms = UserAccess.getInstance().getUserRooms()
            namelist = list(newRooms.keys())
            dict.update({"rooms": namelist})
            idlist = list(newRooms.values())
            dict.update({"ids": idlist})
            dict.update({"amount_rooms": len(namelist)})
            return render_template('index.html', dict=dict)
        if params == "join":
            doc_id = request.form["roomId"]
            valid, msg = join(doc_id)
            newRooms = UserAccess.getInstance().getUserRooms()
            namelist = list(newRooms.keys())
            y = namelist[-1]
            namelist[-1] = y.replace("_", " ")
            dict.update({"rooms": namelist})
            idlist = list(newRooms.values())
            dict.update({"ids": idlist})
            dict.update({"amount_rooms": len(namelist)})
            return render_template('index.html', dict=dict, msg=msg)
    else:
        dict = create_dict(params)
        return render_template('index.html', dict=dict)
# endregion


# region -----------------chat-----------------
@app.route('/chat/<name>/<room>/<roomId>', methods=['GET', 'POST'])
def chat(name, room, roomId):
    if name == 'delete':
        UserAccess.getInstance().delete_room(roomId)
        rooms = remove_room(roomId, room)
        email = UserAccess.getInstance().get_email()
        passw = UserAccess.getInstance().get_passw()
        user = User(name, email, passw, rooms)
        return redirect(url_for('index', params=user))
    history = UserAccess.getInstance().get_chat_history(roomId)
    messages = list(history.values())
    admin = str(UserAccess.getInstance().am_i_admin(roomId))
    user_ids = UserAccess.getInstance().get_room_participants(roomId)
    users = []
    for user_id in user_ids:
        users.append(UserAccess.getInstance().get_name(user_id))
    dict = {"messages": messages,
            "admin": admin,
            "users": users}
    return render_template('chat.html', nickname=name, room=room, roomId=roomId, dict=dict)
# endregion


def remove_room(roomId, room):
    rooms = UserAccess.getInstance().getUserRooms()
    if not rooms:
        dict = {}
        return dict
    namelist = list(rooms.keys())
    for name in namelist:
        name = name.replace("_", " ")
        if name == room:
            namelist.remove(name)
    idlist = list(rooms.values())
    for id in idlist:
        if id == roomId:
            idlist.remove(id)
    dict = {}
    for name in namelist:
        dict.update({name: idlist[name]})
    return dict


# region -----------------create dict-----------------
def create_dict(params):
    params = params.split(",")
    if params[0] == '':
        params = params[1:]
    dict= {"name": params[0], "email": params[1], "passw": params[2], "amount_rooms": int(params[3])}
    dict["rooms"] = []
    dict["ids"] = []
    x = 0
    for room in params[4:]:
        if x == 0:
            if '#39;' in room:
                room = room[4:-5]
            room = room.replace("_", " ")
            dict["rooms"].append(room)
            x = 1
        else:
            dict["ids"].append(room)
            x = 0
    return dict
# endregion create dict


# region -----------------create room-----------------
def create_room(room):
    valid, doc_id = UserAccess.getInstance().create_room(room)
    if valid:
        return True, doc_id
    else:
        return False, None
# endregion create room


# region -----------------join room-----------------
def join(doc_id):
    if UserAccess.getInstance().does_exist(doc_id):
        if not UserAccess.getInstance().is_in_room(doc_id):
            UserAccess.getInstance().add_room(doc_id)
            return True, None
        return False, 'you are already in this room'
    return False, 'this rooom does not exist'
# endregion join room


# region -----------------check profile-----------------
# checks if the info given at the log in form is an actual user
def check_profile(email, passw):
    valid, message = UserAccess.getInstance().check_profile(email, passw)
    if valid:
        username = UserAccess.getInstance().getUserName()
        rooms = UserAccess.getInstance().getUserRooms()
        user = User(username, email, passw, rooms)
        if user:
            return redirect(url_for('index', params=user))
    return redirect(url_for('pageerror', message=message))
# endregion check profile


# region -----------------add profile-----------------
# checks if the info from the sign up form is valid. if it is, creates a new user
def add_profile(user):
    # add to firebase
    valid, message = UserAccess.getInstance().add_profile(user)
    if valid:
        return redirect(url_for('login'))
    return redirect(url_for('pageerror', message=message))
# endregion add profile


# region ------------------login-------------------
@app.route('/', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        try:
            buttonValue = request.form["buttonsignIn"]
        except:
            buttonValue = request.form["buttonsignUp"]
        if buttonValue == "signIn":
            email = request.form['email1']
            passw = request.form['passw1']
            return check_profile(email, passw)
        else:
            if buttonValue == "signUp":
                name = request.form['nameUser']
                user = request.form['email2']
                passw = request.form['passw2']
                # creates a user type object and sends it to the add profile function
                u1 = User(name, user, passw, rooms={})
                return add_profile(u1)
    return render_template('login.html')
# endregion login


# region --------------------socketio------------------------------
@socketio.on('joinroom')
def handle_join_room(data):
    # connects the socket to the room using the built-in join_room function
    join_room(data['roomId'])


# listens to the 'send_message' event
@socketio.on('send_message')
def handle_send_massage(data):
    socketio.emit('receive_message', data, room=data['roomId'])
    '''key = data['key']
    encrypted_msg = data['message']
    obj = AES.new(key, AES.MODE_ECB)  # , 'This is an IV456')
    data_after_dec = obj.decrypt(encrypted_msg)
    org_data = crypto.getInstance().StripPadding(data_after_dec)
    data['message'] = org_data'''
    valid = UserAccess.getInstance().add_message(data['nickname'], data['message'], data['roomId'])


@socketio.on('leave_room')
def handle_leave_room(data):
    leave_room(data['roomId'])
# endregion


if __name__ == '__main__':
    socketio.run(app, debug=True)
