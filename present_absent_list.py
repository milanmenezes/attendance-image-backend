from flask import Flask,render_template
import boto3
import json

app = Flask(__name__)

@app.route("process/<image_name>")
def process(image_name) :
    d=image_name.split("_")
    client = boto3.client('rekognition')
    f=open("faces")
    l=json.load(f)
    f.close()
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
    for face in l:
    	if(client.search_faces(CollectionId=d[0],FaceId=face["face-id"],MaxFaces=1)["FaceMatches"]):
    		present.append(face['usn'])
    	else:
    		absent.append(face['usn'])

    response=client.delete_faces(CollectionId=d[0],FaceIds=temp_image_ids)
    dict={"Present":present,"Absent":absent}
    return dict
    #return render_template("index.html",present=present,absent=absent)

if __name__ == "__main__":
	app.run(host='0.0.0.0', port=80)

