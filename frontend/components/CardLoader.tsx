'use client'
import React from 'react'
import LoadingSpinner from './LoadingSpinner'

interface CardLoaderProps {
  isLoading: boolean
  height?: string
  children?: React.ReactNode
}

/**
 * Component-level loader for cards and sections
 * Wraps content and shows spinner overlay when loading
 */
export default function CardLoader({ isLoading, height = '300px', children }: CardLoaderProps) {
  if (!isLoading) {
    return <>{children}</>
  }

  return (
    <div
      style={{
        height,
        border: '1px solid var(--border-glass, rgba(0,0,0,0.1))',
        borderRadius: '16px',
        background: 'rgba(12, 17, 26, 0.72)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        position: 'relative'
      }}
    >
      <LoadingSpinner size="medium" />
    </div>
  )
}
