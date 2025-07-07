/**
 * @fileoverview
 * Componente raiz de la aplicación “Analizador de Irregularidades”.
 * Orquesta el siguient flujo de pasos: 
 * 1) Subida de PDF de contrato, 
 * 2) consulta en el BOE, 
 * 3) definicion de términos de búsqueda por el usuario, 
 * 4) ejecución y monitorización de jobs de scraping(como hemos comentado anteriormente, pueden ejecutarse varios jobs en paralelo),
 * 5) visualización de resultados y análisis.
 * Usamos Bootstrap para el diseño general y tambien para los graficos finales de la seccion de analisis y React para gestionar estado y rutas internas.
 */

import React, { useState, useEffect } from 'react'
import { CardHeader, CardContent } from './components/ui/card'
import { Button } from './components/ui/button'
import { Progress } from './components/ui/progress'
import { motion, AnimatePresence } from 'framer-motion'
import UploadContract from './components/UploadContract'
import BoeForm from './components/BoeForm'
import ContractDetails from './components/ContractDetails'
import TermsForm from './components/TermsForm'
import JobStatus from './components/JobStatus'
import JobResults from './components/JobResults'
import 'bootstrap/dist/css/bootstrap.min.css'
import './index.css'
import AnalysisDashboard from './components/AnalysisDashboard'


const stepLabels = [
  { key: 'upload', label: 'Subir PDF' },
  { key: 'boe', label: 'BOE' },
  { key: 'terms', label: 'Términos' },
  { key: 'results', label: 'Resultados' },
  { key: 'analysis', label: 'Análisis' },
]

/**
 * Componente principal que gestiona el wizard de pasos y muestra los resultados al finalizar, a tener en cuenta que el analisis se visualiza haciendo click en siguiente cuando se finaliza un job(y devuelve resultados).
 * @returns {JSX.Element}
 */

export default function App() {
  //terminos del PDF y del BOE
  const [fileTerms, setFileTerms] = useState([])
  const [boeData, setBoeData] = useState(null)
  const [boeFecha, setBoeFecha] = useState('')
  const [boeExp, setBoeExp] = useState('')
  //jobs que se van creando, cada uno con su id y resultados
  const [jobs, setJobs] = useState([])
  const [currentJobId, setCurrentJobId] = useState(null)
  //estado del stepper(hemos dividido la aplicacion en pasos muy bien definidos para que el usuario pueda seguir el flujo de manera sencilla)
  const [step, setStep] = useState(0)
  const totalSteps = stepLabels.length
  //items que se van obteniendo de los jobs, al final se usan para el analisis(step 5) y mostrar los resultados(step 4)
  const [allItems, setAllItems] = useState([])
  //indicadores que se usan para el analisis, se obtienen del backend al inicio de la aplicacion
  const [indicators, setIndicators] = useState([])

  //Funciones para avanzar o retroceder en el stepper 
  const next = () => setStep(s => Math.min(s + 1, totalSteps - 1))
  const prev = () => setStep(s => Math.max(s - 1, 0))

  /**
   * Handle: se llama tras subir un contrato con exito.
   * Extrae los terminos relevantes y avanza al siguiente paso.
   * @param {{ terms: string[], notice: any }} payload Datos recibidos del backend
   */
  const handleUpload = ({ terms = [], notice }) => {
    //guardamos los terminos extraidos del pdf
    const extra = [notice?.adjudicatario, notice?.entidad, notice?.objeto].filter(Boolean)
    //actualizamos el estado de fileTerms con los terminos extraidos del pdf y los que nos pasan como parametro 
    setFileTerms([...new Set([...extra, ...terms])])
    //avanzamos al siguiente paso
    next()
  }

  /**
   * Handle: se va a llamar tras obtener datos del BOE.
   * Almacena la informacion y avanza al paso de terminos que seria el paso 3
   * @param {object} data Datos del contrato del BOE
   * @param {string} fecha Fecha publicada en BOE (AAAAMMDD)
   * @param {string} expediente Identificador de expediente
   */
  const handleFound = (data, fecha, expediente) => {
    setBoeData(data)
    setBoeFecha(fecha)
    setBoeExp(expediente)
    next()
  }

  /**
   * Callback cuando un job termina: guarda resultados en el job y
   * si es el job activo, actualiza la lista de items con los resultados del job que ha terminado.
   * @param {string} id Identificador del job
   * @param {any[]} res Resultados obtenidos
   */
  const handleJobFinished = (id, res) => {
    setJobs(js => js.map(j => j.id === id ? { ...j, results: res } : j))
    if (id === currentJobId) {
      setAllItems(res)
    }
  }

  /**
   * Handle: tras crear un job, lo añade a la lista y avanza a "Resultados" donde esperaremos hasta que termine y se muestren los mismos.
   * @param {string} id Identificador del nuevo job
   */
  const handleJobCreated = id => {
    setJobs(js => [...js, { id, results: null }])
    setCurrentJobId(id)
    next()
  }

  //indicadores cargados al inicio de la aplicacion desde el backend
  useEffect(() => {
    fetch("/indicators")
      .then(r => r.json())
      .then(setIndicators)
      .catch(console.error)
  }, [])

  /**
   * Esta funcion es el componente principal que renderiza el contenido segun el paso actual, esta dividido por case y cada case es un paso en el flujo.
   * - 0: UploadContract
   * - 1: BoeForm
   * - 2: ContractDetails + TermsForm
   * - 3: Lista de JobStatus y JobResults
   * - 4: AnalysisDashboard
   * Aqui es donde a cada hijo (los componentes) se les pasa la informacion necesaria junto con los callbacks necesarios para que se comuniquen correctamente
   */
  const renderStep = () => {
    switch (step) {
      case 0:
        return <UploadContract onUpload={handleUpload} />
      case 1:
        return <BoeForm onFound={handleFound} />
      case 2:
        return (
          <>
            <ContractDetails data={boeData} />
            <TermsForm
              initialTerms={[...fileTerms, boeData.identificador]}
              fecha={boeFecha}
              expediente={boeExp}
              onJobCreated={handleJobCreated}
            />
          </>
        )
      case 3:
        const current = jobs.find(j => j.id === currentJobId)

        return (
          <div className="space-y-6">
            {jobs.map(j => (
              <div key={j.id} className="p-4 border rounded-lg shadow-sm">
                <JobStatus jobId={j.id}
                  onFinished={res => handleJobFinished(j.id, res)} />
                {j.results && (
                  <Button variant="link"
                    className="mt-2"
                    onClick={() => setCurrentJobId(j.id)}>
                    Ver resultados de {j.id.slice(0, 8)}…
                  </Button>
                )}
              </div>
            ))}

            {currentJobId && (
              <div className="mt-6">
                <Button
                  variant="secondary"
                  className="mb-4"
                  onClick={() => setCurrentJobId(null)}
                >
                  ← Volver a lista de jobs
                </Button>
                <JobResults
                  jobId={currentJobId}
                  items={jobs.find(j => j.id === currentJobId).results}
                />
              </div>
            )}
          </div>
        )
      case 4:
        return (allItems.length > 0 && indicators.length > 0)
          ? <AnalysisDashboard items={allItems} terms={indicators} />
          : <p className="text-center text-gray-500">Cargando datos de análisis…</p>
      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-white flex flex-col">
      <header className="bg-white shadow-md">
        <div className="container mx-auto py-6">
          <h1 className="text-5xl font-extrabold text-blue-800 text-center">
            Analizador de Irregularidades
          </h1>
        </div>
      </header>

      <main className="flex-1">
        <div className="flex justify-center px-6 py-8">
          <div className="w-full max-w-3xl">
            {/*STEPPER*/}
            <Progress
              value={((step + 1) / totalSteps) * 100}
              className="h-3 rounded-full bg-gray-200 mb-4"
            />
            <div className="d-flex justify-content-center mb-4">
              {stepLabels.map((s, i) => {

                const isLast = i === totalSteps - 1
                const disabled = isLast
                  ? allItems.length === 0
                  : i > step
                const active = i === step
                const btnClass = active
                  ? 'btn btn-primary mx-1'
                  : disabled
                    ? 'btn btn-outline-secondary mx-1 disabled'
                    : 'btn btn-outline-primary mx-1'

                return (
                  <button
                    key={s.key}
                    onClick={() => !disabled && setStep(i)}
                    disabled={disabled}
                    className={btnClass}
                  >
                    {s.label}
                  </button>
                )
              })}
            </div>

            {/*CARD ANIMADA*/}
            <AnimatePresence exitBeforeEnter>
              <motion.div
                key={step + (currentJobId || '')}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -30 }}
                transition={{ duration: 0.3 }}
              >
                <div className="bg-white shadow-lg rounded-lg overflow-hidden">
                  <CardHeader>
                    <h2 className="text-2xl font-semibold text-gray-800 p-6 text-center">
                      Paso {step + 1}: {stepLabels[step].label}
                    </h2>
                  </CardHeader>
                  <CardContent className="p-6">
                    {/*ESTE DIV ES EL WRAPPER QUE CENTRA Y LIMITA ANCHO*/}
                    <div className="w-full max-w-md mx-auto space-y-4">
                      {renderStep()}
                    </div>
                  </CardContent>
                </div>
              </motion.div>
            </AnimatePresence>
          </div>
        </div>

        {/*BOTONES DE NAVEGACION*/}
        <div className="px-6 pb-8">
          <div className="max-w-3xl mx-auto flex justify-between">
            <Button
              variant="ghost"
              onClick={prev}
              disabled={step === 0}
              className={`px-4 py-2 rounded
                ${step === 0
                  ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                  : 'bg-white text-gray-800 hover:bg-gray-100'}
              `}
            >
              Anterior
            </Button>

            <Button
              variant="ghost"
              onClick={step === totalSteps - 1 ? () => window.location.reload() : next}
              disabled={
                (step < totalSteps - 1 && step !== 2 && step !== 3)
                || (step === 3 && allItems.length === 0)
              }
              className={`px-4 py-2 rounded
                ${(step < totalSteps - 1 && step !== 2 && step !== 3)
                  || (step === 3 && allItems.length === 0)
                  ? 'bg-gray-200 text-gray-500 cursor-not-allowed'
                  : 'bg-white text-gray-800 hover:bg-gray-100'
                }
              `}
            >
              {step === totalSteps - 1 ? 'Reiniciar' : 'Siguiente'}
            </Button>
          </div>
        </div>
      </main>
    </div>
  )
}