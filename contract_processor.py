import fitz  # PyMuPDF
import os
import re
import logging
from dataclasses import dataclass, fields
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import Optional, List, Tuple

# --- 1. Configuración del Logging ---
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- Sufijos para normalizar nombres ---
SUFFIXES_TO_STRIP = [
    "S.L.U.", "S.L.N.E.", "S.L.P.", "S.L.L.", "S.A.U.", "S.A.D.",
    "S.L.U", "S.L.N.E", "S.L.P", "S.L.L", "S.A.U", "S.A.D",
    "S.L.", "S.A.", "S.C.A.", "S.C.P.", "S.COOP.", "S.C.",
    "S.L", "S.A", "S.C.A", "S.C.P", "S.COOP", "S.C",
    "U.T.E.", "UTE", "INC.", "LTD.", "LLC.", "GMBH.",
    "INC", "LTD", "LLC", "GMBH",
    "(UTE)"
]

# --- 2. PATRONES REGEX ---
PATRON_FECHA_PUB = re.compile(
    r"Publicado en la Plataforma de Contratación del Sector Público el\s*(\d{2}[-/]\d{2}[-/]\d{4})",
    re.IGNORECASE
)
PATRON_VALOR = re.compile(
    r"Valor estimado del contrato\s*([\d.,]+)\s*EUR",
    re.IGNORECASE
)
PATRON_EXPEDIENTE = re.compile(
    r"Número de Expediente\s*([^\s]+)",
    re.IGNORECASE
)
PATRON_FECHA_ACUERDO = re.compile(
    r"Fecha del Acuerdo\s*(\d{2}/\d{2}/\d{4})",
    re.IGNORECASE
)
PATRON_NIF = re.compile(
    rf"(?:NIF|CIF)\s*:?[ ]*([A-Z]\d{{7}}[A-Z0-9]|[A-Z]\d{{8}}|[KLMXYZ]\d{{7}}[A-Z]|\d{{8}}[A-Z])",
    re.IGNORECASE
)
URL_PATTERN = re.compile(
    r"(https?://(?:[a-zA-Z0-9\-._~:/?#\[\]@!$&'()*+,;=]|%[0-9a-fA-F]{{2}}|\s)*?[a-zA-Z0-9/\-_%#&=?]+)",
    re.IGNORECASE
)

# --- 3. DATACLASS PARA ESTRUCTURA ---
@dataclass
class AwardNotice:
    pdf_path: str
    fecha_publicacion: Optional[date] = None
    entidad_adjudicadora: Optional[str] = None
    objeto_contrato: Optional[str] = None
    valor_estimado_contrato: Optional[Decimal] = None
    presupuesto_base_sin_iva: Optional[Decimal] = None
    numero_expediente: Optional[str] = None
    adjudicatario_nombre: Optional[str] = None
    adjudicatario_nif: Optional[str] = None
    importe_adjudicacion_sin_iva: Optional[Decimal] = None
    importe_adjudicacion_con_iva: Optional[Decimal] = None
    fecha_acuerdo_adjudicacion: Optional[date] = None
    url_perfil_contratante: Optional[str] = None
    url_detalle_licitacion: Optional[str] = None

# --- 4. FUNCIONES AUXILIARES ---

def extract_text_from_pdf(pdf_path: str) -> str:
    if not os.path.exists(pdf_path):
        logging.error(f"Archivo PDF no encontrado: {pdf_path}")
        return ""
    try:
        with fitz.open(pdf_path) as doc:
            pages = len(doc)
            logging.info(f"Procesando PDF {pdf_path} ({pages} páginas)")
            parts = []
            for i, page in enumerate(doc, 1):
                parts.append(page.get_text("text"))
            text = "\n".join(parts)
            text = re.sub(r'[–—]', '-', text)
            text = re.sub(r'\s+', ' ', text)
            return text
    except Exception as e:
        logging.error(f"Error al abrir PDF {pdf_path}: {e}")
        return ""


def to_decimal(s: Optional[str]) -> Optional[Decimal]:
    if not s:
        return None
    try:
        return Decimal(s.replace('.', '').replace(',', '.'))
    except InvalidOperation:
        logging.warning(f"No se pudo convertir '{s}' a Decimal")
        return None


def to_date(s: Optional[str], fmt: str) -> Optional[date]:
    if not s:
        return None
    try:
        return datetime.strptime(s, fmt).date()
    except ValueError:
        logging.warning(f"No se pudo parsear fecha '{s}' con formato {fmt}")
        return None


def clean_value(s: Optional[str]) -> Optional[str]:
    return ' '.join(s.replace('→', '').split()) if s else None


def normalize_search_term(term: str) -> str:
    # Remover sufijos
    for suf in SUFFIXES_TO_STRIP:
        term = re.sub(rf"(,\s*)?{re.escape(suf)}\.?$", '', term, flags=re.IGNORECASE)
    term = re.sub(r'[.,\s]+$', '', term)
    term = re.sub(r'^[^\w\s(]+|[^\w\s)]+$', '', term)
    return term.strip()


def extract_section(text: str, start: str, ends: List[str]) -> Optional[str]:
    idx = text.find(start)
    if idx < 0:
        return None
    idx += len(start)
    positions = [text.find(e, idx) for e in ends]
    positions = [p for p in positions if p >= 0]
    end = min(positions) if positions else len(text)
    return text[idx:end].strip()

# --- 5. EXTRACCIÓN CRUDA ---

def extract_raw_data(text: str) -> dict:
    r = {}
    if m := PATRON_FECHA_PUB.search(text):
        r['fecha_publicacion'] = m.group(1)

    # Entidad Adjudicadora
    ent_block = extract_section(
        text,
        'Entidad Adjudicadora',
        ['Tipo de Administración','Actividad Principal','Perfil del Contratante','Contacto']
    )
    if ent_block:
        lines = [ln.strip(' →') for ln in ent_block.split('\n') if ln.strip()]
        r['entidad_adjudicadora'] = ' '.join(lines)

    # Objeto Contrato
    if m := re.search(r"Objeto del Contrato:\s*(.+?)(?=Valor estimado del contrato|$)", text, re.IGNORECASE):
        r['objeto_contrato'] = m.group(1)

    # Valor Estimado
    if m := PATRON_VALOR.search(text):
        r['valor_estimado_contrato'] = m.group(1)

    # Presupuesto base sin IVA
    pres_block = extract_section(
        text,
        'Presupuesto base de licitación',
        ['Clasificación CPV','Lugar de ejecución']
    )
    if pres_block and (m := re.search(r"Importe\s*\(sin impuestos\)\s*([\d.,]+)\s*EUR", pres_block, re.IGNORECASE)):
        r['presupuesto_base_sin_iva'] = m.group(1)

    # Número Expediente
    if m := PATRON_EXPEDIENTE.search(text):
        r['numero_expediente'] = m.group(1)

    # Fecha Acuerdo
    if m := PATRON_FECHA_ACUERDO.search(text):
        r['fecha_acuerdo_adjudicacion'] = m.group(1)

    # URLs
    if m := re.search(r"Perfil del Contratante\s*[\n→\s]*("+URL_PATTERN.pattern+r")", text, re.IGNORECASE):
        r['url_perfil_contratante'] = m.group(1)
    if m := re.search(r"Detalle de la Licitación:\s*[\n→\s]*("+URL_PATTERN.pattern+r")", text, re.IGNORECASE):
        r['url_detalle_licitacion'] = m.group(1)

    # Adjudicatario y NIF
    adj_block = extract_section(
        text,
        'Adjudicatario',
        ['Importes de Adjudicación','Condiciones de Subcontratación','Motivación','Fecha del Acuerdo']
    )
    if adj_block:
        lines = [ln.strip(' →') for ln in adj_block.split('\n') if ln.strip()]
        if lines:
            r['adjudicatario_nombre'] = lines[0]
        if m := PATRON_NIF.search(adj_block):
            r['adjudicatario_nif'] = m.group(1)

    # Importes Adjudicación
    imp_block = extract_section(
        text,
        'Importes de Adjudicación',
        ['Condiciones de Subcontratación','Motivación','Fecha del Acuerdo']
    )
    if imp_block:
        if m := re.search(r"Importe total ofertado \(sin impuestos\)\s*([\d.,]+)\s*EUR", imp_block, re.IGNORECASE):
            r['importe_adjudicacion_sin_iva'] = m.group(1)
        if m := re.search(r"Importe total ofertado \(con impuestos\)\s*([\d.,]+)\s*EUR", imp_block, re.IGNORECASE):
            r['importe_adjudicacion_con_iva'] = m.group(1)

    return r

# --- 6. CONSTRUCCIÓN DEL OBJETO ---

def build_award_notice(raw: dict, path: str) -> AwardNotice:
    return AwardNotice(
        pdf_path=path,
        fecha_publicacion=to_date(raw.get('fecha_publicacion'), "%d-%m-%Y"),
        entidad_adjudicadora=clean_value(raw.get('entidad_adjudicadora')),
        objeto_contrato=clean_value(raw.get('objeto_contrato')),
        valor_estimado_contrato=to_decimal(raw.get('valor_estimado_contrato')),
        presupuesto_base_sin_iva=to_decimal(raw.get('presupuesto_base_sin_iva')),
        numero_expediente=clean_value(raw.get('numero_expediente')),
        adjudicatario_nombre=clean_value(raw.get('adjudicatario_nombre')),
        adjudicatario_nif=clean_value(raw.get('adjudicatario_nif')),
        importe_adjudicacion_sin_iva=to_decimal(raw.get('importe_adjudicacion_sin_iva')),
        importe_adjudicacion_con_iva=to_decimal(raw.get('importe_adjudicacion_con_iva')),
        fecha_acuerdo_adjudicacion=to_date(raw.get('fecha_acuerdo_adjudicacion'), "%d/%m/%Y"),
        url_perfil_contratante=(clean_value(raw.get('url_perfil_contratante')) or '').replace(' ', '%20') or None,
        url_detalle_licitacion=(clean_value(raw.get('url_detalle_licitacion')) or '').replace(' ', '%20') or None,
    )

# --- 7. ORQUESTACIÓN Y TÉRMINOS DE BÚSQUEDA ---

def process_award_notice(pdf_path: str) -> Tuple[List[str], AwardNotice]:
    text = extract_text_from_pdf(pdf_path)
    raw = extract_raw_data(text)
    notice = build_award_notice(raw, pdf_path)

    # Generar términos de búsqueda: nombre simplificado y NIF
    terms = []
    if notice.adjudicatario_nombre:
        # Nombre antes de " NIF"
        simple = notice.adjudicatario_nombre.split(' NIF')[0]
        simple = normalize_search_term(simple)
        terms.append(simple)
    if notice.adjudicatario_nif:
        terms.append(notice.adjudicatario_nif)

    return terms, notice

# --- 8. EJECUCIÓN PRINCIPAL ---

if __name__ == "__main__":
    path = "DOC_CAN_ADJ2024-000245509.pdf"
    if os.path.exists(path):
        terms, notice = process_award_notice(path)
        print("\n--- Datos extraídos ---")
        for f in fields(notice):
            print(f"- {f.name.replace('_',' ').capitalize()}: {getattr(notice,f.name)}")
        print(f"\nTérminos búsqueda: {terms}")
    else:
        print(f"No existe el archivo {path}")
