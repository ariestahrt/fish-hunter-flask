import os
import boto3
from flask import current_app

logger = current_app.config["LOGGER"]

'''
    Downloads a file from S3
    return the path to the file
'''
def s3_download(s3_path):
    logger.info("Downloading file from S3")
    save_to = os.path.join(current_app.config["BASE_DIR"], "files/downloads", s3_path)
    
    # check if file exists
    if os.path.exists(save_to):
        return save_to

    s3 = boto3.client('s3', aws_access_key_id=current_app.config["AWS_ACCESS_KEY"], aws_secret_access_key=current_app.config["AWS_SECRET_KEY"])
    with open(save_to, 'wb') as f:
        s3.download_fileobj("fish-hunter", s3_path, f)
    
    return save_to

'''
    Uploads a file to S3
    return True if successful
'''
def s3_upload(bucket, local_file, dest):
    logger.info("Uploading file to S3")
    # Note: This is only for images
    s3 = boto3.client('s3', aws_access_key_id=current_app.config["AWS_ACCESS_KEY"], aws_secret_access_key=current_app.config["AWS_SECRET_KEY"])

    try:
        s3.upload_file(local_file, bucket, dest, ExtraArgs={'ContentType': 'image/jpg'})
        logger.info("File uploaded successfully")
        return True
    except FileNotFoundError:
        logger.error("The file was not found")
        return False