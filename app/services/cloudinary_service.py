import cloudinary
import time
import cloudinary.uploader
from app.core.config import CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET,
    secure=True
)

def get_cloudinary_signature():
    timestamp = int(time.time())
    params_to_sign = {
        "timestamp": timestamp,
        "folder": "pdfs",
        "resource_type": "raw",
    }

    signature = cloudinary.utils.api_sign_request(
        params_to_sign, cloudinary.config().api_secret
    )

    return {
        "timestamp": timestamp,
        "signature": signature,
        "api_key": cloudinary.config().api_key,
        "cloud_name": cloudinary.config().cloud_name,
        "folder": params_to_sign["folder"],
    }


def upload_pdf_to_cloudinary(file_path: str) -> str:
    result = cloudinary.uploader.upload(
        file_path,
        resource_type="raw",
        folder="pdfs"
    )
    return result.get("secure_url")

def delete_pdf_from_cloudinary(file_url: str):
    public_id = file_url.split("/")[-1].split(".")[0]  # crude but safe for now
    cloudinary.uploader.destroy(f"pdfs/{public_id}", resource_type="raw")
