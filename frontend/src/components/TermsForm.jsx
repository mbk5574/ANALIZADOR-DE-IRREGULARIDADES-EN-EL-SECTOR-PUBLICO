/**
 * @fileoverview
 * Formulario para definir los términos de busqueda y lanzar el análisis.
 * Permite añadir, editar y eliminar términos dinámicamente, tambien valida la entrada
 * y envia los datos al backend para crear un nuevo job de scraping con los terminos definidos por el usuario y los extraidos del pdf y de la llamada a la API del BOE.
 */

import React, { useState } from 'react'
const API = import.meta.env.VITE_API_URL
import { Button } from './ui/button'

/**
 * Componente de formulario para enviar los terminos de busqueda al backend y que este realice el trabajo necesario.
 * @param {object} props Props del componente.
 * @param {string[]} props.initialTerms Array inicial de terminos (puede venir del PDF o BOE como hemos comentado antes).
 * @param {string} props.fecha Fecha de publicación en BOE (debe tener este formato de manera obligatoria: AAAAMMDD).
 * @param {string} props.expediente Identificador de expediente en el BOE.
 * @param {function(string): void} props.onJobCreated Callback que recibe el jobId cuando el analisis arranca.
 * @returns {JSX.Element} Formulario con campos dinamicos y un botón de envio.
 */

//Este componente recibe los terminos iniciales(esto se lo pasa el padre como todo lo demas), la fecha y el expediente como props, y una funcion onJobCreated que se llamara cuando el analisis arranque.
export default function TermsForm({ initialTerms = [], fecha, expediente, onJobCreated }) {
  //Si vienen terminos iniciales que serian los extraidos del PDF o del BOE, los usamos como estado inicial, sino(porque el pdf no tuviese el formato deseado o la llamada al BOE fallase) 
  //usariamos un array con un solo elemento vacio para que el usuario pueda empezar a añadir terminos.
  const [terms, setTerms] = useState(initialTerms.length ? initialTerms : [''])
  //error y loading son estados para manejar errores y el estado de carga.
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  
  /**
   * Actualiza el término en la posición `i` con el nuevo valor `v`.
   * /actualiza el estado de terms reemplazando el termino en la posicion indicada por el nuevo valor.
   * Esto permite que el usuario pueda editar los terminos de busqueda que ha introducido y lo gestionamos de manera dinamica
   */
  const handleChange = (i, v) =>
    setTerms(ts => ts.map((t, idx) => idx === i ? v : t))
  /**
   * Añade un nuevo campo de término vacío al final.
   * cuando hacemos click en el boton de añadir termino, simplemente añadimos un nuevo elemento vacio al array preexistente de terms
   */
  const addTerm = () => setTerms(ts => [...ts, ''])
  /**
   * Elimina el campo de término en la posición `i`.
   * cuando hacemos click en el boton de eliminar termino, eliminamos el termino en la posicion indicada por el indice i
   * esto lo hacemos filtrando el array de terms y devolviendo todos los terminos excepto el que tiene el indice i
   */
  const removeTerm = i => setTerms(ts => ts.filter((_, idx) => idx !== i))

  /**
   * Manejador de submit del formulario. Los pasos que realiza son los siguientes:
   * - Valida que haya al menos un termino no vacio.
   * - Verifica que fecha y expediente existan.
   * - Envía POST a `${API}/scrape` con el payload JSON.
   * - Llama a onJobCreated con el id devuelto.
   */
  const handleSubmit = async e => {
    //hemos explicado esta funcionalidad en el .jsx del componente BoeForm.jsx(revisar en caso de duda).
    e.preventDefault()
    //Validamos que al menos haya un término no vacío, y que la fecha y el expediente estén completos
    const clean = terms.map(t => t.trim()).filter(Boolean)
    if (!clean.length) {
      setError('Debes indicar al menos un término de búsqueda')
      return
    }
    if (!fecha || !expediente) {
      setError('Faltan datos de fecha o expediente para iniciar el análisis')
      return
    }
    //ponemos el estado de loading a true para indicar que estamos haciendo una petición al backend
    //y limpiamos errores anteriores si los hubiera
    setLoading(true)
    setError('')
    try {
      //Realizamos la petición POST al backend para iniciar el analisis
      const res = await fetch(`${API}/scrape`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ terms: clean, date: fecha, expediente })
      })
      if (!res.ok) throw new Error(`Error ${res.status}`)
      //Si la petición es exitosa convertimos de json a javaScript el cuerpo de la respuesta y extraemos el id del job creado
      const { id } = await res.json()
      //avisamos al componente padre que el job ha sido creado y le pasamos el id del job
      onJobCreated(id)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block font-medium mb-1 text-center">Términos de búsqueda</label>
        {terms.map((t, i) => (
          <div key={i} className="flex items-center mb-2 space-x-2">
            <input
              type="text"
              value={t}
              onChange={e => handleChange(i, e.target.value)}
              className="flex-1 w-full border rounded px-3 py-2"
              placeholder={`Término ${i + 1}`}
            />
            {terms.length > 1 && (
              <button
                type="button"
                onClick={() => removeTerm(i)}
                className="text-red-500 hover:text-red-700"
              >
                ×
              </button>
            )}
          </div>
        ))}
        <button
          type="button"
          onClick={addTerm}
          className="block mx-auto text-sm text-gray-600 hover:text-gray-800"
        >
          + Añadir término
        </button>
      </div>

      {error && <p className="text-red-600 text-center">{error}</p>}

      <div className="text-center mt-4">
        <Button
          type="submit"
          variant="primary"
          block
          disabled={loading}
        >
          {loading ? 'Iniciando análisis…' : 'Iniciar análisis'}
        </Button>
      </div>
    </form>
  )
}
