from flask import Flask, render_template, redirect, request, session,Response,send_file
import flask
from werkzeug.utils import secure_filename
from facedetector import  addsubject, attendence_check, detect, faceencodingvalues, predata
from flask_mail import Mail, Message
import mysql.connector
import numpy as np
import cv2
import os


app = Flask(__name__)
mail= Mail(app)
app.secret_key = "sasank"
UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

global recorded,cap
recorded = "NO"

mydb = mysql.connector.connect(
	host = "localhost",
	user = "root",
	password = "",
	database = "AI_DB"
)

def mailing(email,regno,password):
	app.config['MAIL_SERVER']='smtp.gmail.com'
	app.config['MAIL_PORT'] = 465
	app.config['MAIL_USERNAME'] = 'manamwhy@gmail.com'
	app.config['MAIL_PASSWORD'] = 'neekuenduku'
	app.config['MAIL_USE_TLS'] = False
	app.config['MAIL_USE_SSL'] = True
	mail = Mail(app)
	msg = Message('Hello', sender = 'manamwhy@gmail.com', recipients = [email])
	msg.body = "<h1>Hello Flask message sent from Flask-Mail</h1>"
	msg.subject = "password change"
	link = "http://127.0.0.1:7890/change?regno="+regno+"&password="+password
	msg.html = "<div><h1>change password</h1><h1><a href='"+link+"'}>click me</a></h1></div>"
	mail.send(msg)
	
	return "Sent sucessful"

# =============================home============================================================================================
@app.route("/")
@app.route("/home")
def home():
	if "teacher" in session:
		return redirect('/teacher')
	if "student" in session:
		return redirect('/student')
	if "admin" in session:
		return redirect('/admin')
	else:
		return render_template("common/home.html")

# =============================logout============================================================================================
@app.route("/logout")
def logout():
	session.clear()
	return redirect("/")

# =============================admin============================================================================================
@app.route("/admin", methods = ['POST', 'GET'])
def admin():
	if request.method == 'GET':
		if "admin" in session:
			return render_template("admin/admin.html")
		else:
			return render_template("admin/adminlog.html")

	if request.method == 'POST':
		values = request.form.to_dict()
		if (values["username"],values["password"]) == ("sasank","sasank"):
			session['admin'] = values["username"]
		return redirect("/admin")

# =============================adminadd============================================================================================
@app.route("/adminadd", methods = ['POST', 'GET'])
def addadmin():
	if request.method == 'GET':
		f = request.args.get("who")
		if "teacher" in f:
			return render_template("admin/tadd.html")
		elif "student" in f:
			return render_template("admin/sadd.html")
		else:
			return redirect("/admin")
	
	
	if request.method == 'POST':
		values = request.form.to_dict()
		if values["who"] == "teacher":
			mycursor = mydb.cursor()
			sql = "SELECT * FROM `teacher` WHERE `Courseid`=%s OR `Cname`=%s"
			val = (values["Regno"],values["Tname"])
			mycursor.execute(sql,val)
			myresult = mycursor.fetchall()
			if mycursor.rowcount == 1:
				mycursor.close()
				return render_template("common/error.html",errormsg = "teacher is already assigned to the course")
				return "<h1>teacher is already assigned to the course</h1><br><h1><a href='/'>Home</a></h1>"
			elif mycursor.rowcount == 0:
				mycursor = mydb.cursor()
				sql = "INSERT INTO `teacher` values('',%s,%s,%s,%s)"
				val = (values["Tname"],values["Name"],values["Regno"],"12345")
				mycursor.execute(sql,val)
				mydb.commit()
				mycursor.close()
				return render_template("common/error.html",errormsg = "subject added")
				return "<h1>subject added</h1><br><h1><a href='/'>Home</a></h1>"
			else:
				return render_template("common/error.html",errormsg = "internal error")
				return "<h1>internal error</h1><br><h1><a href='/'>Home</a></h1>"
			
		if values["who"] == "student":
			mycursor = mydb.cursor()
			sql = "SELECT * FROM `student` WHERE `Regno` = %s OR `Email` = %s"
			val = (values["Regno"],values["Email"])
			mycursor.execute(sql,val)
			myresult = mycursor.fetchall()
			if mycursor.rowcount == 1:
				mycursor.close()
				return render_template("common/error.html",errormsg = "a student with same regno or email id is already present")
				return "<h1>a student with same regno or email id is already present</h1><br><h1><a href='/'>Home</a></h1>"
			elif mycursor.rowcount == 0:
				fname = values["Regno"]
				file = request.files['file']
				if file:
					filename = fname+os.path.splitext(secure_filename(file.filename))[1]
					pathtoimg = os.path.join(app.config['UPLOAD_FOLDER'], filename)
					file.save(pathtoimg)
				faceencodings,facelocs = faceencodingvalues(pathtoimg)
				if len(facelocs)==0:
					return render_template("common/error.html",errormsg = "problem with image")
					return "<h1>problem with image</h1><br><h1><a href='/'>Home</a></h1>"
				mycursor = mydb.cursor()
				sql = "INSERT INTO `student` values('',%s,%s,%s,%s,%s,%s)"
				val = (values["Name"],values["Email"],values["Regno"],"12345","",str(faceencodings.tolist()))
				mycursor.execute(sql,val)
				mydb.commit()
				mycursor.close()
				return render_template("common/error.html",errormsg = "student added")
				return "<h1>student added</h1><br><h1><a href='/'>Home</a></h1>"

			else:
				return render_template("common/error.html",errormsg = "internal error")
				return "<h1>internal error</h1><br><h1><a href='/'>Home</a></h1>"
		
# =============================login============================================================================================
@app.route("/teacherlogin", methods = ['POST', 'GET'])
def teacherlogin():
	if request.method == 'GET':
		if "teacher" in session:
			return redirect("/teacher")
		elif "student" in session:
			return redirect("/student")
		else:
			return render_template('common/teacherlogin.html')
	if request.method == 'POST':
		values = request.form.to_dict()
		mycursor = mydb.cursor()
		sql = "SELECT * FROM teacher WHERE Courseid=%s"
		val = (values["Regno"],)
		mycursor.execute(sql,val)
		myresult = mycursor.fetchall()
		if mycursor.rowcount == 1:
			if (values["Regno"],values["password"]) == (myresult[0][3],myresult[0][4]):
				session['teacher'] = values["Regno"]
				mycursor.close()
				return redirect("/")
			else:
				mycursor.close()
				return render_template("common/error.html",errormsg = "incorrect password")
				return "<h1>incorrect password</h1><br><h1><a href='/'>Home</a></h1>"
		elif mycursor.rowcount == 0:
			mycursor.close()
			return render_template("common/error.html",errormsg = "invalid course id")
			return "<h1>invalid course id</h1><br><h1><a href='/'>Home</a></h1>"
		else:
			mycursor.close()
			return render_template("common/error.html",errormsg = "some internel error has occured")
			return "<h1>some internel error has occured</h1><br><h1><a href='/'>Home</a></h1>"

@app.route("/studentlogin", methods = ['POST', 'GET'])
def studentlogin():
	if request.method == 'GET':
		if "teacher" in session:
			return redirect("/teacher")
		elif "student" in session:
			return redirect("/student")
		else:
			return render_template('common/studentlogin.html')
	

	if request.method == 'POST':
		values = request.form.to_dict()
		mycursor = mydb.cursor()
		sql = "SELECT * FROM `student` WHERE Regno=%s"
		val = (values["Regno"],)
		mycursor.execute(sql,val)
		myresult = mycursor.fetchall()
		if mycursor.rowcount == 1:
			if (values["Regno"],values["password"]) == (myresult[0][3],myresult[0][4]):
				session['student'] = myresult[0][3]
				session['regno'] = values["Regno"]
				Subjects = myresult[0][5]
				Subjects = Subjects.split(",")
				session['student_subjects'] = Subjects
				mycursor.close()
				return redirect("/")
			else:
				mycursor.close()
				return render_template("common/error.html",errormsg = "")
				return render_template("common/error.html",errormsg = "incorrect password")
				return "<h1>incorrect password</h1><br><h1><a href='/'>Home</a></h1>"
		elif mycursor.rowcount == 0:
			mycursor.close()
			return render_template("common/error.html",errormsg = "invalid reg no")
			return "<h1>invalid reg no</h1><br><h1><a href='/'>Home</a></h1>"
		else:
			mycursor.close()
			return render_template("common/error.html",errormsg = "some internel error has occured")
			return "<h1>some internel error has occured</h1><br><h1><a href='/'>Home</a></h1>"
	
# =============================forgot password============================================================================================
@app.route("/forgotpassword", methods = ['POST', 'GET'])
def forgot():
	if request.method == 'GET':
		if "teacher" in session:
			return redirect("/")
		elif "student" in session:
			return redirect("/")
		elif "admin" in session:
			return redirect("/admin")
		else:
			return render_template("common/forgotpassword.html")
	
	if request.method == 'POST':
		values = request.form.to_dict()
		if values["npassword"] != values["cpassword"]:
			return render_template("common/error.html",errormsg = "new password and conform password should be same")
			return "<h1>new password and conform password should be same</h1><br><h1><a href='/'>Home</a></h1>"
		mycursor = mydb.cursor()
		sql = "SELECT * FROM student WHERE Regno=%s"
		val = (values["Regno"],)
		mycursor.execute(sql,val)
		myresult = mycursor.fetchall()
		if mycursor.rowcount == 1:
			try:
				check = mailing(myresult[0][2],myresult[0][3],values["npassword"])
				if check == "Sent sucessful":
					return render_template("common/error.html",errormsg = "verify your mail to update")
					return "<h1>verify your mail to update</h1><br><h1><a href='/'>Home</a></h1>"
				else:
					return render_template("common/error.html",errormsg = "serror in sending mail")
					return "<h1>serror in sending mail</h1><br><h1><a href='/'>Home</a></h1>"
			except:
				return render_template("common/error.html",errormsg = "error in sending mail")
				return "<h1>error in sending mail</h1><br><h1><a href='/'>Home</a></h1>"
		elif mycursor.rowcount == 0:
			mycursor.close()
			return render_template("common/error.html",errormsg = "no such regno")
			return "<h1>no such regno</h1><br><h1><a href='/'>Home</a></h1>"
		else:
			mycursor.close()
			return render_template("common/error.html",errormsg = "internal error as occured")
			return "<h1>internal error as occured</h1><br><h1><a href='/'>Home</a></h1>"

# =============================change password============================================================================================
@app.route("/change", methods = ['POST', 'GET'])
def change():
	if request.method == 'GET':
		regno = request.args.get("regno")
		password = request.args.get("password")
		if regno != None and password != None:
			mycursor = mydb.cursor()
			sql = "SELECT * FROM `student` WHERE Regno=%s"
			val = (regno,)
			mycursor.execute(sql,val)
			myresult = mycursor.fetchall()
			if mycursor.rowcount == 1:
				mycursor = mydb.cursor()
				sql = "UPDATE `student` SET `Password` = %s WHERE `Regno` = %s"
				val = (password,regno)
				mycursor.execute(sql,val)
				mydb.commit()
				mycursor.close()
				return render_template("common/error.html",errormsg = "sucessfully changed")
				return "<h1>sucessfully changed</h1><br><h1><a href='/'>Home</a></h1>"
			elif mycursor.rowcount == 0:
				return render_template("common/error.html",errormsg = "invalid URL")
				return "<h1>invalid URL</h1><br><h1><a href='/'>Home</a></h1>"
			else:
				return render_template("common/error.html",errormsg = "invalid URL")
				return "<h1>invalid URL</h1><br><h1><a href='/'>Home</a></h1>"
		else:
			return render_template("common/error.html",errormsg = "invalid URL")
			return "<h1>invalid URL</h1><br><h1><a href='/'>Home</a></h1>"
		
		return render_template("common/error.html",errormsg = "invalid URL")
		return "<h1>invalid URL</h1><br><h1><a href='/'>Home</a></h1>"

	if request.method == 'POST':
		return redirect("/")

# =============================teacher============================================================================================
@app.route("/teacher", methods = ['POST', 'GET'])
def teacher():
	if "teacher" in session:
		mycursor = mydb.cursor()
		sql = "SELECT * FROM `teacher` WHERE Courseid=%s"
		val = (session["teacher"],)
		mycursor.execute(sql,val)
		myresult = mycursor.fetchall()
		if mycursor.rowcount == 1:
			return render_template("teacher/teacherhome.html",data = myresult[0])
		else:
			return render_template("common/error.html",errormsg = "some error has occured")
			return "<h1>some error has occured</h1><br><h1><a href='/'>Home</a></h1>"
	elif "student" in session:
		return redirect('/student')
	elif "admin" in session:
		return redirect('/admin')
	else:
		return redirect('/')

# =============================student list============================================================================================
@app.route("/studentlist")
def studentlist():
	mycursor = mydb.cursor()
	sql = "SELECT * FROM student"
	mycursor.execute(sql)
	myresult = mycursor.fetchall()
	mycursor.close()
	return render_template("teacher/studentlist.html",data = myresult)

# =============================new student============================================================================================
@app.route("/newstudent", methods = ['POST', 'GET'])
def newstudent():
	if request.method == 'GET' and "teacher" in session:
		return render_template('teacher/newstudent.html')
	if request.method == 'POST':
		values = request.form.to_dict()
		mycursor = mydb.cursor()
		sql = "SELECT * FROM student WHERE Regno=%s"
		val = (values["regno"],)
		mycursor.execute(sql,val)
		myresult = mycursor.fetchall()
		if mycursor.rowcount == 1:
			Subjects = myresult[0][5]
			Subjects = Subjects.split(",")
			if Subjects[0] == '':
				Subjects.pop(0)
			if session['teacher'] in Subjects:
				mycursor.close()
				return render_template("common/error.html",errormsg = "user already added")
				return "<h1>user already added</h1><br><h1><a href='/'>Home</a></h1>"
			else:
				Subjects.append(session['teacher'])
				Subjects.sort()
				Subjects = ",".join(Subjects)
				mycursor = mydb.cursor()
				sql = "UPDATE student SET subjects = %s WHERE Regno = %s"
				val = (Subjects,values["regno"])
				mycursor.execute(sql,val)
				mydb.commit()
				mycursor.close()
				return render_template("common/error.html",errormsg = "updated subject")
				return "<h1>updated subject</h1><br><h1><a href='/'>Home</a></h1>"
		elif mycursor.rowcount == 0:
			return render_template("common/error.html",errormsg = "no account with this register number")
			return "<h1>no account with this register number</h1><br><h1><a href='/'>Home</a></h1>"
		else:
			return render_template("common/error.html",errormsg = "an error has occured")
			return "<h1>an error has occured</h1><br><h1><a href='/'>Home</a></h1>"
			
	return redirect("/")

# =============================student============================================================================================
@app.route("/student", methods = ['POST', 'GET'])
def student():
	if "student" in session:
		print(session["student"])
		mycursor = mydb.cursor()
		sql = "SELECT * FROM `student` WHERE Regno=%s"
		val = (session["student"],)
		mycursor.execute(sql,val)
		studetails = mycursor.fetchall()
		if mycursor.rowcount == 1:
			Subjects = studetails[0][5]
			Subjects = Subjects.split(",")

			if Subjects[0] == '':
				return render_template("student/studenthome.html",data = studetails[0])
			else:
				sublist = []
				for i in Subjects:
					mycursor = mydb.cursor()
					sql = "SELECT Courseid,Cname FROM `teacher` WHERE Courseid=%s"
					val = (i,)
					mycursor.execute(sql,val)
					myresult = mycursor.fetchall()
					sublist.append(myresult[0])
				return render_template("student/studenthome.html",data = studetails[0],sublist=sublist)

			return render_template("student/studenthome.html",data = studetails[0],Subjects=Subjects)
		else:
			return render_template("common/error.html",errormsg = "some error has occured")
			return "<h1>some error has occured</h1><br><h1><a href='/'>Home</a></h1>"
	elif "teacher" in session:
		return redirect('/teacher')
	elif "admin" in session:
		return redirect('/admin')
	else:
		return redirect('/')


# =============================subject attendence============================================================================================
@app.route("/stuattendence", methods = ['POST', 'GET'])
def stuattendence():
	if request.method == 'GET':
		subjectname = request.args.get("subject")
		re = addsubject(subjectname)
		if (re == "created" or re == "existed"):
			check = attendence_check(session["student"],subjectname)
			if check == "PRESENT":
				return render_template("common/error.html",errormsg = "attendence already marked")
				return "<h1>attendence already marked</h1><br><h1><a href='/'>Home</a></h1>"
			else:
				return render_template("student/attendance.html",subjectname=subjectname)
		else:
			return render_template("common/error.html",errormsg = "error in attendence")
			return "<h1>error in attendence</h1><br><h1><a href='/'>Home</a></h1>"

cap = cv2.VideoCapture(0)
# =============================for attendence recording============================================================================================
def gen_frames(regnosofstudent):
	global recorded,cap
	# predata(regnosofstudent)
	cap = cv2.VideoCapture(0)
	while True:
		sucess,img = cap.read()
		(frame,ans) = detect(img,regnosofstudent)
		recorded = ans
		if recorded == "YES":
			break

		yield(b'--frame\r\n'
					b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
	print("yield condition exit")
	cap.release()			

@app.route('/video_feed')
def video_feed():
	predata(session["student"])
	return Response(gen_frames(session["student"]), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/recorded')
def recorded():
	global recorded
	if recorded == "YES":
		return flask.jsonify("YES")
	elif recorded == "NO":
		return flask.jsonify("NO")
	else:
		return flask.jsonify("NO")

@app.route('/recorddone', methods = ['POST', 'GET'])
def recorddone():
	global recorded
	cap.release()
	recorded = "NO"
	if request.method == 'GET':
		return render_template("common/error.html",errormsg = "attendence has been recorded")
		return "<h1>attendence has been recorded</h1><br><h1><a href='/'>Home</a></h1>"

# =============================view attendence============================================================================================
@app.route("/viewattendence", methods = ['POST', 'GET'])
def viewattendence():
	if request.method == 'GET':
		print("=================================================")
		print(session["teacher"])
		try:
			csv(session["teacher"].lower())
			return render_template("teacher/csv.html")
		except:
			return render_template("common/error.html",errormsg = "error in creaing file")
			return "<h1>error in creaing file</h1><br><h1><a href='/'>Home</a></h1>"

@app.route("/dowload_file")
def dowload_file():
	path = "static/files/"+session["teacher"].lower()+".csv"
	return send_file(path,as_attachment=True)



def csv(subject):
	# os.remove("static/files/"+subject+".csv")
	headinglist = headings(subject)
	attendncedata = data(subject)
	with open("static/files/"+subject+".csv","w+") as f:
		headingdata= f",".join(headinglist)
		f.writelines(headingdata)
		for info in attendncedata:
			x = f"\n"+",".join(map(str, info))
			f.writelines(x)
	return "YES"

def headings(subject):
	mycursor = mydb.cursor()
	sql = "SHOW columns FROM `"+subject+"`;"
	mycursor.execute(sql)
	columns = [column[0] for column in mycursor.fetchall()]
	mycursor.close()
	# print(subject)
	return columns

def data(subject):
	mycursor = mydb.cursor()
	sql = "SELECT * FROM `"+subject+"`;"
	mycursor.execute(sql)
	myresult = mycursor.fetchall()
	mycursor.close()
	return myresult


if __name__ == '__main__':
	app.run(debug=True,port=7890)