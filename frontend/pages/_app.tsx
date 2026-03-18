import '../styles/globals.css'
import type { AppProps } from 'next/app'
import { AuthProvider } from '../lib/auth'
import Navigation from '../components/Navigation'

export default function App({ Component, pageProps }: AppProps) {
  return (
    <AuthProvider>
      <Navigation />
      <Component {...pageProps} />
    </AuthProvider>
  )
}
