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
    
    intruder=len(temp_image_ids)-len(present)
    return json.dumps({"present":present,"absent":absent, "intruder":intruder})

	
@app.route('/update/<courseid>/<present>')
def update(courseid,present):
    con=mysql.connect()
    cur=con.cursor()
    cur.execute("update "+courseid+" set count=count+1 where usn in ("+present[1:-1:]+")")
    cur.execute('update courses set count=count+1 where cid="'+courseid+'"')
    cur.execute('commit;')
    cur.close()
    con.close()
    return 'OK'

@app.route('/teacher-login/<id>/<password>/')
def tlogin(id,password):
    con = mysql.connect()
    id=id.upper()
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


# @app.route('/courses/')
# def courses():
#     con = mysql.connect()
#     cur = con.cursor()
#     cur.execute("select cid,cname from courses")
#     result =cur.fetchall()
#     cur.close()
#     con.close()

#     final = {}
#     i=1
#     for row in result:
#         fdata = {}
#         fdata['cid'] = row[0]
#         fdata['cname'] = row[1]
#         final['id'+str(i)]=fdata
#         i+=1
#     new={'len':len(final),'data':final}
#     final = json.dumps(new)
#     return final

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0',port=8080)
