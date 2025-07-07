/**
 * @fileoverview
 * Formulario para buscar datos de un contrato en el BOE.
 * Recupera la fecha de publicación y el número de expediente,
 * realiza una llamada a la API y envía los datos encontrados al
 * componente padre (app.jsx) mediante la función onFound donde se procesaran los datos recibidos.
 */

import React, { useState } from 'react'
const API = import.meta.env.VITE_API_URL
import { Button } from './ui/button'

/**
 *
 * @param {object} props
 * @param {(data: any, fecha: string, expediente: string) => void} props.onFound
 *   Callback que se invoca cuando la búsqueda en el BOE es exitosa.
 *   Recibe los datos del contrato, la fecha y el expediente.
 * @returns {JSX.Element}
 */

//recibimos una funcion o callback onFound del componente padre 
export default function BoeForm({ onFound }) {
  //definimos los estados necesarios para manejar el formulario, lo hacemos con useState que nos permite crear variables de estado en componentes funcionales
  //fecha y expediente son los campos que el usuario debe completar
  const [fecha, setFecha] = useState('')
  const [expediente, setExpediente] = useState('')
  //error y loading son estados para manejar errores y el estado de carga(basicamente controlar si se esta haciendo una peticion o no)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)


  const handleSubmit = async e => {
    //Como nuestro proyecto usa React basandose en el modelo SPA (Single Page Application) evitamos recargar la pagina porque eso haría que se perdieran los estados del formulario
    e.preventDefault()
    //Validamos que la fecha tenga el formato correcto (AAAAMMDD) y que el expediente no esté vacío
    if (!/^\d{8}$/.test(fecha) || !expediente.trim()) {
      setError('Debes indicar fecha (AAAAMMDD) y expediente')
      return
    }

    setLoading(true); setError('')
    //Realizamos la petición a la API del backend para buscar el contrato
    try {
      //Usamos fetch para hacer la petición GET a la API, pasamos la fecha y el expediente como parámetros en la URL
      const res = await fetch(
        `${API}/contracts/${fecha}/${encodeURIComponent(expediente.trim())}`
      )
      if (!res.ok) throw new Error(`Contrato no encontrado (${res.status})`)
      //Si la petición es exitosa, parseamos la respuesta a JSON y llamamos a onFound con los datos obtenidos para que el componente padre(app.jsx) pueda procesarlos
      const data = await res.json()
      onFound(data, fecha, expediente.trim())
    } catch (err) {
      setError(err.message)
    } finally {
      //Finalmente, independientemente de si la petición fue exitosa o no, cambiamos el estado de loading a false para indicar que ya no estamos cargando y asi poder volver a habilitar el botón de búsqueda
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 flex flex-col items-center max-w-md mx-auto">
      <div>
        <label className="block font-medium mb-1">Fecha Publicación En El BOE (AAAAMMDD)</label>
        <input
          type="text"
          value={fecha}
          onChange={e => setFecha(e.target.value)}
          className="w-full border rounded px-3 py-2"
          placeholder="20250703"
        />
      </div>
      <div>
        <label className="block font-medium mb-1">Número de expediente</label>
        <input
          type="text"
          value={expediente}
          onChange={e => setExpediente(e.target.value)}
          className="w-full border rounded px-3 py-2"
          placeholder="BOE-B-2025-22668"
        />
      </div>
      {error && <p className="text-red-600">{error}</p>}
      <div className="text-center mt-4 w-100">
        <Button
          type="submit"
          variant="primary"
          block
          disabled={loading}
        >
          {loading ? 'Buscando…' : 'Buscar en BOE'}
        </Button>
      </div>
    </form>
  )
}

