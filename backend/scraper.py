"""
backend/scraper.py

Este modulo inicia el proceso de scraping externo (usando Scrapy) y actualiza
el estado de los jobs en la base de datos.
"""
import subprocess
import pathlib
from pathlib import Path
from .db import SessionLocal
from .models import ScrapeJob, JobStatus
import json
import logging

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


logger = logging.getLogger(__name__)


def update_job_status(job_id: str, status: JobStatus):
    """
Actualiza el estado de un job existente en la base de datos.

Args:
    job_id (str): UUID que identifica el job.
    status (JobStatus): Nuevo estado que puede ser; (pending, running, finished, failed).
    """
    db = SessionLocal()
    try:
        job = db.get(ScrapeJob, job_id) if hasattr(db, "get") \
              else db.query(ScrapeJob).filter_by(id=job_id).first()
        if job:
            job.status = status
            db.commit()
    finally:
        db.close()


def launch_scrape(terms: list[str], result_path: str, job_id: str):
    """
Ejecuta el crawler de Scrapy como un subproceso y gestiona el flujo de estados.
Los pasos que sigue son:
1. Crea la carpeta de resultados si no existe.
2. Construye y ejecuta el comando de Scrapy.
3. Al terminar, actualiza el estado a finished o failed segun sea el caso.
4. Normaliza el JSON de salida (asegura de esta manera un formato válido).

Args:
    terms (list[str]): Lista de terminos de busqueda que recibe el spider.
    result_path (str): Ruta donde Scrapy volcara los resultados en JSON.
    job_id (str): UUID del job para actualizar su estado.
    """
    try:
        RESULTS_DIR.mkdir(exist_ok=True)

        contract_terms_str = ",".join(terms)
        command = [
            "scrapy", "crawl", "multisource_spider",
            "-a", f"contract_terms={contract_terms_str}",
            "-o", result_path,
            "-a", f"result_path={result_path}",
        ]

        backend_dir = pathlib.Path(__file__).resolve().parent
        project_path = backend_dir.parent / "corruption_detector"
        subprocess.run(command, cwd=str(project_path), check=True)

        update_job_status(job_id, JobStatus.finished)
        try:
            with open(result_path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            logger.warning(f"Resultados mal formados para job {job_id}, volcando una lista vacía.")
            data = []
        try:
            with open(result_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            logger.error(f"No se pudo reescribir resultados para job {job_id}: {e}")


    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Error durante el scraping para el job {job_id}: {e}")
        update_job_status(job_id, JobStatus.failed)
