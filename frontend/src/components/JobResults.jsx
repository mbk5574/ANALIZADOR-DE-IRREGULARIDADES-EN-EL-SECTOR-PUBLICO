/**
 * @fileoverview
 * Muestra los resultados de un job de análisis: permite descargar un CSV en caso de que el usuario quiera realizar un análisis posterior
 * de los datos obtenidos, y además renderiza un gráfico de barras con el recuento de términos contractuales
 * encontrados y lista en una tabla todos los ítems procesados junto con sus metadatos.
 */

import React from 'react'
import 'bootstrap/dist/css/bootstrap.min.css'

/** importamos los elementos necesarios de chart.js para poder luego crear el grafico de barras con todos sus elementos **/
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
//importamos el componente Bar de react-chartjs-2 que nos permite renderizar graficos de barras
import { Bar } from 'react-chartjs-2'

//Paso obligatorio para registrar los componentes de Chart.js que vamos a utilizar
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

/**
 * Componente que muestra los resultados de un job de scraping/análisis.
 *
 * @param {object} props
 * @param {string} props.jobId  Identificador unico del job, usado para generar la URL de descarga CSV.
 * @param {Array|null} props.items  Array de resultados; puede ser:
 *    - `null` mientras se cargan,
 *    - `[]` si no hay resultados,
 *    - un Array de objetos `CorruptionItem` con campos como `title`, `source`, `publication_date`, `date_scraped`,
 *      `sentiment_polarity`, `contract_terms_found` y `entities`.
 *
 * @returns {JSX.Element} 
 * Renderiza:
 * 1. Mensaje de carga o “no hay resultados” si `items` es `null` o `[]` lo cual puede pasar cuando ninguno de los terminos indicativos de irregularidades se encuentran en los articulos scrapeados.
 * 2. Enlace para descargar un CSV con todos los resultados.
 * 3. Un gráfico de barras que muestra cuántas veces aparece cada término contractual.
 * 4. Una tabla con todos los ítems, enlazando al artículo original y mostrando sus metadatos.
 */

export default function JobResults({ jobId, items }) {
  //El componente recibe del padre un nulo o un array de items que son los resultados del job
  //Si items es nulo, mostramos un mensaje de carga porque significa que el trabajo aun no ha terminado
  if (items === null) {
    return <p className="mt-4">Cargando resultados…</p>
  }
  if (items.length === 0) {
    return <p className="mt-4">El análisis terminó pero no se encontraron resultados.</p>
  }
  //Si llegamos hasta aqui, significa que tenemos resultados y podemos proceder a construir la url que apuntara a nuestro endpoint del backend para poder descargar el archivo CSV
  const csvUrl = `${import.meta.env.VITE_API_URL}/jobs/${jobId}/results.csv`

  //Contamos cuantos items tienen cada termino contractual encontrado usando la funcion reduce que nos permite iterar sobre el array de items y crear un objeto donde las claves son los terminos encontrados y los valores son el numero de veces que aparecen
  const termCounts = items.reduce((acc, it) => {
    it.contract_terms_found.forEach(term => {
      acc[term] = (acc[term] || 0) + 1
    })
    return acc
  }, {})

  //Creamos los datos que usaremos para el grafico de barras, las etiquetas del eje x seran las claves de nuestro objeto termCounts
  const chartData = {
    labels: Object.keys(termCounts),
    datasets: [
      {
        label: 'Apariciones por término',
        data: Object.values(termCounts),
        backgroundColor: 'rgba(54, 162, 235, 0.6)',
      },
    ],
  }

  return (
    <div className="container my-5">
      <div className="text-center mb-4">
        <a href={csvUrl} className="btn btn-link">
          📥 Descargar CSV
        </a>
      </div>

      <div className="mb-5">
        <Bar data={chartData} />
      </div>

      <table className="table table-striped table-bordered">
        <thead className="thead-light">
          <tr>
            <th>Título</th>
            <th>Fuente</th>
            <th>Fecha Pub</th>
            <th>Fecha Scrapeo</th>
            <th>Polarity</th>
            <th>Entidades</th>
          </tr>
        </thead>
        <tbody>
          {items.map((it, i) => (
            <tr key={i}>
              <td>{it.title}</td>
              <td>
                <a href={it.link} target="_blank" rel="noreferrer">
                  {it.source}
                </a>
              </td>
              <td>{it.publication_date}</td>
              <td>{it.date_scraped}</td>
              <td>{it.sentiment_polarity}</td>
              <td>{it.entities?.map(e => `${e.text} (${e.label})`).join(', ')}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
