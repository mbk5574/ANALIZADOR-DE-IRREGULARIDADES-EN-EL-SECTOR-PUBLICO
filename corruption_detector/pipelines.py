"""
Pipelines de Scrapy para el proyecto Corruption Detector.
- CorruptionDetectorPipeline: gestionamos la serializacion de items a JSON y CSV, junto con la normalizacion y enriquecimiento de los datos.
- TextCleanerPipeline: limpiamos el texto del título y su contenido antes de procesarlos.
"""

import datetime
import json
import logging
import shutil
from itemadapter import ItemAdapter
import spacy
import csv
from pathlib import Path
import unicodedata
from corruption_detector.spiders.corruption_spider import BASE_CORRUPTION_INDICATORS

#cargamos un modelo spaCy (espaniol) para reconocimiento de entidades
nlp = spacy.load("es_core_news_sm")


def strip_accents(text: str) -> str:
    """
Eliminamos acentos de una cadena usando unicodedata.normalize de la libreria unicodedata.
Esto que hacemos aqui es muy util para normalizar el texto antes de realizar las comparaciones o conteos.

Args:
    text (str): Texto de entrada.
Returns:
    str: Texto sin acentos.
    """
    return ''.join(
        c for c in unicodedata.normalize("NFD", text)
        if not unicodedata.combining(c)
    )

class CorruptionDetectorPipeline:
    """
Pipeline principal para realizar lo siguiente:
    1) Normalizamos fechas y metadatos.
    2) Extraemos entidades con spaCy.
    3) Contamos indicadores de corrupcion y longitud de contenido.
    4) Serializamos cada item a JSON y escribimos en un array en disco.
    5) Al cerrar el spider, generamos tambien un CSV 'latest.csv'.
    """
    def open_spider(self, spider):
        """
    Se ejecuta al inicio del spider. Inicializa ruta de resultados y un flag first_item.
        """
        self.path = getattr(spider, "result_path", None)
        self.first_item = True

    def close_spider(self, spider):
        """
    Esta funcion Scrapy la llama automaticamente una sola vez, eso pasa justo cuando el spider ha terminado todo su trabajo 
    es decir, (ha visitado todas las páginas y ha procesado todos los items), siempre:
        - Cerramos el array JSON añadiendo ']' al final
        - Generamos un CSV con nombre timestamped y lo copiamos a 'latest.csv'.
        """
        if not self.path:
            spider.logger.warning("CorruptionDetectorPipeline: no result_path, saltando cierre de fichero")
            return

        #1)cerramos el JSON array
        try:
            with open(self.path, 'a', encoding='utf-8') as f:
                f.write('\n]')
        except FileNotFoundError:
            return

        #2)generamos el CSV "latest.csv" 
        results_dir = Path(self.path).parent
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        latest_csv = results_dir / f"latest_{timestamp}.csv"
        fixed_link = results_dir / "latest.csv"
        #Lo que vamos a hacer es abrir el json en modo lectura y el csv en modo escritura, y vamos a volcar los datos del json al csv.
        try:
            with open(self.path, encoding='utf-8') as jf, \
                 open(latest_csv, 'w', newline='', encoding='utf-8') as cf:

                data = json.load(jf)
                writer = csv.writer(cf)
                headers = ["title","link","source","publication_date","date_scraped","sentiment_polarity","indicator_count","content_length","entities"]
                writer.writerow(headers)

                for it in data:
                    ents = ";".join(f"{e['text']}[{e['label']}]" for e in it.get("entities", []))
                    row = [
                        it.get("title","").replace(",", " "),
                        it.get("link",""),
                        it.get("source",""),
                        it.get("publication_date",""),
                        it.get("date_scraped",""),
                        str(it.get("sentiment_polarity","")),
                        str(it.get("indicator_count",0)),
                        str(it.get("content_length",0)),
                        ents
                    ]
                    writer.writerow(row)
        except Exception as e:
            spider.logger.error(f"Error generando latest.csv: {e}")
        #Tras haber creado el csv con su marca de tiempo lo copiamos a latest.csv y asi tenemos un archivo con un nombre fijo por si se quiere hacer un analisis posterior sin dejar de apuntar a un mismo archivo.
        try:
            import shutil
            shutil.copy(latest_csv, fixed_link)
        except Exception as e:
            spider.logger.error(f"No he podido actualizar latest.csv: {e}")

    def process_item(self, item, spider):
        """
    cada vez que se genera un item durante el scraping se debe procesar con esta funcion, normalizamos y enriquecemos cada item de las siguientes maneras:
        - Publicacion: convertimos fechas a ISO.
        - Aniadimos date_scraped.
        - Extraemos entidades con spaCy (PER, LOC, ORG).
        - Contamos indicadores de corrupcion y longitud de contenido.
        - Serializamos a JSON y escribimos en disco.
        """
        adapter = ItemAdapter(item)

        #Convertimos la fecha de publicacion a formato ISO para analisis posteiores.
        raw_pub = adapter.get("publication_date", "").strip()
        if raw_pub:
            parts = raw_pub.split()
            cleaned = " ".join(parts[:2]) if len(parts) >= 2 else raw_pub
            try:
                dt = datetime.datetime.fromisoformat(cleaned)
                adapter["publication_date"] = dt.isoformat()
            except Exception:
                adapter["publication_date"] = cleaned

        adapter["date_scraped"] = datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat()

        text = adapter.get("title", "") + " " + adapter.get("content_preview", "")
        #Utilizamos la libreria de procesamiento de lenguaje natural spaCy para extraer entidades como personas, organizaciones y localizaciones.
        doc = nlp(text)
        ALLOWED_LABELS = {"PER", "LOC", "ORG"}
        seen = set()
        cleaned_ents = []
        #Iteramos sobre las entidades encontradas y filtramos por longitud y etiquetas permitidas ignorando algun resultado sin sentido como por ejemplo una entidad de mas de 4 palabras.
        for ent in doc.ents:
            txt = ent.text.strip()
            lbl = ent.label_
            if lbl not in ALLOWED_LABELS:
                continue
            words = txt.split()
            if len(words) > 4 or len(txt) < 2:
                continue
            key = (txt, lbl)
            if key in seen:
                continue
            #añadimos la entidad al set de entidades vistas para evitar duplicados.
            seen.add(key)
            cleaned_ents.append({"text": txt, "label": lbl})

        adapter["entities"] = cleaned_ents

        #Calculamos metricas adicionales que serviran en etapas posteiores para realizar el analisis
        raw_for_count = (adapter.get("title","") + " " + adapter.get("content_preview","")).lower()
        norm_for_count = strip_accents(raw_for_count)
        adapter["indicator_count"] = sum(
            norm_for_count.count(strip_accents(term))
            for term in BASE_CORRUPTION_INDICATORS
        )
        adapter["content_length"] = len(adapter.get("content_preview", "").split())

        try:
            line = json.dumps(dict(adapter), ensure_ascii=False)
        except Exception as e:
            spider.logger.error(f"Error serializando item {adapter.get('link')}: {e}")
            return item

        if not self.path:
            return item

        if self.first_item:
            with open(self.path, "w", encoding="utf-8") as f:
                f.write("[\n" + line)
            self.first_item = False
        else:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(",\n" + line)

        return item


class TextCleanerPipeline:
    """
pequenio ipeline ligero para terminar de:
    - Eliminar espacios sobrantes y saltos en títulos y previews.
    """
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        if adapter.get("content_preview"):
            adapter["content_preview"] = adapter["content_preview"].strip()
        if adapter.get("title"):
            adapter["title"] = adapter["title"].replace("\n", " ").strip()
        logging.debug(f"Ítem limpiado: {adapter.get('title', 'Sin título')}")
        return item
