from flask import render_template, url_for, redirect, flash, request, Response
from flaskblog.forms import RegistrationForm, LoginForm, UpdateAccountForm
from flaskblog.models import User, Post, Temperature
from flaskblog import app, db, bcrypt
from flask_login import login_user, current_user, logout_user, login_required
from imutils.video import VideoStream
import threading
import imutils
import time
import random
import secrets
import os
from datetime import datetime
from PIL import Image
import matplotlib.pyplot as plt
from flaskblog.motiondetector import MotionDetector
import cv2 
import numpy as np
from socket import *


outputFrame = None
lock = threading.Lock()


address = ( '192.168.1.5', 5000) 
client_socket = socket(AF_INET, SOCK_DGRAM) 
client_socket.settimeout(1) 
 
control_name = [
"temperature",
"light",
"lock",
"askTemperature"
]

temperature_control = [
"plus",
"minus"
]

light_control = [
"on",
"off"
]

lock_control = [
"open",
"close"
]

def sendControl(controlName, controlValue):
    data = controlName + " " + controlValue; 
    client_socket.sendto(data.encode(), address)

def requestData(controlName):
    data = controlName + " Request"; 
    client_socket.sendto(data.encode(), address)
    try:
        rec_data, addr = client_socket.recvfrom(2048)
        return(rec_data)
    except: 
        pass

def sendCommand(commandName, commandValue):
    try:
        address = ( '192.168.1.5', 5000) 
        client_socket = socket(AF_INET, SOCK_DGRAM) 
        client_socket.settimeout(1) 
        sendControl(commandName, commandValue)
    except:
        pass

def getValues(commandName):
    try:
        address = ( '192.168.1.5', 5000) 
        client_socket = socket(AF_INET, SOCK_DGRAM) 
        client_socket.settimeout(1) 
        requestData(commandName)
    except:
        pass

# testing only

posts = [
    {
        'author': 'Kollo Magor',
        'title' : 'Blog Post 1',
        'content': 'First post content',
        'date_posted' : 'October 23, 2021'
    },
    {
        'author': 'John Doe',
        'title' : 'Blog Post 2',
        'content': 'Second post content',
        'date_posted' : 'October 24, 2021'
    }
]



@app.route("/") # decorator -> additional functionality to existing functions
@app.route("/home")
def home():
    return render_template("home.html", posts=posts, now=datetime.utcnow())

@app.route("/about") # decorator -> additional functionality to existing functions
def about():
    return render_template("about.html", title ="About", now=datetime.utcnow())

@app.route("/register", methods = ['GET', 'POST']) # decorator -> additional functionality to existing functions
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_pw = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email = form.email.data, password = hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash(f'Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template("register.html", title ="Register", form = form, now=datetime.utcnow())

@app.route("/login", methods = ['GET', 'POST']) # decorator -> additional functionality to existing functions
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        if user and bcrypt.check_password_hash(user.password,form.password.data):
            login_user(user, remember = form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check your email and password!', 'danger')
    return render_template("login.html", title ="Login", form = form, now=datetime.utcnow())

def plotData(tempD):
    xAxis = []
    yAxis = []
    for row in tempD[-10:]:
        xAxis.append(row.date_posted.strftime("%H:%M"))
        yAxis.append(row.tempC)
    plt.plot(xAxis, yAxis)
    plt.ylabel("celsius")
    plt.xlabel("time")
    plt.savefig("/home/pi/projects/CN/flaskBlog/flaskblog/static/tempData.png")



temp = random.randint(17, 23)
tempVendor = None
@app.route("/temperature", methods = ['GET', 'POST'])
def temperature():
    global tempVendor
    #img_file = "../temp"
    if tempVendor is None:
        tempVendor = temp
        tempModel = Temperature(tempC = tempVendor)
        db.session.add(tempModel)
        db.session.commit()
        tempD = Temperature.query.all()
        plotData(tempD)
        print("Now is in this stage, tempVendor = ", tempVendor)
        return render_template('temperature.html', title = "Temperature", tempC = tempVendor, now=datetime.utcnow())
    else:
        if request.method == 'POST':
            if request.form.get('action1') == '+':
                tempVendor = tempVendor + 1
                print("plus", tempVendor)
                #tempD = Temperature.query.all()
                #flash(tempD, 'success')
                sendCommand(control_name[0],temperature_control[0])
                return render_template('temperature.html', title = "Temperature", tempC = tempVendor, now=datetime.utcnow())
            elif  request.form.get('action2') == '-':
                tempVendor = tempVendor - 1
                print("minus", tempVendor)
                #tempD = Temperature.query.all()
                #flash(tempD, 'success')
                sendCommand(control_name[0],temperature_control[1])
                return render_template('temperature.html', title = "Temperature", tempC = tempVendor, now=datetime.utcnow())
            else:
                pass # unknown
        elif request.method == 'GET':
            return render_template('temperature.html', title = "Temperature", tempC = tempVendor, now=datetime.utcnow())
        
        return render_template("temperature.html", now=datetime.utcnow())


@app.route("/lock", methods = ['GET', 'POST'])
def lock():
    lockS = "Closed"
    if request.method == 'POST':
        if request.form.get('lockON') == 'Open':
            print("ON")
            lockS = "Opened"
            sendCommand(control_name[2],lock_control[0])
            return render_template('lock.html', lockStatus = lockS, title = "Lock", now=datetime.utcnow())
        elif  request.form.get('lockOFF') == 'Close':
            print("OFF")
            lockS = "Closed"
            sendCommand(control_name[2],lock_control[1])
            return render_template('lock.html', lockStatus = lockS, title = "Lock", now=datetime.utcnow())
        else:
            pass # unknown
    elif request.method == 'GET':
        return render_template('lock.html', lockStatus = lockS, title = "Lock",  now=datetime.utcnow())
    
    return render_template("lock.html", now=datetime.utcnow())


@app.route("/lamp", methods = ['GET', 'POST'])
def lamp():
    lampS = "off"
    if request.method == 'POST':
        if request.form.get('lampON') == 'on':
            print("ON")
            lampS = "on"
            sendCommand(control_name[1],light_control[0])
            return render_template('lamp.html', lampStatus = lampS, title = "Lamp", now=datetime.utcnow())
        elif  request.form.get('lampOFF') == 'off':
            print("OFF")
            lampS = "off"
            sendCommand(control_name[1],light_control[1])
            return render_template('lamp.html', lampStatus = lampS, title = "Lamp", now=datetime.utcnow())
        else:
            pass # unknown
    elif request.method == 'GET':
        return render_template('lamp.html', lampStatus = lampS, title = "Lamp", now=datetime.utcnow())
    
    return render_template("lamp.html", now=datetime.utcnow())




@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path  = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    #form_picture.save(picture_path)

    return picture_fn



@app.route('/account', methods = ['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Your account has been updated!", 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template("account.html", title= "Account",
                            image_file = image_file, form = form, now=datetime.utcnow())


# def motion_detector(
#         self.accumW = accumWeighted
#     def flasH

def detect_motion():
    vs = VideoStream(src=0).start()
    #global outputFrame, lock
    frameCount = 32
    #time.sleep(2.0)
	# initialize the motion detector and the total number of frames
	# read thus far
    md = MotionDetector(accumWeight=0.1)
    total = 0
    while True:
        frame = vs.read()
        print("mi a baj")
        #height = int(frame.shape[0])
        #frame = cv2.resize(frame, (400,250), interpolation = cv2.INTER_AREA)
        #print(frame)
        # if AttributeError:
        #     print("why")
        #     continue
        # else:
        frame = imutils.resize(frame, width=400)
        #frame = np.array(frame)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(frame, (7, 7), 0)
        
        timestamp = datetime.now()
        cv2.putText(frame, timestamp.strftime(
            "%A %d %B %Y %I:%M:%S%p"), (10, frame.shape[0] - 10),
            cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 255), 1)

        if total > frameCount:
            motion = md.detect(gray)
            if motion is not None:
                (thresh, (minX, minY, maxX, maxY)) = motion
                cv2.rectangle(frame, (minX, minY), (maxX, maxY),
                    (0, 0, 255), 2)
        
        md.update(gray)
        total += 1
        

        outputFrame = frame.copy()
        (flag, encodedImage) = cv2.imencode(".jpg",outputFrame )
        if not flag:
            continue
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
			bytearray(encodedImage) + b'\r\n')

	

# def gen_frames(vs):
#     global outputFrame

#     while True:
#         if outputFrame is None:
#             continue
#         (flag, encodedImage) = cv2.imencode(".jpg",outputFrame )
#         if not flag:
#             continue
#         yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
# 			bytearray(encodedImage) + b'\r\n')
    

# def gen_frames():
# 	# grab global references to the output frame and lock variables
# 	global outputFrame, lock

# 	# loop over frames from the output stream
# 	while True:
#         if outputFrame is None:
# 		    continue

# 			# encode the frame in JPEG format
# 			(flag, encodedImage) = cv2.imencode(".jpg", outputFrame)

# 			# ensure the frame was successfully encoded
# 			if not flag:
# 				continue

# 		# yield the output frame in the byte format
# 		yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
# 			bytearray(encodedImage) + b'\r\n')
  

def gen_frames2():
    camera = cv2.VideoCapture(0)  
    while True:
        success, frame = camera.read()  # read the camera frame
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result

@app.route('/video_feed')
def video_feed():
    s = socket(AF_INET, SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    local_ip = s.getsockname()[0]
    s.close()
    ip = "http://" +local_ip + ":5001"
    return redirect(ip, code=302)
    #time.sleep(2.0)
    #t = threading.Thread(target=gen_frames2)
    #t.daemon = True
    #t.start()
    # return Response(detect_motion(), 
    #     mimetype = 'multipart/x-mixed-replace; boundary = frame')


