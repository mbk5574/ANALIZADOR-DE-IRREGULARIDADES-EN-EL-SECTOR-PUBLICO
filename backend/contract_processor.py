import fitz     # PyMuPDF
import os, re, logging
from typing import List, Tuple, Optional
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

#sufijos que quitamos de los nombres de empresa para normalizar el termino lo maximo posible
SUFFIXES_TO_STRIP = [
    "S.L.U", "S.L.N.E", "S.L.P", "S.L.L", "S.A.U", "S.A.D", "S.L", "S.A",
    "U.T.E", "UTE", "INC", "LTD", "LLC", "GMBH"
]

def normalize_search_term(term: str) -> str:
    """
Elimina sufijos legales de una razón social para obtener su nombre base que es lo que realmente nos interesa.

Args:
    term: Cadena con el nombre completo, incluyendo posibles sufijos.

Returns:
    Nombre simplificado sin sufijos como S.L., S.A., UTE, etc.
    """
    for suf in SUFFIXES_TO_STRIP:
        term = re.sub(rf"(,\s*)?{re.escape(suf)}\.?$", "", term, flags=re.IGNORECASE)
    return term.strip()

def extract_text_from_pdf(pdf_path: str) -> str:
    """
Extrae todo el texto de un PDF manteniendo saltos de línea por página.

Args:
    pdf_path: Ruta al archivo PDF.

Returns:
    Texto completo concatenado de todas las paginas, o tambien una cadena vacia en caso de que falle.
    """
    if not os.path.exists(pdf_path):
        logging.error(f"Archivo no encontrado: {pdf_path}")
        return ""
    doc = fitz.open(pdf_path)
    text = "\n".join(page.get_text("text") for page in doc)
    return text.replace('–', '-').replace('—', '-').strip()

@dataclass
class SimpleNotice:
    """
Representa la información minima extraída de un aviso de adjudicacion.

Attributes:
    adjudicatario_nombre: Nombre del adjudicatario de la adjudicacion.
    entidad_adjudicadora: Nombre del organismo o entidad adjudicadora.
    objeto_contrato: Texto que describe el objeto del contrato adjudicado.
    """
    adjudicatario_nombre: Optional[str]
    entidad_adjudicadora: Optional[str]
    objeto_contrato:    Optional[str]

def extract_raw_data(text: str) -> dict:
    
    """
Busca patrones claves en el texto extraido para obtener metadato, es la manera en que conseguimos extraer cada uno de los terminos relevantes.

Patrones:
    - Adjudicatario: linea que suele seguir al texto "Adjudicatario".
    - Entidad adjudicadora: línea tras "Entidad Adjudicadora".
    - Objeto del Contrato: linea tras "Objeto del Contrato".

Args:
    text: Texto completo del PDF.

Returns:
    Diccionario con claves parciales: "adjudicatario_nombre", "entidad_adjudicadora", "objeto_contrato".
    """
    
    r = {}

    #1)Adjudicatario: en este caso sabemos que va desde “Adjudicatario:” hasta fin de línea o “Importes de Adjudicación”
    m = re.search(
        r"Adjudicatario\s*[:\n]\s*([^\n]+?)(?=\n|Importes de Adjudicación|$)",
        text,
        re.IGNORECASE
    )
    if m:
        r["adjudicatario_nombre"] = m.group(1).strip()

    #2)Entidad adjudicadora: iria desde “Entidad Adjudicadora:” hasta fin de línea o “Objeto del Contrato”
    m = re.search(
        r"Entidad Adjudicadora\s*[:\n]\s*([^\n]+?)(?=\n|Objeto del Contrato|$)",
        text,
        re.IGNORECASE
    )
    if m:
        r["entidad_adjudicadora"] = m.group(1).strip()

    #3)Objeto del contrato: iria desde “Objeto del Contrato:” hasta fin de línea o puede darse el caso de que lo siguiente sea: “Descripción” o “Valor estimado”.
    m = re.search(
        r"Objeto del Contrato\s*[:\n]\s*([^\n]+?)(?=\n|Descripción|Valor estimado|$)",
        text,
        re.IGNORECASE
    )
    if m:
        r["objeto_contrato"] = m.group(1).strip()

    return r

def build_simple_notice(raw: dict) -> SimpleNotice:
    """
Convertimos aqui datos crudos en instancia de SimpleNotice limpiando espacios, etc.

Args:
    raw: Diccionario con posibles claves parciales extraídas.

Returns:
    SimpleNotice con cadenas normalizadas o None si faltan.
    """
    clean = lambda s: ' '.join(s.split()) if s else None
    return SimpleNotice(
        adjudicatario_nombre = clean(raw.get("adjudicatario_nombre")),
        entidad_adjudicadora= clean(raw.get("entidad_adjudicadora")),
        objeto_contrato     = clean(raw.get("objeto_contrato")),
    )

def process_award_notice(pdf_path: str) -> Tuple[List[str], SimpleNotice]:
    """
Flujo completo para extraer términos de búsqueda y metadatos de un PDF usando las funciones anteriores que acabamos de explicar.
Los pasos que sigue son:
1. extrae texto del PDF.
2. Extrae datos crudos (en este caso: adjudicatario, entidad, objeto).
3. construye SimpleNotice.
4. Normalizamos sufijos y obtenemos la lista de términos únicos.

Args:
    pdf_path: ruta al PDF de la adjudicacion.

Returns:
    Una tupla con:
        - Lista de términos normalizados (sin sufijos ni duplicados).
        - Instancia de SimpleNotice con metadatos.
    """
    text = extract_text_from_pdf(pdf_path)
    raw  = extract_raw_data(text)
    notice = build_simple_notice(raw)
    terms = []
    if notice.adjudicatario_nombre:
        terms.append(normalize_search_term(notice.adjudicatario_nombre))
    if notice.entidad_adjudicadora:
        terms.append(normalize_search_term(notice.entidad_adjudicadora))
    if notice.objeto_contrato:
        terms.append(normalize_search_term(notice.objeto_contrato))
    terms = [t for i,t in enumerate(terms) if t and t not in terms[:i]]
    return terms, notice
