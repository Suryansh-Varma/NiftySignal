import '../styles/globals.css'
import type { AppProps } from 'next/app'
import { AuthProvider } from '../lib/auth'
import Navigation from '../components/Navigation'
import { useRouter } from 'next/router'

export default function App({ Component, pageProps }: AppProps) {
  const router = useRouter()
  const isAuthPage = router.pathname === '/login' || router.pathname === '/signup'

  return (
    <AuthProvider>
      {!isAuthPage && <Navigation />}
      <main style={{ paddingTop: isAuthPage ? 0 : '88px' }}>
        <Component {...pageProps} />
      </main>
    </AuthProvider>
  )
}
