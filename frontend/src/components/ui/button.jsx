/**
 * @fileoverview Componente Button: wrapper sobre button de Bootstrap con variantes de estilo, tamaños,etc.
 * 
 * Este componente unifica la forma de renderizar botones en la app al:
 * Soportar variantes (primary, secondary, link, ghost) mapeadas a clases de Bootstrap predefinidas.
 * Controla el tamaño, (se explica mas abajo), (sm, md, lg) ajustando paddings y fuente.
 * Permite ocupar todo el ancho de su contenedor con `block`, por defecto lo dejamos en false porque pocas veces necesitamos ese comportamiento.
 * Acepta `className` para extensiones puntuales, esto nos permite añadir clases css adicionales en caso de que sea necesario personalizar más allá de las variantes y tamaños predefinidos.
 */
import React from 'react'

/**
 * Botón reutilizable con variantes de estilo, tamaño y opción de bloque completo.
 * @param {object} props Props del componente, es el objeto en el que se definen todas las propiedades del botón.
 * @param {React.ReactNode} props.children Cualquier contenido que se introduzca entre las etiquetas del botón.
 * @param {'primary'|'secondary'|'link'|'ghost'} [props.variant='primary'] Son los estilos predefinidos, en este caso de bootstrap. Internamente se traduce en una clase de Bootstrap que asigna colores de fondo, borde y comportamiento al pasar el ratón.
 * @param {'sm'|'md'|'lg'} [props.size='md'] Controlamos el padding y el tamaño de fuente para adaptarlo a un botón pequeño(sm), mediano(md) o grande(lg). Por defecto es mediano(md).
 * @param {boolean} [props.block=false] Si es true se añadiría la clase w-full para que el botón ocupe todo el ancho de su contenedor.
 * @param {string} [props.className] Esto basicamente nos permite añadir clases CSS adicionales en caso de que necesitásemos personalizar más allá de las variantes y tamaños predeterminados.
 * @param {...any} props Captura cualquier otra propiedad que pudieramos necesitar pasar al elemento <button>, como onClick, etc. De esta manera el componente es totalmente transparente y reutilizable para cualquier caso de uso.
 * @returns {JSX.Element} El resultado que devolveremos es un botón estilizado con las clases de Bootstrap y los estilos aplicados.
 */

export function Button({ children, variant = 'primary', size = 'md', block = false, className = '', ...props  }) {
  const base = 'px-4 py-2 rounded-lg font-medium focus:outline-none'
  
  
  const variants = {
    primary: 'btn-primary',
    secondary: 'btn-secondary',
    link: 'btn-link',
    ghost: 'btn-outline-primary',
  }

 const sizeClasses = {
    sm: 'px-2 py-1 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  }

  const blockClass = block ? 'w-full' : ''

  return (
    <button
      className={`btn ${variants[variant]} ${sizeClasses[size] || sizeClasses.md} ${blockClass} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}