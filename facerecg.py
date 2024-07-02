import boto3
import os
from urllib.parse import unquote_plus
import json

s3 = boto3.client('s3')
lambda_client = boto3.client('lambda')

def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    print(bucket)
    key = unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    input_video_name = os.path.splitext(os.path.basename(key))[0]
    print("key",key)
    print("Input Video: ",input_video_name)

    # Update the FFmpeg command to split the video
    # ffmpeg_command = f"ffmpeg -ss 0 -r 1 -i /tmp/{key} -vf fps=1/10 -start_number 0 -vframes 10 /tmp/{input_video_name}/output_%02d.jpg -y"
    
    ffmpeg_command = 'ffmpeg -i /tmp/' + key + ' -vframes 1 ' + '/tmp/' + input_video_name +'.jpg'

    # Download the video file from S3
    local_video_path = f"/tmp/{key}"
    s3.download_file(bucket, key, local_video_path)
    
   
    print("Downloaded video file")


    # Execute FFmpeg command to split the video
    os.system(ffmpeg_command)
    print("video -> Img")

    # Upload the output images to yukta-stage-1 bucket
    stage_1_bucket = '1225266406-stage-1'
    img_path = f"{input_video_name}.jpg"
    s3.upload_file(f'/tmp/{img_path}', stage_1_bucket, img_path)
    
    
    print("Inside output")
    
    payload = {
        "bucket_name": stage_1_bucket,
        "image_file_name": img_path
    }

    # Invoke the Lambda function asynchronously
    lambda_client.invoke(
        FunctionName='face-recognition',  # Provide the name of your face_recognition Lambda function
        InvocationType='Event',
        Payload=json.dumps(payload)
    )
    
    print("Face recognition invo")
  
