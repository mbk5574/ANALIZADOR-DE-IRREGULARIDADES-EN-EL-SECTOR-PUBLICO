import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import 'bootstrap/dist/css/bootstrap.min.css'
import './index.css'
import App from './App.jsx'

/**
 * Punto de entrada de nuestra aplicacion React.
 * - Importa estilos globales (Bootstrap y Tailwind via index.css, finalmente tailwind he prescindido y optado por Bootstrap para el diseño).
 * - Renderizamos <App /> dentro de <StrictMode> (esto lo he realizado asi para detectar problemas en el desarrollo).
 * - Se vincula al elemento HTML con id="root".
 */
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
