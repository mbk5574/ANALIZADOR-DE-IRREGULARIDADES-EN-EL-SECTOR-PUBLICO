/**
 * @fileoverview
 * Progreso visual donde usamos el estilo Bootstrap que muestra una barra rellenable
 * basada en un valor porcentual, en este caso del progreso del step en el que nos encontremos.
 */
import React from 'react'

/**
 * Componente de progreso visual.
 * @param {object} param0 Props del componente.
 * @param {number} param0.value Valor del progreso (0-100).
 * @param {string} param0.className Clases CSS adicionales que queramos aplicar sobre el contenedor `.progress`.
 * @returns {JSX.Element} Elemento contenedor `.progress` con la barra interna `.progress-bar` de bootstrap que refleja el porcentaje y lo muestra como texto
 */
export function Progress({ value = 0, className = '' }) {
  // value entre 0 y 100
  const pct = Math.min(100, Math.max(0, value))

  return (
    <div className={`progress ${className}`}>
      <div
        className="progress-bar"
        role="progressbar"
        style={{ width: `${pct}%` }}
        aria-valuenow={pct}
        aria-valuemin="0"
        aria-valuemax="100"
      >
        {pct}%
      </div>
    </div>
  )
}