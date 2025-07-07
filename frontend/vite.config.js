/**
 * vite.config.js
 *
 * Configuración de Vite para el proyecto React:
 *  - Incluye el plugin oficial de React para soportar JSX y Fast Refresh.
 *  - Durante el desarrollo, se han introducido en el proxy para redirigir, rutas de API al backend en http://localhost:8000:
 *      • /contracts
 *      • /jobs
 *      • /scrape
 *      • /indicators
 */

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/contracts': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/jobs': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/scrape': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
      '/indicators': {
        target: 'http://localhost:8000',
        changeOrigin: true
      },
    }
  }
})