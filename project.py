from flask import Flask
import hashlib
import json
import boto3
from flaskext.mysql import MySQL

app = Flask(__name__)

mysql = MySQL()

# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'master'
app.config['MYSQL_DATABASE_PASSWORD'] = 'qwerty123'
app.config['MYSQL_DATABASE_DB'] = 'attendance'
app.config['MYSQL_DATABASE_HOST'] = 'project.cubis4lnt2kc.ap-south-1.rds.amazonaws.com'
mysql.init_app(app)

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route("/process/<image_name>")
def process(image_name) :
    d=image_name.split("_")
    client = boto3.client('rekognition',aws_access_key_id="AKIAIVCDOBME6US2GYTQ",aws_secret_access_key="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",region_name="ap-south-1")
    #f=open("faces")
    #l=json.load(f)
    #.close()
    con=mysql.connect()
    cur=con.cursor()
    cur.execute("select usn,faceid from stu_auth where usn in (select usn from "+d[0]+")")
    res=cur.fetchall()
    cur.close()
    con.close()
    present=[]
    absent=[]
    response = client.index_faces(
	    CollectionId=d[0],
	    Image={
	        'S3Object': {
	            'Bucket': 'attendaceupload',
	            'Name': image_name,
	        }
	    },
	    ExternalImageId=image_name,
	    DetectionAttributes=[
	        'DEFAULT',
	    ],
	    MaxFaces=80,
	    QualityFilter='NONE'
	)
    temp_image_ids=[]
    for i in response["FaceRecords"]:
	       temp_image_ids.append(i["Face"]["FaceId"])
    try:
        for face in res:
        	if(client.search_faces(CollectionId=d[0],FaceId=face[1],MaxFaces=1)["FaceMatches"]):
        		present.append(face[0])
        	else:
        		absent.append(face[0])
    finally:
        response=client.delete_faces(CollectionId=d[0],FaceIds=temp_image_ids)

    return json.dumps({"present":present,"absent":absent})

	
@app.route('/update/<courseid>/<present>')
def update(courseid,present):
    # present=json.loads(present)
    con=mysql.connect()
    cur=con.cursor()
    cur.execute("update "+courseid+" set count=count+1 where usn in ("+present[1:-1:]+")")
    cur.execute('update courses set count=count+1 where cid="'+courseid+'"')
    cur.close()
    con.close()
    return 'OK'

@app.route('/attendance/<course_id>/<mac>/')
def attendance(course_id,mac):
    con = mysql.connect()
    with con:
        cur = con.cursor()
        cur.execute("UPDATE "+course_id+" SET count=count+1 where usn=(select usn from stu_auth where mac= '"+mac+"')")
    cur.close()
    con.close()
    return "OK"

@app.route('/teacher-login/<id>/<password>/')
def tlogin(id,password):
    con = mysql.connect()
    id=id.upper()
    with con:
        cur = con.cursor()
        cur.execute("select password from lec_details where id='"+id+"'");
        result=cur.fetchall()

    cur.close()
    con.close()
    # password= hashlib.md5(password).hexdigest()
    if result==None:
        return "user-not-found"
    if(result[0][0]==password):
        return "OK"
    else:
        return "wrong-password"

@app.route('/total-count/<courseid>/')
def total(courseid):
    con=mysql.connect()
    cur=con.cursor()
    cur.execute("update courses set count=count+1 where cid='"+courseid+"';commit;")
    cur.close()
    con.close()
    return 'OK'

@app.route('/student-register/<usn>/<mac>/<password>/')
def slogin(usn,mac,password):
    password = hashlib.md5(password).hexdigest()
    con = mysql.connect()
    cur=con.cursor()
    usn=usn.upper()
    cur.execute("select count(*) from stu_details where usn='" + usn + "'")
    res = cur.fetchall()
    cur.close()
    if res[0][0]==1:
        try:

            cur1 = con.cursor()
            cur1.execute("insert into stu_auth values('"+usn+"', '"+password+"', '"+mac+"');commit;")
            cur1.close()
            cur=con.cursor()
            cur.execute("select cid,cname from courses")
            result = cur.fetchall()
            cur.close()
            for row in result:
                cur=con.cursor()
                cur.execute("insert into "+row[0]+" values('"+usn+"', "+"0);commit;")
                cur.close()
            con.close()
            return 'OK'
        except:
            con.close()
            return 'ALREADY_REGISTERED'

    else :
        con.close()
        return 'INVALID_USER'

@app.route('/teacher-courses/<tid>/')
def tcourses(tid):
    con=mysql.connect()
    cur=con.cursor()
    cur.execute("select cid,cname from courses where tid='"+tid+"'")
    result = cur.fetchall()
    cur.close()
    con.close()

    final={}
    j=1

    for row in result:
        fdata = {}
        fdata['cid']=row[0]
        fdata['cname']=row[1]
        final["id"+str(j)]=fdata
        j+=1
    new = {'len': len(final), 'data': final}
    final = json.dumps(new)
    return final


@app.route('/courses/')
def courses():
    con = mysql.connect()
    cur = con.cursor()
    cur.execute("select cid,cname from courses")
    result =cur.fetchall()
    cur.close()
    con.close()

    final = {}
    i=1
    for row in result:
        fdata = {}
        fdata['cid'] = row[0]
        fdata['cname'] = row[1]
        final['id'+str(i)]=fdata
        i+=1
    new={'len':len(final),'data':final}
    final = json.dumps(new)
    return final

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0')
