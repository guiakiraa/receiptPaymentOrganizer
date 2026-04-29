from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
import io
import os
from src.logger import get_logger
from dotenv import load_dotenv

load_dotenv()

logger = get_logger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive"]


def _get_drive_service():
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "service-account.json")
    credentials = service_account.Credentials.from_service_account_file(
        cred_path,
        scopes=SCOPES
    )
    return build("drive", "v3", credentials=credentials)


def get_filename(file_id: str) -> str:
    logger.info(f"Buscando nome do arquivo: {file_id}")
    service = _get_drive_service()
    file = service.files().get(fileId=file_id, fields="name").execute()
    filename = file.get("name")
    logger.info(f"Nome do arquivo: '{filename}'")
    return filename


def download_file(file_id: str) -> bytes:
    logger.info(f"Baixando arquivo do Drive: {file_id}")
    service = _get_drive_service()

    request = service.files().get_media(fileId=file_id)
    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)

    done = False
    while not done:
        _, done = downloader.next_chunk()

    content = buffer.getvalue()
    logger.info(f"Download concluído — {len(content)} bytes")
    return content


def delete_file(file_id: str) -> None:
    logger.info(f"Deletando arquivo do Drive: {file_id}")
    service = _get_drive_service()
    service.files().delete(fileId=file_id).execute()
    logger.info("Arquivo deletado do Drive com sucesso!")


def list_files_in_folder(folder_id: str) -> list[dict]:
    logger.info(f"Listando arquivos da pasta: {folder_id}")
    service = _get_drive_service()

    query = (
        f"'{folder_id}' in parents "
        f"and mimeType != 'application/vnd.google-apps.folder' "
        f"and trashed = false"
    )

    results = service.files().list(
        q=query,
        fields="files(id, name, mimeType)"
    ).execute()

    files = results.get("files", [])
    logger.info(f"{len(files)} arquivo(s) encontrado(s) na pasta")
    return files