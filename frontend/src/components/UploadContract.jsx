/**
 * @fileoverview
 * Formulario para subir un archivo PDF de contrato al backend.  
 * Gestiona todos los pasos desde la seleccion de fichero, validación básica y el envio por FormData
 * hasta la notificación al padre mediante onUpload cuando la subida es exitosa.
 */

import React, { useState } from 'react'
const API = import.meta.env.VITE_API_URL
import { Button } from '../components/ui/button'

/**
 * Componente de formulario de subida de contrato.
 * @param {object} props Props del componente.
 * @param {function(object): void} props.onUpload Callback que recibe la respuesta del servidor tras subir el PDF, tendra los datos del contrato parseado
 * @returns {JSX.Element} Formulario estilizado que permite seleccionar y subir un PDF.
 */

export default function UploadContract({ onUpload }) {
  //Como hemos ido haciendo en todos los componentes, usamos useState para manejar el estado del archivo seleccionado, errores y el estado de carga.
  const [file, setFile] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  /**
   * Esta función maneja el envío del formulario.
   * Los pasos que realiza son:
   * - Validar que se haya seleccionado un fichero.
   * - Envolvor el PDF en FormData y enviarlo al endpoint `/upload_contract`.
   * - En caso de que la subida fallara, muestra un error. Si tiene éxito, invoca onUpload().
   * @param {React.FormEvent<HTMLFormElement>} e Evento de submit del formulario.
   */
  const handleSubmit = async e => {
    //funcioanlidad explicada anterioemente en boeform
    e.preventDefault()
    if (!file) {
      setError('Debes seleccionar un PDF')
      return
    }
    //Ponemos el estado de loading a true para indicar que estamos haciendo una petición al backend
    //y limpiamos errores anteriores si los hubiera
    setLoading(true)
    setError('')
    //Creamos un FormData para enviar el archivo PDF al backend
    //Esto es necesario porque el backend espera un FormData con el archivo bajo la clave 'file'
    const data = new FormData()
    data.append('file', file)
    try {
      //Realizamos la petición POST al backend para subir el contrato
      const res = await fetch(`${API}/upload_contract`, {
        method: 'POST',
        body: data,
      })
      if (!res.ok) throw new Error(`Error ${res.status}`)
      const body = await res.json()
      //Si la petición es exitosa, llamamos a onUpload con los datos del contrato parseado
      onUpload(body)
    } catch (err) {
      setError('Error subiendo contrato: ' + err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-4 w-full max-w-md mx-auto"
    >
      <div className="w-full">
        <label className="block font-medium mb-1 text-center">PDF del contrato</label>
        <input
          type="file"
          accept="application/pdf"
          onChange={e => setFile(e.target.files[0])}
          className="w-full border rounded px-3 py-2"
        />
      </div>

      {error && <p className="text-red-600 text-center">{error}</p>}
      <div className="text-center mt-4 w-100">
        <Button
          type="submit"
          variant="primary"
          block
          disabled={!file}
        >
          {loading ? 'Subiendo…' : 'Subir contrato'}
        </Button>
      </div>
    </form>
  )
}
