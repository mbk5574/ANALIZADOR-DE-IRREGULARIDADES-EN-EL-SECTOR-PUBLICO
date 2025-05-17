# contract_processor.py (Version Final1)

import fitz  #PyMuPDF es el que voy a usar finalmente, apuntar en word
import spacy
import os
import re #importamos el modulo de expresiones regulares

#cargamos el modelo de spaCy para español
try:
    nlp = spacy.load("es_core_news_lg")
    print("Modelo spaCy 'es_core_news_lg' cargado.")
except OSError:
    print("Error: Modelo 'es_core_news_lg' no encontrado.")
    print("Por favor, descárgalo ejecutando: python -m spacy download es_core_news_lg")
    nlp = None

def extract_text_from_pdf(pdf_path):
    """Extrae texto plano de un archivo PDF, linea por linea."""
    if not os.path.exists(pdf_path):
        print(f"Error: Archivo PDF no encontrado en {pdf_path}")
        return ""
    full_text = ""
    try:
        doc = fitz.open(pdf_path)
        print(f"Procesando PDF: {pdf_path}, Páginas: {len(doc)}")
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            full_text += page.get_text("text", sort=True) + "\n"
        doc.close()
    except Exception as e:
        print(f"Error procesando PDF {pdf_path}: {e}")
    return full_text

def extract_structured_info(text):
    """
    Extrae información clave usando una combinación de regex y procesamiento
    línea por línea, con lógica de parada refinada para el objeto.
    """
    info = {}
    lines = text.splitlines()

    # --- Extraccion de campos simples con Regex ---
    #adjudicatario
    match = re.search(r"Adjudicatario\s*[\r\n]+([^\r\n]+)", text, re.IGNORECASE)
    if match: info['adjudicatario_nombre'] = match.group(1).strip().replace('→', '').strip()

    #NIF
    nif_match = re.search(r"NIF\s+([A-Z0-9]+)", text, re.IGNORECASE)
    if nif_match: info['adjudicatario_nif'] = nif_match.group(1).strip()
    elif info.get('adjudicatario_nombre'):
        adj_index = text.find(info['adjudicatario_nombre'])
        if adj_index != -1:
            sub_text = text[adj_index:]
            match_nif_line = re.search(r"[\r\n]+\s*NIF\s+([A-Z0-9]+)", sub_text, re.IGNORECASE)
            if match_nif_line: info['adjudicatario_nif'] = match_nif_line.group(1).strip()

    #importe adjduicacion s IVA
    match = re.search(r"Importe total ofertado \(sin impuestos\)\s*([\d.,]+)\s*EUR", text, re.IGNORECASE)
    if match: info['importe_adjudicacion_sin_iva'] = match.group(1).strip()

    #entidad edjudicadora
    match = re.search(r"Entidad Adjudicadora\s*[\r\n]+((?:[^\r\n]+(?:[\r\n]+(?!\s*(?:Tipo de Administración|Actividad Principal|Perfil del Contratante|Dirección Postal)))?)+)", text, re.IGNORECASE | re.MULTILINE)
    if match: info['entidad_adjudicadora'] = ' '.join(match.group(1).replace('→','').strip().split())

    #numero expediente
    match = re.search(r"Número de Expediente\s+([^\s\r\n]+)", text, re.IGNORECASE)
    if match: info['numero_expediente'] = match.group(1).strip()

    #objeto del Contrato (lo hacemos linea por linea con re.match para parada)
    objeto_lines = []
    capturing_objeto = False
    start_keyword = "Objeto del Contrato"
    stop_keywords = [
        "-- Descripción", "Valor estimado", "Clasificación CPV", "Lugar de ejecución",
        "Tipo de procedimiento", "Programas de Financiación", "Procedimiento",
        "Presupuesto base", "Adjudicado",
    ]

    for i, line in enumerate(lines):
        line_stripped = line.strip()

        if capturing_objeto:
            is_stop_line = False
            #usamois re.match para comprobar el inicio de la linea (mejor porque m,e permite junk inicial)
            for keyword in stop_keywords:
                #el patron: inicio línea(^), opcional(espacio/flecha/...), keyword escape
                pattern_to_check = r"^\s*(?:→\s*)*" + re.escape(keyword)
                if re.match(pattern_to_check, line_stripped, re.IGNORECASE):
                     is_stop_line = True
                     #print(f"DEBUG: Stop line detected: '{line_stripped}' by keyword '{keyword}'")
                     break

            if is_stop_line:
                capturing_objeto = False
                break #salimos del bucle for
            else:
                cleaned_line = line_stripped.replace('→', '').strip()
                if cleaned_line: objeto_lines.append(cleaned_line)

        elif start_keyword in line:
             capturing_objeto = True
             potential_object_on_same_line = line_stripped.split(start_keyword, 1)[-1].lstrip(':').strip()
             if potential_object_on_same_line:
                  cleaned_part_same_line = potential_object_on_same_line.replace('→', '').strip()
                  contains_stop_same_line = False
                  for keyword in stop_keywords:
                      pattern_to_check_same = r"^\s*(?:→\s*)*" + re.escape(keyword)
                      if re.match(pattern_to_check_same, cleaned_part_same_line, re.IGNORECASE):
                           contains_stop_same_line = True
                           #tomamos eñ texto antes de la keyword encontrada
                           match_stop_same = re.match(pattern_to_check_same, cleaned_part_same_line, re.IGNORECASE)
                           if match_stop_same: #debería encontrarlo en caso de que si entro al if
                               stop_pos = match_stop_same.start() #posición donde empieza la keyword de parada
                               cleaned_part_same_line = cleaned_part_same_line[:stop_pos].strip()
                           break
                  if cleaned_part_same_line: objeto_lines.append(cleaned_part_same_line)
                  if contains_stop_same_line:
                      capturing_objeto = False
                      break

    if objeto_lines:
        info['objeto_contrato'] = re.sub(r'\s+', ' ', ' '.join(objeto_lines)).strip()
    # -------------------------------------------------------------------------

    print(f"Información estructurada extraída (Final): {info}")
    return info

def extract_entities_nlp(text):
    """(Sin cambios) Extrae entidades NLP filtradas (solo informativo)."""
    if not nlp or not text: return []
    doc = nlp(text)
    entities = set()
    relevant_labels = {"ORG", "PER"}
    ignore_list = { "contacto", "importe", "dirección", "nif", "número", "expediente", "procedimiento", "criterio", "fecha", "plazo", "tipo", "subtipo", "contrato", "contratación", "sector", "público", "adjudicadora", "adjudicatario", "autoridad", "directiva", "acuerdo", "perfil", "plataforma", "teléfono", "correo", "electrónico", "fax", "web", "mes", "euros", "gobierno", "general", "servicio", "servicios", "administración", "españa", "madrid", "condiciones", "licitación", "valor", "documento", "siguiente", "objeto", "base", "licitación", "ejecución", "lugar", "clasificación", "cpv", "presentación", "recursos", "tribunal", "justicia", "sistema", "dinámico", "adquisición", "oferta", "motivo", "motivación", "subcontratación", "origen", "producto", "país", "anuncio", "publicado", "horas", "sobre", "mediante", "aplicación", "otros", "detalle", "sellado", "tiempo", "serie", "cet", "id", "uuid", "url", "https", "http", "www", "com", "es", "eu", "pcp", "wps", "poc", "uri", "deeplink", "true", "false", "si", "no", "caso", "gob", "según", "previsto", "lcsp", "atendiendo", "dispuesto", "pcap", "am", "financiación", "fondos", "ue", "pyme", "s", "a", "u", "l", "inc", "org", "dg", "m", "tsj", "tacrc" }
    for ent in doc.ents:
        if ent.label_ in relevant_labels:
            entity_text = ent.text.replace('\n', ' ').replace('→', '').strip()
            entity_lower = entity_text.lower()
            if len(entity_text) <= 3: continue
            if entity_lower in ignore_list: continue
            if not re.search(r'\w', entity_text): continue
            if entity_text.endswith(':'): continue
            entities.add(entity_text)
    print(f"Entidades NLP filtradas (ORG, PER) (Ejecutado para info, no para búsqueda): {list(entities)}")
    return list(entities)

def process_award_notice(pdf_path):
    """(Sin cambios) Función principal simplificada."""
    print(f"Iniciando procesamiento de Anuncio de Adjudicación: {pdf_path}")
    full_text = extract_text_from_pdf(pdf_path)
    if not full_text:
        print("No se pudo extraer texto del PDF.")
        return [], {}

    structured_data = extract_structured_info(full_text)
    _ = extract_entities_nlp(full_text) #ejecutampos NLP solo para info

    search_terms = set()
    adjudicatario_nombre = structured_data.get('adjudicatario_nombre')
    if adjudicatario_nombre:
        search_terms.add(adjudicatario_nombre)
        print(f"Término de búsqueda principal añadido: '{adjudicatario_nombre}'")

    objeto_contrato = structured_data.get('objeto_contrato')
    if objeto_contrato:
        print(f"Objeto del contrato extraído: '{objeto_contrato}'")
        #(Sección para aniadir objeto a search_terms sigue comentada por defecto hasta que aclare esto respecto a los contratos publicos)
        # if len(objeto_contrato) < 150:
        #     search_terms.add(objeto_contrato)
        #     print(f"Aniadido objeto del contrato como termino de busqueda.")
        pass

    final_search_terms = list(search_terms)
    print(f"\n--- Términos Finales Seleccionados para Búsqueda de Noticias (Final) ---")
    if not final_search_terms: print("¡Advertencia! No se pudo extraer ningún término de búsqueda fiable (Adjudicatario).")
    else:
        for i, term in enumerate(final_search_terms): print(f"{i+1}. {term}")

    return final_search_terms, structured_data


if __name__ == "__main__":
    test_pdf_path = "DOC_CAN_ADJ2024-000245509.pdf"
    if os.path.exists(test_pdf_path):
        extracted_terms, structured_info = process_award_notice(test_pdf_path)
        print("\n--- Datos Estructurados Completos Extraídos ---")
        for key, value in structured_info.items():
             print(f"- {key}: {value}")
    else:
        print(f"Archivo de prueba no encontrado: {test_pdf_path}")