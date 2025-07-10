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

# instala dependencias
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
Muy importante asegurarse de instalar la ultima version de nodejs, a continuación se listan los pasos en un entorno Linux para la versión usada en el desarrollo de este proyecto:
## Descarga e instala nvm:
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.2/install.sh | bash

## en lugar de reiniciar la shell
\. "$HOME/.nvm/nvm.sh"

## Descarga e instala Node.js:
nvm install 22

## Verifica la versión de Node.js:
node -v # Debería mostrar "v22.17.0".
nvm current # Debería mostrar "v22.17.0".

## Verifica versión de npm:
npm -v # Debería mostrar "10.9.2".


# Para ejecutar backend desde la raiz del proyecto puedes hacer:
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 --log-level debug
