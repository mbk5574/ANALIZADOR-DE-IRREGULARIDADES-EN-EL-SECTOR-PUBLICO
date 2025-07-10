# TFG – Analizador de Irregularidades

Este proyecto consta de dos partes:

1. **Backend**: API en Python (FastAPI) que:
   - Permite subir PDFs de contratos y extraer metadatos.
   - Consulta el BOE para recuperar datos del contrato.
   - Crea y monitoriza jobs de scraping de noticias.
   - Devuelve resultados en JSON o CSV.
2. **Frontend**: SPA en React + Bootstrap que consume la API para:
   - Subir contratos, buscar en BOE y definir términos.
   - Lanzar el scraping, mostrar estado y visualizar/análisis de resultados.

---

## Requisitos

- **Python 3.10+**  
- **Node.js 18+** (o superior) y **npm**  
- **Playwright** (para la parte de scraping con `scrapy-playwright`)

---

## Instalación

Clona el repo y sitúate en la raíz.

# crea y activa un entorno virtual
python -m venv venv
# Unix/macOS
source venv/bin/activate
# Windows
venv\Scripts\activate

# instala dependencias(mejor coger el .txt en la carpeta backend)
pip install -r requirements.txt

# instala el modelo de spaCy (español)
python -m spacy download es_core_news_sm

# instala navegadores de Playwright (si no lo tienes)
playwright install

cd frontend
npm install
# (opcional) define en .env:
# VITE_API_URL=http://localhost:8000

# Para ejecutar frontend importante que estes situado en la carpeta frontend y ahi haces:
npm run dev
Muy importante asegurarse de instalar la ultima version de nodejs. Usar Windows para ejecutar el proyecto.

## importante instalar las siguientes modulos en node que no existen en el actual json
npm install bootstrap@5 
npm install framer-motion
npm install recharts
npm install chart.js
npm install react-chartjs-2


# Para ejecutar backend desde la raiz del proyecto puedes hacer:
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
