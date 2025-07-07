/**
 * @fileoverview
 * Este componente renderiza la información principal de un contrato
 * extraído del BOE. Muestra el identificador, título, organismo y,
 * si está disponible, un enlace para descargar su PDF que ayude a continuacion al usuario a extraer terminos clave.
 * En conjunto, facilita al usuario entender rápidamente los datos
 * del contrato sin necesidad de salir del flujo de la aplicación.
 */

import React from 'react'

/**
 * Muestra los detalles de un contrato obtenido del BOE.
 *
 * @param {object} props                     Props del componente.
 * @param {object} props.data                Objeto con la información del contrato.
 * @param {string} props.data.identificador  Identificador oficial del contrato (p.ej. "BOE-B-2025-22668").
 * @param {string} [props.data.titulo]       Título descriptivo del contrato.
 * @param {string} [props.data.organismo]    Nombre del organismo que publica el contrato.
 * @param {string} [props.data.url_pdf]      URL absoluta para descargar el PDF del contrato.
 *
 * @returns {JSX.Element} Un bloque `<div>` centrado con la información del contrato
 *                        y un enlace al PDF si está disponible.
 */

//data es un objeto que viene del componente padre (app.jsx) y contiene los datos del contrato
export default function ContractDetails({ data }) {
  //Aqui simplemente destructuramos el objeto data para obtener las propiedades que nos interesan
  const { identificador, titulo, url_pdf, organismo } = data

  return (
    <div className="contract-details p-4 bg-gray-50 rounded max-w-md mx-auto text-center">
      <h2 className="text-xl font-semibold mb-2">Contrato BOE</h2>

      <p>
        <strong>Identificador:</strong>{' '}
        <span className="font-mono">{identificador}</span>
      </p>
      <p>
        <strong>Título:</strong>{' '}
        <span>{titulo || '—'}</span>
      </p>
      <p>
        <strong>Organismo:</strong>{' '}
        <span>{organismo || '—'}</span>
      </p>
      {url_pdf && (
        <p>
          <strong>Descarga PDF:</strong>{' '}
          <a
            href={url_pdf}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 underline"
          >
            Ver documento
          </a>
        </p>
      )}
    </div>
  )
}
