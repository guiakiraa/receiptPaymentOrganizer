from google.cloud import storage
import os
from src.logger import get_logger
from dotenv import load_dotenv

load_dotenv()

logger = get_logger(__name__)

def upload_file(
    file_content: bytes,
    category: str,
    new_filename: str
) -> str:
    bucket_name = os.getenv("GCS_BUCKET_NAME")

    if not bucket_name:
        raise ValueError("Variável de ambiente GCS_BUCKET_NAME é obrigatória.")

    client = storage.Client()
    bucket = client.bucket(bucket_name)

    destination_path = f"{category}/{new_filename}"
    blob = bucket.blob(destination_path)

    logger.info(f"Fazendo upload para gs://{bucket_name}/{destination_path}")

    blob.upload_from_string(
        file_content,
        content_type=_get_content_type(new_filename)
    )

    gcs_uri = f"gs://{bucket_name}/{destination_path}"
    logger.info(f"Upload concluído: {gcs_uri}")

    return gcs_uri


def _get_content_type(filename: str) -> str:
    extension = filename.split(".")[-1].lower()
    content_types = {
        "pdf": "application/pdf",
        "png": "image/png",
        "jpeg": "image/jpeg",
        "jpg": "image/jpeg",
    }
    return content_types.get(extension, "application/octet-stream")