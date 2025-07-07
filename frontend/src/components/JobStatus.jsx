/**
 * @fileoverview
 * Componente que muestra el estado de un job de scraping/análisis y, cuando se completa,
 * solicita automáticamente sus resultados. Realiza polling al endpoint `/jobs/:jobId`
 * cada 5 segundos hasta que el estado es `finished`, y entonces llama a `onFinished(data)`.
 */

import React, { useEffect, useState, useRef } from 'react'
const API = import.meta.env.VITE_API_URL

/**
 * Basicamente este JobStatus.jsx realizara un polling periodico sobre el estado de un job y notificara
 * al final cuando haya resultados disponibles.
 *
 * @param {object} props
 * @param {string} props.jobId      Identificador del job a monitorizar.
 * @param {function(Array):void} props.onFinished  Callback que recibe el array de resultados
 *                                                (`/jobs/:jobId/results`) cuando el job termina.
 *
 * @returns {JSX.Element|null}
 * - Mientras carga o hace polling, renderiza:  
 *   `Job <jobId>: <estado>`  
 * - Si ocurre un error en la peticion, muestra un mensaje en rojo con la cruz:  
 *   `❌ <mensaje de error>`
 */


export default function JobStatus({ jobId, onFinished }) {
  //estado actual del job: 'pending', 'running', 'finished', etc.
  const [status, setStatus] = useState('')
  //para en caso de que ocurra un error
  const [error, setError] = useState('')
  //creamos tambien la referencia para manejar el timeout del polling
  const timeoutRef = useRef(null)
  //y la referencia para evitar que se llame varias veces a onFinished
  const finishedRef = useRef(false)
  //finalmente creamos una referencia para mantener la ultima version de onFinished
  const onFinishedRef = useRef(onFinished)

  //mantenemos la referencia actualizada de onFinished para evitar problemas de cierre (closure) en el useEffect
  //esto es necesario porque si onFinished cambia, queremos que el useEffect use la nueva version
  //de esta forma, si el padre que en este caso es app.jsx cambia la funcion onFinished, el componente JobStatus usara la nueva version
  //Esto ha sido necesario hacerlo para desacoplar la logica del polling de los cambios que puedan producirse en el componente padre
  useEffect(() => { onFinishedRef.current = onFinished }, [onFinished])

  //Cuando recibe un nuevo jobId, reinicia el estado y comienza el polling
  useEffect(() => {
    if (!jobId) return

    //reiniciamos el estado y limpiamos el timeout
    finishedRef.current = false
    clearTimeout(timeoutRef.current)
    /**
     * Función que consulta el estado del job y, si ha terminado,
     * solicita y pasa los resultados al callback `onFinished`.
     * En caso contrario, vuelve a programarse tras 5s para seguir consultando.
     */
    const poll = async () => {
      try {
        //consultamos el estado del job haciendo una llamada al endpoint /jobs/:jobId
        const res = await fetch(`${API}/jobs/${jobId}`)
        if (!res.ok) throw new Error(`Error estado (${res.status})`)
        //si la llamada es exitosa, obtenemos el estado del job
        const { status: st } = await res.json()
        setStatus(st)
        //si el estado es finished y finishedRef.current es falso, significa que es la primera vez que recibimos el estado finished
        if (st === 'finished' && !finishedRef.current) {

          finishedRef.current = true
          //cancelamos el temporizador de polling, muy importante o sino podria seguir llamando a poll sin sentido (es un problema que he encontrado en el desarrollo de este componente).
          clearTimeout(timeoutRef.current)
          //solicitamos los resultados del job haciendo una llamada al endpoint /jobs/:jobId/results
          const r2 = await fetch(`${API}/jobs/${jobId}/results`)
          if (!r2.ok) throw new Error(`Error resultados (${r2.status})`)
          const data = await r2.json()
          //llamamos a onFinished con los datos obtenidos, esto es lo que hara que el componente padre (app.jsx) reciba los resultados del job
          onFinishedRef.current(data)
        } else if (st !== 'finished') {
          //si el estado no es finished, programamos el siguiente polling que como hemos dicho es cada 5 segundos
          timeoutRef.current = setTimeout(poll, 5000)
        }
      } catch (e) {
        //si ocurre un error, lo guardamos en el estado de error
        //y limpiamos el timeout para evitar que siga llamando a poll 
        setError(e.message)
        clearTimeout(timeoutRef.current)
      }
    }

    poll()
    //limpiamos el timeout al desmontar o cambiar jobId, esta segunda llamada es estrictamente necesaria para evitar que se acumulen timeouts si el jobId cambia antes de que se complete el polling.
    return () => {
      clearTimeout(timeoutRef.current)
    }
  }, [jobId])

  if (error) return <p className="text-red-600">❌ {error}</p>
  return <p>Job <strong>{jobId}</strong>: <em>{status || 'cargando…'}</em></p>
}
