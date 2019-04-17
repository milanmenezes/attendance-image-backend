from flask import Flask
import hashlib
import json
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
    app.run(debug=True, host='0.0.0.0')
