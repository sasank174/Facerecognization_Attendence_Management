from datetime import datetime
import face_recognition
import mysql.connector
import numpy as np
import cv2

mydb = mysql.connector.connect(
	host = "localhost",
	user = "root",
	password = "",
	database = "AI_DB"
)

global knownencodings,count,sub
knownencodings =[]
count = 0
sub=""

def faceencodingvalues(img):
	print("===============start=====================================================")
	imgload = face_recognition.load_image_file(img)
	imgload = cv2.cvtColor(imgload,cv2.COLOR_BGR2RGB)

	faceloc = face_recognition.face_locations(imgload)[0]  # (260, 825, 528, 557)
	encodeimg = face_recognition.face_encodings(imgload)[0]
	print("===============faceloc=====================================================")
	# print(faceloc)
	print("==================encodeimg==================================================")
	# print(encodeimg)

	return (encodeimg,faceloc)

def addsubject(subjectname):
	global sub
	subjectname = subjectname.lower()
	sub = subjectname
	mycursor = mydb.cursor()
	mycursor.execute("SHOW TABLES")
	subjectlist = [column[0] for column in mycursor.fetchall()]
	print(subjectlist)
	mycursor.close()
	if subjectname not in subjectlist:
		mycursor = mydb.cursor()
		now = datetime.now()
		date = now.strftime("%m-%d-%Y")
		sql = "CREATE TABLE `"+subjectname+"` ( `id` INT NOT NULL AUTO_INCREMENT , `Regno` VARCHAR(225) NOT NULL , `"+date+"` VARCHAR(225) NOT NULL DEFAULT 'ABSENT' , PRIMARY KEY (`id`));"
		mycursor.execute(sql)
		mydb.commit()
		mycursor.close()
		print("created")
		return "created"
	else:
		print("existed")
		return "existed"


def attendence_check(name,subject):
	# now = datetime.now()
	# tdate = now.strftime("%m-%d-%Y")
	addtoday(subject)
	now = datetime.now()
	date = now.strftime("%m-%d-%Y")

	mycursor = mydb.cursor()
	sql = "SELECT `"+date+"` FROM `"+subject+"` WHERE `Regno`=%s"
	val = (name,)
	mycursor.execute(sql,val)
	myresult = mycursor.fetchall()
	if mycursor.rowcount == 1:
		mycursor.close()
		if myresult[0][0] == "ABSENT":
			print("ABSENT")
			return "ABSENT"
		else:
			print("PRESENT")
			return "PRESENT"
	elif mycursor.rowcount == 0:
		mycursor.close()
		print("ABSENT")
		return "ABSENT"
	else:
		print("error in attendence check")
		return "ERROR"

def addtoday(subject):
	mycursor = mydb.cursor()
	sql = "SHOW columns FROM `"+subject+"`;"
	mycursor.execute(sql)
	columns = [column[0] for column in mycursor.fetchall()]
	now = datetime.now()
	date = now.strftime("%m-%d-%Y")
	if date not in columns:
		mycursor = mydb.cursor()
		sql = "ALTER TABLE `"+subject+"` ADD `"+date +"` VARCHAR(225) NOT NULL DEFAULT 'ABSENT'"
		mycursor.execute(sql)
		mydb.commit()
		print("today date added")
		mycursor.close()
	else:
		print("today date already present")
		mycursor.close()

def predata(regnosofstudent=""):
	global knownencodings,count
	count=0
	knownencodings = allencodings()
	mycursor = mydb.cursor()
	mycursor.execute("SELECT Regno FROM student")
	myresult = mycursor.fetchall()
	for i in myresult:
		if i[0] == regnosofstudent:
			break
		count+=1
	mycursor.close()

def allencodings():
	encodinglist = []
	mycursor = mydb.cursor()
	sql = "SELECT * FROM student"
	mycursor.execute(sql)
	myresult = mycursor.fetchall()
	for result in myresult:
		arr = np.array(eval(result[6]))
		encodinglist.append(arr)
	mycursor.close()
	return encodinglist


def detect(img,regnosofstudent=""):
	imgS = cv2.resize(img,(0,0),None,0.25,0.25)
	imgS = cv2.cvtColor(imgS,cv2.COLOR_BGR2RGB)
	facesS = face_recognition.face_locations(imgS)
	encodeS = face_recognition.face_encodings(imgS,facesS)

	for encodeFace,faceLoc in zip(encodeS,facesS):
		print("check response")
		matches = face_recognition.compare_faces(knownencodings,encodeFace)
		faceDis = face_recognition.face_distance(knownencodings,encodeFace)
		# print(faceDis)
		matchindex = np.argmin(faceDis)
		# print(matchindex)
		# print("match index "+str(matches[matchindex]))
		# print("face dis "+str(faceDis[matchindex]))
		# print("match index "+str(matchindex))
		# print("count "+ str(count))
		if matches[matchindex] and faceDis[matchindex]<0.6 and matchindex == count:
			# print("==========================================="+str(faceDis[matchindex])+"===========================================")
			name = regnosofstudent
			# print(name)
			y1,x2,y2,x1 = faceLoc
			y1,x2,y2,x1 = y1*4,x2*4,y2*4,x1*4
			cv2.rectangle(img,(x1,y1),(x2,y2),(0,255,0),2)
			cv2.rectangle(img,(x1,y2-35),(x2,y2),(0,255,0),cv2.FILLED)
			cv2.putText(img,name,(x1+6,y2-6),cv2.FONT_HERSHEY_DUPLEX,1,(255,255,255),2)




			attendence(name)
			ret,buffer=cv2.imencode('.jpg',img)
			frame=buffer.tobytes()
			print("frame captured")
			return (frame,"YES")
	ret,buffer=cv2.imencode('.jpg',img)
	frame=buffer.tobytes()
	print("not response")
	return (frame,"NO")



def attendence(name):
	# addtoday()
	mycursor = mydb.cursor()
	sql = "SELECT * FROM `"+sub+"` WHERE `Regno`=%s"
	val = (name,)
	mycursor.execute(sql,val)
	myresult = mycursor.fetchall()
	now = datetime.now()
	tdate = now.strftime("%m-%d-%Y")
	timeS = now.strftime('%H:%M:%S')
	if mycursor.rowcount == 1:
		mycursor.close()
		mycursor = mydb.cursor()
		sql = "UPDATE `"+sub+"` SET `"+tdate+"`='"+timeS+"' WHERE Regno = '"+name+"'"
		mycursor.execute(sql)
		mydb.commit()
		mycursor.close()
		print("attendence marked")
	elif mycursor.rowcount == 0:
		mycursor.close()
		mycursor = mydb.cursor()
		sql = "INSERT INTO `"+sub+"` (Regno, `"+tdate+"`) VALUES (%s, %s);"
		val = (name,timeS)
		mycursor.execute(sql,val)
		mydb.commit()
		mycursor.close()
		print("attendence marked")
	else:
		print("error")