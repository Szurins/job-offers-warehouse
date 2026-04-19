import os

import boto3
from botocore.exceptions import ClientError
from justjoinit_offers.justJoinIt import load_justJoinIt_offers

ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
SECRET_KEY = os.getenv("AWS_SECRET_KEY")

BUCKET_NAME = "job-offers-data"
REGION = "eu-central-1"

s3 = boto3.client(
    "s3",
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name=REGION,
)


# Function to create bucket if not exists
def create_bucket_if_not_exists(bucket_name):
    try:
        s3.head_bucket(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' already exists.")
    except ClientError as e:
        error_code = int(e.response["Error"]["Code"])

        if error_code == 404:
            print(f"Bucket '{bucket_name}' does not exist. Creating...")
            if REGION == "us-east-1":
                s3.create_bucket(Bucket=bucket_name)
            else:
                s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={"LocationConstraint": REGION},
                )
            print("Bucket created.")
        else:
            raise


# Ensure bucket exists
create_bucket_if_not_exists(BUCKET_NAME)

# Create folders
FOLDER_NAMES = ["raw", "bronze", "silver", "gold"]
for folder in FOLDER_NAMES:
    s3.put_object(Bucket=BUCKET_NAME, Key=f"{folder}/")

load_justJoinIt_offers()

files = os.listdir("./justjoinit_offers/json_files/")
for file in files:
    s3.upload_file(
        f"./justjoinit_offers/json_files//{file}",
        BUCKET_NAME,
        f"raw/just_join_it/{file}",
    )

print("File uploaded successfully.")
