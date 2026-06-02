'use client'
import React from 'react'
import LoadingSpinner from './LoadingSpinner'

interface PageLoaderProps {
  isLoading: boolean
  message?: string
}

/**
 * Full-page overlay loader component
 * Place at the top level of your page/layout to cover the entire view
 */
export default function PageLoader({ isLoading, message = 'Loading...' }: PageLoaderProps) {
  if (!isLoading) return null

  return <LoadingSpinner fullPage={true} size="large" message={message} />
}
