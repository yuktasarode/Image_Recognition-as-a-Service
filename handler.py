#__copyright__   = "Copyright 2024, VISA Lab"
#__license__     = "MIT"


import boto3
import os
from urllib.parse import unquote_plus


import os
import imutils
import cv2
import json
from PIL import Image, ImageDraw, ImageFont
from facenet_pytorch import MTCNN, InceptionResnetV1
from shutil import rmtree
import numpy as np
import torch

mtcnn = MTCNN(image_size=240, margin=0, min_face_size=20) # initializing mtcnn for face detection
resnet = InceptionResnetV1(pretrained='vggface2').eval() # initializing resnet for face img to embeding conversion

s3 = boto3.client('s3')

def face_recognition_function(key_path):
    # Face extraction
    img = cv2.imread(key_path, cv2.IMREAD_COLOR)
    boxes, _ = mtcnn.detect(img)

    # Face recognition
    key = os.path.splitext(os.path.basename(key_path))[0].split(".")[0]
    img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    face, prob = mtcnn(img, return_prob=True, save_path=None)
    saved_data = torch.load('/tmp/data.pt')  # loading data.pt file
    if face != None:
        emb = resnet(face.unsqueeze(0)).detach()  # detech is to make required gradient false
        embedding_list = saved_data[0]  # getting embedding data
        name_list = saved_data[1]  # getting list of names
        dist_list = []  # list of matched distances, minimum distance is used to identify the person
        for idx, emb_db in enumerate(embedding_list):
            dist = torch.dist(emb, emb_db).item()
            dist_list.append(dist)
        idx_min = dist_list.index(min(dist_list))

        # Save the result name in a file
        with open("/tmp/" + key + ".txt", 'w+') as f:
            f.write(name_list[idx_min])
        return name_list[idx_min]
    else:
        print(f"No face is detected")
    return



def handler(event, context):
    

	print(event)
	bucket = event['bucket_name']
	print(bucket)
	key = event['image_file_name']
	input_img_name = key[:-4]
	print("key",key)
	print("Input Img: ",input_img_name)
	
	local_img_path = f"/tmp/{key}"
     
	s3.download_file(bucket, key, local_img_path)
	s3.download_file("modelpt", "data.pt", "/tmp/data.pt")

	result = face_recognition_function(local_img_path)

	print(result)
	
	output_bucket = "1225266406-output"
	
	if any(result):
		s3.upload_file("/tmp/" + input_img_name + ".txt", output_bucket, input_img_name+".txt")	

	print("Done")
