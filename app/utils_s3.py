import boto3
import os
import uuid
from flask import current_app

def upload_file_to_s3(file_obj, filename, content_type=None):
    """
    Uploads a file object to S3 and returns the public URL.
    """
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=current_app.config["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=current_app.config["AWS_SECRET_ACCESS_KEY"],
        region_name=current_app.config["AWS_REGION"]
    )
    
    bucket_name = current_app.config["AWS_S3_BUCKET_NAME"]
    
    # Generate unique filename to avoid collisions
    ext = os.path.splitext(filename)[1]
    unique_filename = f"{uuid.uuid4()}{ext}"
    
    extra_args = {}
    if content_type:
        extra_args["ContentType"] = content_type
        # Assuming public read for OpenAI access
        # extra_args["ACL"] = "public-read" 
        # Note: ACLs might be disabled on the bucket, in which case bucket policy controls access.

    try:
        s3_client.upload_fileobj(
            file_obj,
            bucket_name,
            unique_filename,
            ExtraArgs=extra_args
        )
    except Exception as e:
        print(f"S3 Upload Error: {e}")
        raise e

    # Construct Public URL
    # Format: https://{bucket}.s3.{region}.amazonaws.com/{key}
    region = current_app.config["AWS_REGION"]
    url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{unique_filename}"
    
    return url
