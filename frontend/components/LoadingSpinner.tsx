'use client'
import React from 'react'

interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large'
  fullPage?: boolean
  message?: string
}

export default function LoadingSpinner({ size = 'medium', fullPage = false, message }: LoadingSpinnerProps) {
  const sizeClasses = {
    small: 'w-6 h-6',
    medium: 'w-12 h-12',
    large: 'w-16 h-16'
  }

  const spinnerContent = (
    <div className="flex flex-col items-center justify-center gap-4">
      <div className={`${sizeClasses[size]} relative`}>
        {/* Outer ring */}
        <div
          className="absolute inset-0 rounded-full border-4 border-transparent border-t-current border-r-current opacity-75"
          style={{
            animation: 'spin 2s linear infinite',
            color: 'var(--primary-600, #3b82f6)'
          }}
        />
        {/* Inner ring */}
        <div
          className="absolute inset-2 rounded-full border-2 border-transparent border-b-current opacity-50"
          style={{
            animation: 'spin 3s linear infinite reverse',
            color: 'var(--accent-500, #10b981)'
          }}
        />
      </div>
      {message && (
        <p style={{ color: 'var(--slate-600)', fontSize: '0.95rem', marginTop: '0.5rem', fontWeight: 500 }}>
          {message}
        </p>
      )}
      <style jsx>{`
        @keyframes spin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }
      `}</style>
    </div>
  )

  if (fullPage) {
    return (
      <div
        className="fixed inset-0 z-50 flex items-center justify-center"
        style={{
          background: 'rgba(255, 255, 255, 0.85)',
          backdropFilter: 'blur(4px)',
          WebkitBackdropFilter: 'blur(4px)'
        }}
      >
        {spinnerContent}
      </div>
    )
  }

  return spinnerContent
}
