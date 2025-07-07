/**
 * @fileoverview
 * En este .jsx definiremos nuestro anel de análisis que mostrará varios gráficos basados en los datos scrapeados, en este caso hemos definido 5 gráficos:
 * 1. Frecuencia de términos de corrupción.
 * 2. Histograma de polaridad de sentimiento.
 * 3. Top entidades mencionadas y su polaridad media.
 * 4. Distribución de sentimiento por fuente.
 * 5. Gráfico de dispersión de entidades vs. polaridad media.
 */
import React, { useMemo } from 'react'
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid,
    ResponsiveContainer, Legend,
    ScatterChart, Scatter, Cell, Label
} from 'recharts'

/**
 * Dashboard de analisis de los artículos scrapeados
 *
 * @param {Object} props
 * @param {Array<Object>} [props.items=[]]
 *   Array de items(objetos), cada uno con:
 *     - content_preview: Vista previa del contenido extraido de las noticias.
 *     - sentiment_polarity: Sentimiento (número entre -1 y 1).
 *     - entities: Array de entidades extraidas con NLP ({ text, label }).
 *     - source: Nombre de la fuente de las noticias.
 * @param {Array<string>} [props.terms=[]]
 *   Lista de términos de corrupción a contar en los artículos.
 * @returns {JSX.Element}
 */


export default function AnalysisDashboard({ items = [], terms = [] }) {
    //definimos como constantes los colores para la polaridad de sentimiento 
    const COLOR_ROJO = '#FF4D4F'
    const COLOR_AMARILLO = '#FFBB28'
    const COLOR_VERDE = '#52C41A'

    console.log("🔍 items recibidos:", items)
    console.log("🔍 entidades raw de cada ítem:", items.map(i => i.entities))

    //hacemos un calculo de frecuencia de cada término en todos los content_preview(es decir el contenido extraido de las noticias)
    //Usamos useMemo para que este cálculo se haga una sola vez y no en cada renderizado para evitar calculos innecesarios
    const termFrequency = useMemo(() => {
        const freq = {}
        //Creamos un contador para cada termino
        terms.forEach(t => { freq[t] = 0 })
        //iteramos sobre cada item content_preview y contamos las apariciones de cada termino
        items.forEach(({ content_preview = "" }) => {
            //normalizamos el texto a minusculas porque nuestros base corruption terms estan en minusculas
            const text = content_preview.toLowerCase()
            //para cada termino, contamos las apariciones en el texto
            //usamos una expresión regular para contar las ocurrencias exactas de cada término
            //la expresión RegExp busca el término como una palabra completa (\\b) y la 'g' al final indica que queremos todas las ocurrencias
            terms.forEach(t => {
                const count = (text.match(new RegExp(`\\b${t.toLowerCase()}\\b`, 'g')) || []).length
                freq[t] += count
            })
        })
        //convertimos el objeto freq a un array de objetos con { term, count } para que recharts pueda usarlo y lo renderice correctamente
        return Object.entries(freq).map(([term, count]) => ({ term, count }))
    }, [items, terms])


    const sentimentBins = useMemo(() => {
        const bins = []
        const binSize = 0.2
        //creamos los bins de polaridad desde -1 hasta 1 con un tamaño de bin de 0.2
        //primera iteracion sera con un start de -1 y un end de -0.8, luego -0.8 a -0.6, etc.
        for (let start = -1; start < 1; start += binSize) {
            const end = start + binSize
            //creamos un label con javascript que convierte el rango en un string para poder luego mostrarlo en el eje x del grafico
            const label = `${start.toFixed(1)} to ${end.toFixed(1)}`
            //basicamente creamos un objeto con el rango, el conteo,(que seran los articulos que caen en ese rango), inicial a 0 y los valores de inicio y fin del bin
            bins.push({ range: label, count: 0, start, end })
        }
        //asignamos cada artículo a su bin según su polaridad iterando sobre los items
        items.forEach(({ sentiment_polarity }) => {
            //convertimos la polaridad a un número flotante, si no es un número válido, usamos 0, esto debido a que al estar usando pysentimiento a veces ha fallado en los resultados que devuelve.  
            const val = parseFloat(sentiment_polarity) || 0
            //para asegurarnos de que un articulo que por ejemplo tenga una polaridad de 1, caiga en el último bin, usamos una segunda condicion que usará la segunda comparacion para ese bin "especial"
            const bin = bins.find((b, i) =>
                i === bins.length - 1
                    ? val >= b.start && val <= b.end
                    : val >= b.start && val < b.end
            )
            //incrementamos para ese rango de polaridad el conteo de artículos que caen en ese rango
            if (bin) bin.count += 1
        })
        //finalmente devolvemos el array de bins con su rango, conteo, inicio y fin, la razon para devolver start y end es que los usaremos para colorear los bins en el grafico
        return bins.map(({ range, count, start, end }) => ({ range, count, start, end }))
    }, [items])

    //
    const entityData = useMemo(() => {
        const freq = {}
        //solo nos interesa el array de entidades y la polaridad de sentimiento
        items.forEach(({ entities = [], sentiment_polarity }) => {
            //convertimos la polaridad a un número flotante, si no es un número válido, usamos 0 como hicimos en el histograma de polaridad
            const pol = parseFloat(sentiment_polarity) || 0
            //iteramos sobre cada entidad y contamos las apariciones de cada una
            entities.forEach(e => {
                const key = e.text
                //Si es la primera vez que vemos esta entidad, la inicializamos en el objeto freq
                if (!freq[key]) freq[key] = { count: 0, sumSent: 0 }
                //Sumamos 1 al contador de esa entidad y sumamos la polaridad al sumSent
                //esto nos servirá para luego calcular la polaridad media de esa entidad
                freq[key].count += 1
                freq[key].sumSent += pol
            })
        })

        //convertimos el objeto freq a un array de objetos con { entity como clave, count y sentimiento como valores de cada clave}
        const arr = Object.entries(freq)
            //transformamos el array de entradas en un array de objetos con la polaridad media por entidad
            .map(([entity, { count, sumSent }]) => ({
                entity,
                count,
                avgSentiment: sumSent / count
            }))
            //ordenamos el array por el conteo de menciones de cada entidad, de mayor a menor
            .sort((a, b) => b.count - a.count)
            //Para evitar problemas que he tenido de saturar el grafico ponemos un limite de 20 entidades mas relevantes, de ahi el ordenamiento
            .slice(0, 20)
        // Aquí metemos el log para ver en la consola del navegador
        console.log("🔍 entityData:", arr)

        //devolvemos el array listo para que recharts pueda usarlo y lo renderice correctamente
        return arr
    }, [items])

    //Aqui calculamos las estadísticas de sentimiento por fuente para el grafico de barras
    const sourceStats = useMemo(() => {

        const stats = {}
        //iteramos sobre cada item que ha recogido el scraper y contamos los artículos positivos, neutrales y negativos por fuente
        items.forEach(({ source, sentiment_polarity }) => {
            //Si es la primera vez que vemos esta fuente, la inicializamos en el objeto stats
            if (!stats[source]) stats[source] = { positive: 0, neutral: 0, negative: 0 }
            const pol = parseFloat(sentiment_polarity) || 0
            //según el valor de polaridad, incrementamos el contador correspondiente
            if (pol > 0.1) stats[source].positive++
            else if (pol < -0.1) stats[source].negative++
            else stats[source].neutral++

        })
        //para simplificar tamanio del codigo seguimos la misma logica seguida en anteriores funciones, convertimos el objeto stats a un array de objetos con { source, positive, neutral, negative } y luego convertimos a un array para que recharts pueda usarlo 
        return Object.entries(stats).map(([source, vals]) => ({ source, ...vals }))
    }, [items])


    return (
        <div className="container py-4">
            <div className="row">
                <div className="col-md-6">
                    <h5>Frecuencia de términos</h5>
                    <p className="text-sm text-gray-600 mb-2">
                        Número de apariciones de cada indicador de corrupción en los artículos.
                    </p>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={termFrequency} margin={{ top: 20, right: 30, left: 0, bottom: 80 }}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis
                                dataKey="term"
                                interval={0}
                                angle={-45}
                                textAnchor="end"
                                height={60}
                                tick={{
                                    fontFamily: 'Arial, sans-serif',
                                    fontWeight: 'bold',
                                    fontSize: 12,
                                    fill: '#555'
                                }}>
                                <Label
                                    value="Término de irregularidad"
                                    position="bottom"
                                    offset={50}
                                    style={{
                                        fontFamily: 'Arial, sans-serif',
                                        fontWeight: 'bold',
                                        fontSize: 14,
                                        fill: '#333'
                                    }} />
                            </XAxis>

                            <YAxis
                                tick={{
                                    fontFamily: 'Arial, sans-serif',
                                    fontWeight: 'bold',
                                    fontSize: 12,
                                    fill: '#555'
                                }}>
                                <Label
                                    value="Veces mencionado"
                                    position="insideLeft"
                                    angle={-90}
                                    style={{
                                        textAnchor: 'middle',
                                        fontFamily: 'Arial, sans-serif',
                                        fontWeight: 'bold',
                                        fontSize: 14,
                                        fill: '#333'
                                    }} />
                            </YAxis>

                            <Tooltip />
                            <Bar dataKey="count" fill="#8884d8" />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
                <div className="col-md-6">
                    <h5>Histograma de polaridad</h5>
                    <p className="text-sm text-gray-600 mb-2">
                        Distribución de los puntajes de sentimiento (−1 muy negativo, +1 muy positivo).
                    </p>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={sentimentBins} margin={{ top: 20, right: 30, left: 2, bottom: 60 }}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="range">
                                <Label
                                    value="Rango de polaridad"
                                    position="bottom"
                                    style={{
                                        fontSize: 14,
                                        fontWeight: 'bold',
                                        fontFamily: 'Arial, sans-serif',
                                        fill: '#333',
                                    }}
                                    offset={20}
                                    fontSize={12}
                                    fill="#555"
                                />
                            </XAxis>
                            <YAxis>
                                <Label
                                    value="Conteo de artículos"
                                    position="left"
                                    angle={-90}
                                    style={{
                                        textAnchor: 'middle',
                                        fontSize: 14,
                                        fontWeight: 'bold',
                                        fontFamily: 'Arial, sans-serif',
                                        fill: '#333',
                                    }}
                                    offset={-10}
                                    fontSize={12}
                                    fill="#555"
                                />
                            </YAxis>

                            <Tooltip />
                            <Bar dataKey="count">
                                {sentimentBins.map((bin, idx) => {

                                    const color =
                                        bin.end <= 0 ? COLOR_ROJO :
                                            bin.start >= 0 ? COLOR_VERDE :
                                                COLOR_AMARILLO
                                    return <Cell key={idx} fill={color} />
                                })}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>
            <div className="row mt-4">
                <div className="col-md-6">
                    <h5>Top entidades mencionadas</h5>
                    <p className="text-sm text-gray-600 mb-2">
                        Las entidades (personas/organizaciones/lugares) más citadas.
                    </p>
                    <ResponsiveContainer width="100%" height={400}>
                        <BarChart data={entityData} margin={{ top: 20, right: 30, left: 0, bottom: 80 }}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis
                                dataKey="entity"
                                interval={0}
                                angle={-45}
                                textAnchor="end"
                                height={60}
                                tick={{
                                    fontFamily: 'Arial, sans-serif',
                                    fontWeight: 'bold',
                                    fontSize: 12,
                                    fill: '#555'
                                }}>
                                <Label
                                    value="Entidad"
                                    position="bottom"
                                    offset={50}
                                    style={{
                                        fontFamily: 'Arial, sans-serif',
                                        fontWeight: 'bold',
                                        fontSize: 14,
                                        fill: '#333'
                                    }} />
                            </XAxis>
                            <YAxis
                                tick={{
                                    fontFamily: 'Arial, sans-serif',
                                    fontWeight: 'bold',
                                    fontSize: 12,
                                    fill: '#555'
                                }}
                            >
                                <Label
                                    value="Número de menciones"
                                    position="insideLeft"
                                    angle={-90}
                                    style={{
                                        textAnchor: 'middle',
                                        fontFamily: 'Arial, sans-serif',
                                        fontWeight: 'bold',
                                        fontSize: 14,
                                        fill: '#333'
                                    }}
                                />
                            </YAxis>
                            <Tooltip />
                            <Bar dataKey="count" fill="#ffc658" />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
                <div className="col-md-4">
                    <h5>Entidad vs. Polaridad (scatter)</h5>
                    <p className="text-sm text-gray-600 mb-2">
                        Frecuencia de menciones (eje X) frente al sentimiento medio (eje Y) por entidad.
                    </p>
                    <ResponsiveContainer width="100%" height={300}>
                        <ScatterChart margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                            <CartesianGrid />
                            <XAxis
                                type="number"
                                dataKey="count"
                                name="Frecuencia"
                                domain={[0, 'dataMax + 1']}
                                tick={{
                                    fontFamily: 'Arial, sans-serif',
                                    fontWeight: 'bold',
                                    fontSize: 12,
                                    fill: '#555'
                                }}>
                                <Label
                                    value="Frecuencia de menciones"
                                    position="bottom"
                                    offset={10}
                                    style={{
                                        fontFamily: 'Arial, sans-serif',
                                        fontWeight: 'bold',
                                        fontSize: 14,
                                        fill: '#333'
                                    }}
                                />
                            </XAxis>
                            <YAxis
                                type="number"
                                dataKey="avgSentiment"
                                name="Polaridad media"
                                domain={[-1, 1]}
                                tick={{
                                    fontFamily: 'Arial, sans-serif',
                                    fontWeight: 'bold',
                                    fontSize: 12,
                                    fill: '#555'
                                }}>
                                <Label
                                    value="Polaridad media"
                                    position="insideLeft"
                                    angle={-90}
                                    style={{
                                        textAnchor: 'middle',
                                        fontFamily: 'Arial, sans-serif',
                                        fontWeight: 'bold',
                                        fontSize: 14,
                                        fill: '#333'
                                    }} />
                            </YAxis>
                            <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                            <Scatter name="Entidades" data={entityData} fill="#8884d8" />
                        </ScatterChart>
                    </ResponsiveContainer>
                </div>
            </div>
            <div className="row mt-4">
                <div className="col-md-8">
                    <h5>Distribución de sentimiento por fuente</h5>
                    <p className="text-sm text-gray-600 mb-2">
                        Número de artículos positivos, neutrales y negativos por medio.
                    </p>
                    { }
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={sourceStats} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="source" />
                            <YAxis
                                tick={{
                                    fontFamily: 'Arial, sans-serif',
                                    fontWeight: 'bold',
                                    fontSize: 12,
                                    fill: '#555'
                                }}>
                                <Label
                                    value="Número de artículos"
                                    position="insideLeft"
                                    angle={-90}
                                    style={{
                                        textAnchor: 'middle',
                                        fontFamily: 'Arial, sans-serif',
                                        fontWeight: 'bold',
                                        fontSize: 14,
                                        fill: '#333'
                                    }}
                                />
                            </YAxis>
                            <Tooltip />
                            <Legend />
                            <Bar dataKey="positive" stackId="a" fill="#00C49F" />
                            <Bar dataKey="neutral" stackId="a" fill="#FFBB28" />
                            <Bar dataKey="negative" stackId="a" fill="#FF8042" />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
                { }
            </div>
        </div>
    )
}
