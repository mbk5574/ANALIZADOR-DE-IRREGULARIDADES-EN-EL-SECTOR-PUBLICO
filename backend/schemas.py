from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional
from datetime import date, datetime

class ScrapeRequest(BaseModel):
    """
Solicitud para iniciar un job de scraping.

Attributes:
    expediente (str):
        Identificador BOE del contrato. Debe cumplir el patron
        `BOE-[A|B]-YYYY-NNNNN`. Como por ejemplo: `BOE-B-2025-22668`.
    date (str):
        Fecha del contrato. Debe ser con el formato: `YYYYMMDD`.
    terms (List[str]):
        Lista de terminos de busqueda para el scraper.
    """
    expediente: str = Field(..., pattern=r"^BOE-[AB]-\d{4}-\d+$")
    date: str  
    terms: List[str]

class JobInfo(BaseModel):
    """
Informacion basica de un job de scraping.

Attributes:
    id (str):
        UUID que identifica el job.
    status (str):
        Estado actual del job (`pending`, `running`, `finished`, `failed`).
    created_at (datetime):
        Marca de tiempo de cuando se creó el job.
    """
    id: str
    status: str
    created_at: datetime

class ContractDetails(BaseModel):
    """
Detalles de un contrato obtenido del BOE.

Attributes:
    identificador (str):
        Código identificador del contrato en el BOE.
    titulo (str):
        Titulo o descripcion del contrato
    url_pdf (HttpUrl):
        Enlace al PDF del contrato
    organismo (Optional[str]):
        Nombre del organismo adjudicador.
    """
    identificador: str
    titulo: str
    url_pdf: HttpUrl
    organismo: Optional[str]

class Item(BaseModel):
    """
Representa un articulo resultante del scraping que contendra lo siguiente:.

Attributes:
    title (str):
        Título del artículo.
    link (HttpUrl):
        Enlace original al artículo.
    content_preview (Optional[str]):
        Fragmento de contenido donde se encontro el termino.
    source (Optional[str]):
        Nombre de la fuente o medio.
    author (Optional[str]):
        Autor del artículo (si se extrae).
    publication_date (Optional[datetime]):
        Fecha de publicación.
    contract_terms_found (List[str]):
        Términos de contrato detectados en el contenido.
    corruption_keywords_found (List[str]):
        Indicadores de corrupcion(o irregularidades que es un termino mas apropiado) detectados.
    sentiment_polarity (Optional[float]):
        Puntuación de sentimiento (iremos desde: -1 muy negativo a +1 muy positivo).
    risk_score (Optional[int]):
        Puntuación de riesgo calculada.
    date_scraped (datetime):
        Fecha y hora en que se realizo el scraping.
    entities (List[dict]):
        Entidades reconocidas, esto lo hacemos con NLP (pueden ser: personas, organizaciones, etc.).
    """
    title: str
    link: HttpUrl
    content_preview: Optional[str] = None
    source: Optional[str] = None
    author: Optional[str] = None
    publication_date: Optional[datetime] = None
    contract_terms_found: List[str] = []
    corruption_keywords_found: List[str] = []
    sentiment_polarity: Optional[float] = None
    risk_score: Optional[int] = None
    alert_level: Optional[str] = None
    date_scraped: datetime
    entities: List[dict]    