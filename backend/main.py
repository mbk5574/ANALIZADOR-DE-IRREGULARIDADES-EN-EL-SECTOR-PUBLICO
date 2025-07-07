"""
Main module del backend FastAPI para el TFG "Analizador de Irregularidades".
Basicamente es una API REST que permite interactuar con el sistema de scraping
y analisis de contratos públicos en España, centrándose en la detección de
irregularidades. Este módulo expone los endpoints para:
1. Subir y procesar un PDF de contrato.
2. Consultar detalles de un contrato en el BOE.
3. Crear, monitorizar y recuperar resultados de jobs de scraping.
4. Exportar resultados a CSV.

También configura CORS, monta ficheros estáticos y gestiona el ciclo de vida de la aplicación.
"""


from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query, Path as PathParam, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from typing import List
from uuid import uuid4
import os, json, logging, httpx
from corruption_detector.spiders.corruption_spider import BASE_CORRUPTION_INDICATORS
from .db import SessionLocal, init_db
from .models import ScrapeJob, JobStatus
from .schemas import JobInfo, Item, ScrapeRequest
from .scraper import launch_scrape
from pathlib import Path as FSPath
from .contract_processor import process_award_notice 
from fastapi import UploadFile, File             



# ——————————————————————————————————————————————————————————————————————
# Configuración de logging
# ——————————————————————————————————————————————————————————————————————
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(name)s │ %(message)s")
logger = logging.getLogger(__name__)




# ——————————————————————————————————————————————————————————————————————
# Directorios de resultados(los json y csv) y uploads(los pdfs de los contratos)
# ——————————————————————————————————————————————————————————————————————
RESULTS_DIR = FSPath(__file__).resolve().parent / "results"
UPLOAD_DIR = RESULTS_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


# ——————————————————————————————————————————————————————————————————————
# Ciclo de vida de FastAPI: init_db en arranque(es una funcion asincrona de fastapi para gestionar el arranque y apagado).
# —————————————————————————————————————————————————————————————————————— 
@asynccontextmanager
async def lifespan(app: FastAPI):
    #Arranque: inicializamos la base de datos y crea la tabla jobs en caso de que no exista.
    init_db()
    yield  


# ——————————————————————————————————————————————————————————————————————
# Creación de la aplicación FastAPI donde se define algo muy importante:
# el middleware CORS para permitir peticiones entre el frontend y el backend. Al estar ambos en distintos puertos, el frontend(5173) y el backend(8000), necesitamos permitir CORS para que el navegador no bloquee las peticiones.
# ——————————————————————————————————————————————————————————————————————
app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

"""Dependency de FastAPI: proporciona una sesión de base de datos y la cierra al finalizar de forma segura."""
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

"""Tambien hacemos visible el directorio de resultados para que el frontend pueda acceder a los JSON y CSV generados por los jobs de scraping y descargar los resultados"""
app.mount("/results", StaticFiles(directory=RESULTS_DIR), name="results")

# ——————————————————————————————————————————————————————————————————————
# Endpoints publicos
# ——————————————————————————————————————————————————————————————————————
@app.get("/indicators")
def get_indicators():
    """Devuelve la lista base de indicadores de corrupción."""
    return BASE_CORRUPTION_INDICATORS


# ——————————————————————————————————————————————————————————————————————
# 1) Endpoint para subir un contrato en PDF
# ——————————————————————————————————————————————————————————————————————
@app.post("/upload_contract")
async def upload_contract(file: UploadFile = File(...)) -> dict:
    """
Sube un PDF de contrato, lo guarda y extrae términos y metadatos.

Args:
file (UploadFile): El PDF enviado por el usuario.

Returns:
dict: {
"terms": List[str], 
"notice": {
"adjudicatario": str,
"entidad": str,
"objeto": str
}
}
    """
    job_pdf = UPLOAD_DIR / f"{uuid4()}.pdf"
    with open(job_pdf, "wb") as f:
        f.write(await file.read())
    terms, notice = process_award_notice(str(job_pdf))
    return {
        "terms": terms,
        "notice": {
            "adjudicatario": notice.adjudicatario_nombre,
            "entidad":      notice.entidad_adjudicadora,
            "objeto":       notice.objeto_contrato,
        }
    }


# ——————————————————————————————————————————————————————————————————————
# 2) Endpoint de detalle de contrato BOE
# ——————————————————————————————————————————————————————————————————————

def extract_items_and_depts(node, dept_map=None, parent_dept=None):
    """
Recorre recursivamente la estructura JSON del BOE y extrae todos los items,
de esta manera conseguiremos construir un mapa identificador --> departamento.

Args:
    node: Nodo actual (dict o list) en el JSON.
    dept_map: Mapa acumulado de identificador a departamento.
    parent_dept: Nombre del departamento padre.

Returns:
    Lista de diccionarios con los ítems encontrados.
    """
    if dept_map is None:
        dept_map = {}
    items = []
    if isinstance(node, dict):
        dept_name = node.get('nombre') or parent_dept
        it = node.get('item')
        if it:
            if isinstance(it, list):
                for entry in it:
                    items.append(entry)
                    dept_map[entry['identificador']] = dept_name
            else:
                items.append(it)
                dept_map[it['identificador']] = dept_name
        for key, value in node.items():
            if key in ('departamento', 'seccion', 'epigrafe'):
                items += extract_items_and_depts(value, dept_map, dept_name)
    elif isinstance(node, list):
        for elem in node:
            items += extract_items_and_depts(elem, dept_map, parent_dept)
    return items



# ——————————————————————————————————————————————————————————————————————
# 3) Endpoint de consulta de contrato en el BOE, el procesamiento se hace en extract_items_and_depts(el anterior).
# ——————————————————————————————————————————————————————————————————————
@app.get("/contracts/{fecha}/{expediente:path}")
async def get_contract_details(
    fecha: str = PathParam(..., regex=r"^\d{8}$"),
    expediente: str = PathParam(...)
):
    """
Obtiene detalles de un contrato concreto desde la API abierta del BOE.

Args:
fecha (str): Fecha en formato AAAAMMDD.
expediente (str): Identificador del contrato en el formato BOE...

Returns:
dict: {
"identificador": str,
"titulo": Optional[str],
"url_pdf": Optional[str],
"organismo": Optional[str]
}

Raises:
HTTPException(503): Error de red al consultar el BOE.
HTTPException(404): Si no existe sumario o no se encuentra el expediente.
    """
    url = f"https://www.boe.es/datosabiertos/api/boe/sumario/{fecha}"
    logger.debug(f"📡 Fetch BOE: {url}")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, headers={"Accept": "application/json"})
    except httpx.RequestError as e:
        logger.error(f"Error de red fetching BOE: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                            detail="Error de red consultando el BOE.")
    if resp.status_code != 200:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="No hay sumario para esa fecha en el BOE.")

    raw = resp.json()
    data = raw.get('data') or raw.get('datos') or raw
    sumario = data.get('sumario', {})
    diario = sumario.get('diario', [])
    if not diario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="No hay datos de diario para esa fecha.")
    diario = diario[0]

    dept_map = {}
    flat_items = extract_items_and_depts(diario, dept_map)
    anuncio = next((it for it in flat_items if it.get('identificador') == expediente), None)
    if not anuncio:
        disponibles = [it['identificador'] for it in flat_items]
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "Identificador no encontrado", "disponibles": disponibles}
        )

    return {
        "identificador": anuncio['identificador'],
        "titulo": anuncio.get('titulo'),
        "url_pdf": anuncio.get('url_pdf', {}).get('texto'),
        "organismo": dept_map.get(anuncio['identificador'])
    }


# ——————————————————————————————————————————————————————————————————————
# 4) Endpoint de creación de jobs de scraping
# ——————————————————————————————————————————————————————————————————————

@app.post("/scrape", response_model=JobInfo, status_code=status.HTTP_202_ACCEPTED)
def create_scrape_job(
    request: ScrapeRequest,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
Crea un nuevo job de scraping.

Args:
    request (ScrapeRequest): Esto incluye la lista de términos y la fecha y expediente.
    background (BackgroundTasks): Nos permite ejecutar launch_scrape en segundo plano.
    db (Session): Sesión de base de datos inyectada.

Returns:
    JobInfo: { id: str, status: str, created_at: str }

Raises:
    HTTPException(400): Si no hay términos indicados para realizar la busqueda por el usuario.
    """
    if not request.terms:
        raise HTTPException(status_code=400, detail="Debes indicar al menos un término de búsqueda")

    job_id = str(uuid4())
    RESULTS_DIR.mkdir(exist_ok=True)
    result_path = str(RESULTS_DIR / f"{job_id}.json")

    terms_json = json.dumps(request.terms, ensure_ascii=False)
    job = ScrapeJob(
        id=job_id,
        terms=terms_json,
        status=JobStatus.running,
        result_path=result_path,
    )
    
    db.add(job)
    db.commit()

    background.add_task(launch_scrape, request.terms, result_path, job_id)

    return JobInfo(id=job_id, status=job.status.value, created_at=job.created_at.isoformat())


# ——————————————————————————————————————————————————————————————————————
# 5) Endpoint de consulta de estado de job
# ——————————————————————————————————————————————————————————————————————

@app.get("/jobs/{job_id}", response_model=JobInfo)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """
Consulta el estado de un job.

Args:
    job_id (str): UUID del job.
    db (Session): Sesión de base de datos.

Returns:
    JobInfo: id, status, created_at.

Raises:
    HTTPException(404): Si no existe el job.
    """
    job = db.get(ScrapeJob, job_id) if hasattr(db, "get") \
          else db.query(ScrapeJob).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail={"error":"Job no encontrado", "job_id":job_id})
    return JobInfo(id=job.id, status=job.status.value, created_at=job.created_at.isoformat())


# ——————————————————————————————————————————————————————————————————————
# 5) Endpoint de consulta de resultados de job
# ——————————————————————————————————————————————————————————————————————

@app.get("/jobs/{job_id}/results", response_model=List[Item])
def get_job_results(
    job_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """
Recuperamos la lista de resultados en formato JSON de un job finalizado, incluyendo paginación.

Args:
    job_id (str): UUID del job.
    skip (int): Offset a omitir.
    limit (int): Número máximo de items a devolver.
    db (Session): Sesión de base de datos.

Returns:
    List[Item]: Lista de items encontrados (la cual puede estar vacía sino se encuentra nada).

Raises:
    HTTPException(404): Si no existe el job.
    HTTPException(202): Si el job aún no ha terminado.
    """
    job = db.get(ScrapeJob, job_id) if hasattr(db, "get") \
          else db.query(ScrapeJob).filter_by(id=job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job no encontrado")
    if job.status != JobStatus.finished:
        raise HTTPException(status_code=status.HTTP_202_ACCEPTED,
                            detail="Job en curso, inténtalo más tarde por favor.")
    if not os.path.isfile(job.result_path) or os.path.getsize(job.result_path) == 0:
        return []

    with open(job.result_path, encoding="utf-8") as f:
        raw = json.load(f)

    cleaned = []
    for it in raw[skip : skip + limit]:
        if not it.get("publication_date"):
            it.pop("publication_date", None)
        cleaned.append(it)

    return cleaned


# ——————————————————————————————————————————————————————————————————————
# 6) Endpoint para exportar resultados a CSV
# ——————————————————————————————————————————————————————————————————————

@app.get("/jobs/{job_id}/results.csv")
def export_results_csv(job_id: str, db: Session = Depends(get_db)):
    """
Exporta los resultados de un job a CSV mediante un streaming.

Args:
    job_id (str): UUID del job.
    db (Session): Sesión de base de datos.

Returns:
    StreamingResponse: Flujo CSV con encabezados y las filas de datos.

Raises:
    HTTPException(404): Si el job no existe o no ha finalizado.
    """
    job = db.get(ScrapeJob, job_id) if hasattr(db, "get") \
          else db.query(ScrapeJob).filter_by(id=job_id).first()
    if not job or job.status != JobStatus.finished:
        raise HTTPException(status_code=404, detail="Job no encontrado o no finalizado")

    def iter_csv():
        headers = ["title","link","source","publication_date","indicator_count","content_length","sentiment_polarity","entities"]
        yield ",".join(headers) + "\n"
        with open(job.result_path, encoding="utf-8") as f:
            data = json.load(f)
        for it in data:
            ents = ";".join(f"{e['text']}[{e['label']}]" for e in it.get("entities", []))
            row = [
                it.get("title","").replace(",", " "),
                it.get("link",""),
                it.get("source",""),
                it.get("publication_date",""),             
                str(it.get("indicator_count", 0)),        
                str(it.get("content_length", 0)),         
                str(it.get("sentiment_polarity","")),
                ents
            ]
            yield ",".join(row) + "\n"

    return StreamingResponse(iter_csv(), media_type="text/csv")
