'use client'
import React, { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'
import axios from 'axios'
import { useAuth } from '../../lib/auth'
import { getCompanyName, isValidNiftySymbol } from '../../lib/supabase'

export default function CompanyDetail() {
  const router = useRouter()
  const { symbol } = router.query as { symbol?: string }
  const { user, loading: authLoading } = useAuth()
  const [company, setCompany] = useState<any>(null)
  const [recommendation, setRecommendation] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    if (!symbol) return
    if (authLoading) return

    const loadData = async () => {
      try {
        setLoading(true)
        setError('')

        // Validate symbol
        if (!isValidNiftySymbol(symbol)) {
          setError('Invalid stock symbol. Only NSE listed stocks are supported.')
          return
        }

        // Fetch recommendation for this symbol
        const recRes = await axios.get(`${apiUrl}/api/recommendations?symbol=${symbol}`)
        const rec = recRes.data[0] || null
        setRecommendation(rec)

        // Set company info
        setCompany({
          symbol: symbol.toUpperCase(),
          name: getCompanyName(symbol),
          ...rec,
        })
      } catch (err) {
        console.error('Failed to load company data:', err)
        setError('Failed to load company data')
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [symbol, authLoading])

  if (authLoading || loading) {
    return <div className="container"><p>Loading...</p></div>
  }

  if (error) {
    return <div className="container"><div style={{ color: '#ef4444' }}>{error}</div></div>
  }

  if (!company) {
    return <div className="container"><p>Company not found</p></div>
  }

  const recColor = recommendation?.recommendation === 'BUY' ? 'var(--slate-800)' : recommendation?.recommendation === 'SELL' ? 'var(--black)' : 'var(--slate-400)'
  const recBg = recommendation?.recommendation === 'BUY' ? 'var(--slate-100)' : recommendation?.recommendation === 'SELL' ? 'var(--slate-200)' : 'var(--slate-50)'

  return (
    <div className="animate-in" style={{ backgroundColor: 'var(--skeuo-bg)', minHeight: '100vh', padding: '2rem 1rem' }}>
      <div className="container" style={{ maxWidth: 1000 }}>
        {/* Header Section */}
        <div style={{ marginBottom: '3.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '2rem' }}>
          <div>
            <h1 style={{
              margin: 0,
              fontSize: '2.75rem',
              fontWeight: 900,
              color: 'var(--slate-800)',
              textShadow: '1px 1px 0px white',
              display: 'flex',
              alignItems: 'center',
              gap: '1rem'
            }}>
              <span className="skeuo-knob" style={{ width: '40px', height: '40px' }}></span>
              {company.name}
            </h1>
            <p style={{ margin: '0.5rem 0 0 0', color: 'var(--slate-500)', fontSize: '1.25rem', fontWeight: 600, letterSpacing: '0.05em' }}>
              <span className="skeuo-recessed" style={{ padding: '0.2rem 0.8rem', borderRadius: '4px', fontFamily: 'var(--font-mono)' }}>{company.symbol}</span>
            </p>
          </div>
          <div className="skeuo-recessed" style={{ padding: '0.6rem 1.2rem', borderRadius: 'var(--radius-full)', display: 'flex', alignItems: 'center', gap: '0.6rem', fontWeight: 800, color: 'var(--slate-500)', fontSize: '0.8rem' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--slate-400)' }}></span>
            ASSET DATA STREAM v2.1
          </div>
        </div>

        {/* Primary Stats Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '2rem', marginBottom: '3rem' }}>
          <div className="skeuo-card">
            <span style={{ fontSize: '0.7rem', fontWeight: 900, color: 'var(--slate-400)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>MARKET VALUATION</span>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem', marginTop: '0.5rem' }}>
              <span style={{ fontSize: '2.5rem', fontWeight: 900, color: 'var(--slate-800)', fontFamily: 'var(--font-mono)' }}>₹{company.last_price?.toFixed(2) || 'N/A'}</span>
              <span style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--slate-400)' }}>INR</span>
            </div>
            {company.last_date && (
              <div style={{ marginTop: '1.5rem', display: 'inline-flex', alignItems: 'center', gap: '0.4rem', color: 'var(--slate-400)', fontSize: '0.7rem', fontWeight: 700 }}>
                <span style={{ fontSize: '0.9rem' }}>⏱️</span> Last Sync: {company.last_date}
              </div>
            )}
          </div>

          <div className="skeuo-card">
            <span style={{ fontSize: '0.7rem', fontWeight: 900, color: 'var(--slate-400)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>NEURAL SIGNAL</span>
            <div style={{ marginTop: '0.5rem' }}>
              <div style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.75rem 1.5rem',
                background: 'var(--skeuo-bg)',
                boxShadow: 'var(--skeuo-inset-shadow)',
                borderRadius: '8px',
                fontSize: '1.75rem',
                fontWeight: 900,
                color: recColor
              }}>
                <span style={{ width: '14px', height: '14px', borderRadius: '50%', background: recColor, boxShadow: `0 0 10px ${recColor}` }}></span>
                {recommendation?.recommendation || 'NEUTRAL'}
              </div>
            </div>
            <p style={{ margin: '1rem 0 0 0', fontSize: '0.8rem', fontWeight: 700, color: 'var(--slate-500)' }}>Execution Protocol Threshold reached.</p>
          </div>

          <div className="skeuo-card">
            <span style={{ fontSize: '0.7rem', fontWeight: 900, color: 'var(--slate-400)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>ANALYSIS CONFIDENCE</span>
            <div style={{ marginTop: '0.5rem' }}>
              <span style={{ fontSize: '2.5rem', fontWeight: 900, color: 'var(--slate-800)', fontFamily: 'var(--font-mono)' }}>
                {recommendation?.confidence ? `${(recommendation.confidence * 100).toFixed(1)}%` : '---'}
              </span>
            </div>
            <div className="skeuo-progress-container" style={{ marginTop: '1rem', height: '12px' }}>
              <div className="skeuo-progress-bar" style={{ width: `${(recommendation?.confidence || 0) * 100}%`, background: 'var(--slate-800)' }}></div>
            </div>
          </div>
        </div>

        {/* Detailed Analysis Panel */}
        {recommendation ? (
          <div className="skeuo-card" style={{ marginBottom: '3rem' }}>
            <h3 style={{ margin: '0 0 2rem 0', fontSize: '1.25rem', fontWeight: 900, color: 'var(--slate-700)', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span style={{ fontSize: '1.5rem' }}>🧠</span> NEURAL MATRIX OUTPUT
            </h3>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem' }}>
              {[
                { label: 'Primary Vector', val: recommendation.recommendation || 'HOLD', color: 'var(--slate-800)' },
                { label: 'Quantum Weight', val: `${(recommendation.confidence * 100).toFixed(1)}%`, color: 'var(--slate-700)' },
                { label: 'Buy Momentum', val: `${((recommendation.buy_prob || 0) * 100).toFixed(1)}%`, color: 'var(--slate-600)' },
                { label: 'Sell Pressure', val: `${((recommendation.sell_prob || 0) * 100).toFixed(1)}%`, color: 'var(--black)' },
                { label: 'Temporal Ref', val: recommendation.last_date || 'N/A', color: 'var(--slate-500)' },
              ].map((item, i) => (
                <div key={i} className="skeuo-recessed" style={{ padding: '1.25rem' }}>
                  <span style={{ fontSize: '0.65rem', fontWeight: 900, color: 'var(--slate-400)', textTransform: 'uppercase', letterSpacing: '0.1em', display: 'block', marginBottom: '0.5rem' }}>{item.label}</span>
                  <span style={{ fontSize: '1.1rem', fontWeight: 900, color: item.color, fontFamily: 'var(--font-mono)' }}>{item.val}</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="skeuo-recessed" style={{ margin: '0 0 3rem 0', padding: '5rem', textAlign: 'center' }}>
            <span style={{ fontSize: '3rem', display: 'block', marginBottom: '1.5rem', opacity: 0.3 }}>🔎</span>
            <p style={{ fontWeight: 800, color: 'var(--slate-400)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Recommendation Matrix Offline for {company.symbol}</p>
          </div>
        )}

        {/* Tactical Actions */}
        {user && (
          <div className="skeuo-card" style={{ background: 'linear-gradient(135deg, white 0%, var(--skeuo-bg) 100%)', border: '2px solid var(--slate-300)' }}>
            <div className="flex justify-between items-center flex-wrap gap-6">
              <div>
                <h3 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 900, color: 'var(--slate-800)' }}>PORTFOLIO INTEGRATION</h3>
                <p style={{ margin: '0.5rem 0 0 0', color: 'var(--slate-500)', fontWeight: 600 }}>Execute this asset to your active terminal watchlist.</p>
              </div>
              <Link
                href={`/portfolio?add=${symbol}`}
                className="skeuo-button"
                style={{
                  padding: '1.25rem 2.5rem',
                  backgroundColor: 'var(--slate-800)',
                  color: 'white',
                  fontSize: '1rem',
                  fontWeight: 900,
                  textDecoration: 'none',
                  background: 'linear-gradient(180deg, var(--slate-800) 0%, var(--black) 100%)'
                }}
              >
                DEPLOY TO VAULT
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
