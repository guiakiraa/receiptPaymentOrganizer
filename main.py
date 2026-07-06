import functions_framework
from src.classifier.classifier import classify_file
from src.storage.gcs import upload_file
from src.drive.drive import list_files_in_folder, download_file, delete_file
from src.logger import get_logger
import os
from dotenv import load_dotenv

load_dotenv()

logger = get_logger(__name__)


@functions_framework.http
def run(request):
    logger.info("========== Smart Receipt Organizer iniciado ==========")

    folder_id = os.getenv("DRIVE_FOLDER_ID")
    if not folder_id:
        logger.error("DRIVE_FOLDER_ID não configurado")
        return {"status": "error", "message": "DRIVE_FOLDER_ID é obrigatório"}, 400

    try:
        files = list_files_in_folder(folder_id)

        if not files:
            logger.info("Nenhum arquivo encontrado na pasta — nada a processar.")
            return {"status": "success", "message": "Nenhum arquivo para processar"}, 200

        logger.info(f"{len(files)} arquivo(s) encontrado(s) para processar")

        results = []
        errors = []

        for file in files:
            file_id = file["id"]
            original_filename = file["name"]

            logger.info(f"--- Processando: '{original_filename}' ---")

            try:
                classification = classify_file(original_filename)
                category = classification["category"]
                new_filename = classification["new_filename"]

                file_content = download_file(file_id)

                gcs_uri = upload_file(
                    file_content=file_content,
                    category=category,
                    new_filename=new_filename
                )

                delete_file(file_id)

                logger.info(f"✅ '{original_filename}' → '{new_filename}' salvo em {gcs_uri}")

                results.append({
                    "original_filename": original_filename,
                    "new_filename": new_filename,
                    "category": category,
                    "gcs_uri": gcs_uri
                })

            except Exception as e:
                logger.error(f"❌ Erro ao processar '{original_filename}': {str(e)}")
                errors.append({
                    "filename": original_filename,
                    "error": str(e)
                })
                continue

        logger.info(f"========== Concluído: {len(results)} sucesso(s), {len(errors)} erro(s) ==========")

        return {
            "status": "success",
            "processed": len(results),
            "errors": len(errors),
            "results": results,
            "failed": errors
        }, 200

    except Exception as e:
        logger.error(f"Erro geral durante a execução: {str(e)}")
        return {"status": "error", "message": str(e)}, 500