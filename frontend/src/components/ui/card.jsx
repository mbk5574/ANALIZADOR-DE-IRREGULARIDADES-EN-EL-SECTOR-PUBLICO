/**
 * @fileoverview Wrappers de tarjeta (Card) para Bootstrap.
 *
 * En conjunto, estos tres componentes facilitan mantener la consistencia
 * visual en toda la aplicación: todas las “tarjetas” lucirán igual, y también nos permite
 * inyectarles un `className` adicional cuando necesitemos adaptarlas a un caso concreto.
 */

import React from 'react'

/**
 * Contenedor principal tipo tarjeta (Bootstrap) que centra el contenido y limita el ancho.
 * @param {object} props Props del componente Card, que es un contenedor con sombra y ancho máximo.
 * @param {React.ReactNode} props.children Los elementos que se renderizarán dentro de la Card. 
 * @param {string} [props.className=''] Clases CSS adicionales para personalizar la tarjeta.
 * @returns {JSX.Element} El resultado que devolveremos será un contenedor estilo Bootstrap card con sombra y un ancho máximo de 900px.
 */

export function Card({ children, className = '' }) {
  return (
    <div className={`card shadow-sm mx-auto ${className}`} style={{ maxWidth: '900px' }}>
      {children}
    </div>
  )
}

/**
 * Cabecera de una tarjeta con fondo blanco y sin borde.
 * @param {object} props Props del componente CardHeader.
 * @param {React.ReactNode} props.children Los elementos que se mostrarán en la cabecera.
 * @param {string} [props.className=''] Clases CSS adicionales para personalizar el encabezado.
 * @returns {JSX.Element} Devolvemos un contenedor estilo Bootstrap card-header.
 */
export function CardHeader({ children, className = '' }) {
  return <div className={`card-header bg-white border-0 ${className}`}>{children}</div>
}

/**
 * Cuerpo de la tarjeta donde va el contenido principal.
 * @param {object} props Propiedades del componente CardContent.
 * @param {React.ReactNode} props.children Elementos que se mostrarán dentro del cuerpo.
 * @param {string} [props.className=''] Clases CSS adicionales para personalizar el cuerpo.
 * @returns {JSX.Element} devolvewmos un contenedor body usando el estilo Bootstrap card-body predefinido.
 */
export function CardContent({ children, className = '' }) {
  return <div className={`card-body ${className}`}>{children}</div>
}