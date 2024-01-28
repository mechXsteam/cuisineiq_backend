import base64
import imghdr
from datetime import datetime
from io import BytesIO

import boto3
import joblib
import pytz
import qrcode
from botocore.exceptions import NoCredentialsError
from fastapi import HTTPException, status

from app.config import settings

s3_client = boto3.client(
        "s3",
        region_name="ap-south-1",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)


def get_current_time():
        return datetime.utcnow().replace(tzinfo=pytz.utc).astimezone(pytz.timezone('Asia/Kolkata'))


def validate_image_type(image):
        if imghdr.what(image) not in ['jpeg', 'png', 'jpg']:
                return False
        return True


def upload_file_to_s3(file, bucket, object_name=None):
        if object_name is None:
                object_name = file.filename
        try:
                s3_client.upload_fileobj(file.file, bucket, object_name)
        except NoCredentialsError:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not connect to AWS with provided credentials")
        return f"https://{bucket}.s3.amazonaws.com/{object_name}"


def generate_qr(data):
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img_bytesio = BytesIO()
        img.save(img_bytesio)
        img_base64 = base64.b64encode(img_bytesio.getvalue()).decode("utf-8")
        return img_base64


def generate_tags(description: str):
        # Load the dictionary of models
        saved_dict = joblib.load("app/utils/cuisine_generation.joblib")

        # Convert the description to TF-IDF features
        tfidf_vectorizer = saved_dict['vectorizer']
        models = saved_dict['models']

        # Create an empty dictionary to store predictions for each tag
        predictions_dict = {}
        new_description_tfidf = tfidf_vectorizer.transform([description])
        # Make predictions for each tag using the respective models
        for tag, model in models.items():
                tag_prediction = model.predict(new_description_tfidf)
                predictions_dict[tag] = tag_prediction[0]

        # Return the predictions
        return predictions_dict


def delete_file_from_s3(file_name, bucket):
        try:
                s3_client.delete_object(Bucket=bucket, Key=file_name)
        except NoCredentialsError:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not connect to AWS with provided credentials")
        return True
