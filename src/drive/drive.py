from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import google.auth
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import io
import os
import json
from src.logger import get_logger
from dotenv import load_dotenv
from google.cloud import secretmanager

load_dotenv()

logger = get_logger(__name__)

SERVICE_ACCOUNT_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
OAUTH_SCOPES = ["https://www.googleapis.com/auth/drive"]


def _save_token_to_secret_manager(creds):
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.getenv("GCP_PROJECT_ID")
    secret_name = f"projects/{project_id}/secrets/OAUTH_TOKEN"

    client.add_secret_version(
        request={
            "parent": secret_name,
            "payload": {"data": creds.to_json().encode("utf-8")}
        }
    )
    logger.info("Token OAuth atualizado no Secret Manager")


def _get_service_account_service():
    credentials, _ = google.auth.default(scopes=SERVICE_ACCOUNT_SCOPES)
    return build("drive", "v3", credentials=credentials)


def _get_oauth_service():
    token_file = os.getenv("OAUTH_TOKEN_FILE", "oauth-token.json")
    credentials_file = os.getenv("OAUTH_CREDENTIALS_FILE", "oauth-credentials.json")

    creds = None

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, OAUTH_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            logger.info("Renovando token OAuth...")
            creds.refresh(Request())
            _save_token_to_secret_manager(creds)
        else:
            logger.info("Iniciando fluxo OAuth — abrirá o navegador...")
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_file,
                OAUTH_SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(token_file, "w") as f:
            f.write(creds.to_json())
        logger.info("Token OAuth salvo com sucesso!")

    return build("drive", "v3", credentials=creds)


def get_filename(file_id: str) -> str:
    logger.info(f"Buscando nome do arquivo: {file_id}")
    service = _get_service_account_service()
    file = service.files().get(
        fileId=file_id,
        fields="name"
    ).execute()
    filename = file.get("name")
    logger.info(f"Nome do arquivo: '{filename}'")
    return filename


def download_file(file_id: str) -> bytes:
    logger.info(f"Baixando arquivo do Drive: {file_id}")
    service = _get_service_account_service()

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
    logger.info(f"Deletando arquivo do Drive via OAuth: {file_id}")
    service = _get_oauth_service()
    service.files().delete(fileId=file_id).execute()
    logger.info("Arquivo deletado do Drive com sucesso!")


def list_files_in_folder(folder_id: str) -> list[dict]:
    logger.info(f"Listando arquivos da pasta: {folder_id}")
    service = _get_service_account_service()

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