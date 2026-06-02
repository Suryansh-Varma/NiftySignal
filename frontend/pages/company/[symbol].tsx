'use client'
import React, { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'
import axios from 'axios'
import { useAuth } from '../../lib/auth'
import { getCompanyName, isValidNiftySymbol } from '../../lib/supabase'

type CompanyRecommendation = {
  symbol: string
  recommendation: 'BUY' | 'SELL' | 'HOLD'
  confidence: number
  buy_prob?: number
  sell_prob?: number
  risk_score?: number
  last_price?: number
  last_date?: string
}

export default function CompanyDetail() {
  const router = useRouter()
  const { symbol } = router.query as { symbol?: string }
  const { user, loading: authLoading } = useAuth()

  const [company, setCompany] = useState<{ symbol: string; name: string } | null>(null)
  const [recommendation, setRecommendation] = useState<CompanyRecommendation | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const normalizeSymbol = (value: string) => {
    const upper = value.toUpperCase()
    return upper.endsWith('.NS') ? upper : `${upper}.NS`
  }

  const normalizeConfidence = (value: number | undefined) => {
    if (!value && value !== 0) return 0
    return value > 1 ? value / 100 : value
  }

  useEffect(() => {
    if (!symbol || authLoading) return

    const loadData = async () => {
      try {
        setLoading(true)
        setError('')

        const normalizedSymbol = normalizeSymbol(symbol)

        if (!isValidNiftySymbol(normalizedSymbol)) {
          setError('Invalid stock symbol. Use an NSE symbol like RELIANCE.NS.')
          return
        }

        const recRes = await axios.get(`/api/recommendations?symbol=${normalizedSymbol}`)
        const rec = (recRes.data?.[0] || null) as CompanyRecommendation | null
        setRecommendation(
          rec
            ? {
                ...rec,
                symbol: normalizeSymbol(rec.symbol || normalizedSymbol),
                confidence: normalizeConfidence(rec.confidence),
              }
            : null
        )

        setCompany({
          symbol: normalizedSymbol,
          name: getCompanyName(normalizedSymbol),
        })
      } catch (err) {
        console.error('Failed to load company data:', err)
        setError('Failed to load company data. Please try again.')
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [symbol, authLoading])

  const signalColor = useMemo(() => {
    if (recommendation?.recommendation === 'BUY') return 'var(--status-buy)'
    if (recommendation?.recommendation === 'SELL') return 'var(--status-sell)'
    return 'var(--text-secondary)'
  }, [recommendation])

  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center" style={{ gap: '0.9rem' }}>
        <div className="animate-spin" style={{ width: '2.75rem', height: '2.75rem', border: '4px solid var(--slate-200)', borderTopColor: 'var(--primary-500)', borderRadius: '50%' }} />
        <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>Loading stock details...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8" style={{ maxWidth: '1000px', paddingBottom: '2.5rem' }}>
          <div style={panelStyle}>
            <p style={{ ...messageStyle, color: '#fecaca', borderColor: 'rgba(239,68,68,0.35)', background: 'rgba(127,29,29,0.2)' }}>{error}</p>
            <Link href="/dashboard" style={secondaryActionStyle}>Back to dashboard</Link>
          </div>
        </div>
      </div>
    )
  }

  if (!company) {
    return (
      <div className="min-h-screen">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8" style={{ maxWidth: '1000px', paddingBottom: '2.5rem' }}>
          <div style={panelStyle}>
            <p style={{ margin: 0, color: 'var(--text-secondary)' }}>Company not found.</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen animate-in">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8" style={{ maxWidth: '1000px', paddingBottom: '2.5rem' }}>
        <section style={panelStyle}>
          <div className="flex items-start justify-between gap-3 flex-wrap">
            <div>
              <h1 style={titleStyle}>{company.name}</h1>
              <p style={subtitleStyle}>{company.symbol}</p>
            </div>
            <div className="flex gap-2">
              <Link href="/dashboard" style={secondaryActionStyle}>Dashboard</Link>
              <Link href="/portfolio" style={secondaryActionStyle}>Portfolio</Link>
            </div>
          </div>
        </section>

        <section className="grid grid-cols-1 md:grid-cols-3 gap-4" style={{ marginBottom: '1rem' }}>
          <StatCard label="Current Price" value={recommendation?.last_price ? `₹${recommendation.last_price.toFixed(2)}` : '-'} />
          <StatCard label="Signal" value={recommendation?.recommendation || 'N/A'} valueColor={signalColor} />
          <StatCard label="Confidence" value={recommendation?.confidence ? `${(recommendation.confidence * 100).toFixed(1)}%` : '-'} />
        </section>

        <section style={panelStyle}>
          <h2 style={panelTitleStyle}>Signal breakdown</h2>
          {recommendation ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3" style={{ marginTop: '0.9rem' }}>
              <StatCard label="Buy Probability" value={`${((recommendation.buy_prob || 0) * 100).toFixed(1)}%`} compact />
              <StatCard label="Sell Probability" value={`${((recommendation.sell_prob || 0) * 100).toFixed(1)}%`} compact />
              <StatCard label="Risk Score" value={recommendation.risk_score?.toFixed(2) || '-'} compact />
              <StatCard label="Last Updated" value={recommendation.last_date || '-'} compact />
            </div>
          ) : (
            <p style={{ marginTop: '0.9rem', color: 'var(--text-secondary)' }}>No recommendation data is available right now.</p>
          )}
        </section>

        {user && (
          <section style={panelStyle}>
            <div className="flex items-center justify-between gap-3 flex-wrap">
              <div>
                <h2 style={panelTitleStyle}>Add to portfolio</h2>
                <p style={{ marginTop: '0.35rem', color: 'var(--text-secondary)' }}>Send this stock to your portfolio add form with one click.</p>
              </div>
              <Link href={`/portfolio?add=${company.symbol}`} style={primaryActionLinkStyle}>
                Add {company.symbol.replace('.NS', '')}
              </Link>
            </div>
          </section>
        )}
      </div>
    </div>
  )
}

function StatCard({
  label,
  value,
  valueColor,
  compact,
}: {
  label: string
  value: string
  valueColor?: string
  compact?: boolean
}) {
  return (
    <div style={{ ...statCardStyle, padding: compact ? '0.8rem' : '1rem' }}>
      <p style={{ margin: 0, color: 'var(--text-muted)', fontWeight: 700, fontSize: '0.78rem' }}>{label}</p>
      <p style={{ margin: '0.32rem 0 0', color: valueColor || 'var(--text-primary)', fontWeight: 900, fontSize: compact ? '1.1rem' : '1.34rem' }}>{value}</p>
    </div>
  )
}

const panelStyle: React.CSSProperties = {
  border: '1px solid var(--border-glass)',
  borderRadius: '16px',
  background: 'rgba(12, 17, 26, 0.72)',
  padding: '1rem',
  marginBottom: '1rem',
}

const statCardStyle: React.CSSProperties = {
  border: '1px solid var(--border-glass)',
  borderRadius: '16px',
  background: 'rgba(12, 17, 26, 0.72)',
}

const titleStyle: React.CSSProperties = {
  margin: 0,
  color: 'var(--text-primary)',
  fontSize: '1.72rem',
  fontWeight: 900,
}

const subtitleStyle: React.CSSProperties = {
  marginTop: '0.36rem',
  color: 'var(--text-secondary)',
  fontFamily: 'var(--font-mono)',
  fontWeight: 700,
}

const panelTitleStyle: React.CSSProperties = {
  margin: 0,
  fontSize: '1.02rem',
  fontWeight: 800,
  color: 'var(--text-primary)',
}

const messageStyle: React.CSSProperties = {
  borderRadius: '10px',
  borderWidth: '1px',
  borderStyle: 'solid',
  padding: '0.68rem 0.8rem',
  fontWeight: 700,
  fontSize: '0.88rem',
  marginBottom: '0.8rem',
}

const secondaryActionStyle: React.CSSProperties = {
  textDecoration: 'none',
  borderRadius: '10px',
  border: '1px solid var(--border-glass)',
  background: 'rgba(15,23,42,0.6)',
  color: 'var(--text-primary)',
  padding: '0.52rem 0.75rem',
  cursor: 'pointer',
  fontWeight: 700,
  fontSize: '0.82rem',
}

const primaryActionLinkStyle: React.CSSProperties = {
  textDecoration: 'none',
  borderRadius: '10px',
  border: '1px solid rgba(0,255,204,0.35)',
  background: 'rgba(0,255,204,0.14)',
  color: 'var(--primary-glow)',
  padding: '0.52rem 0.8rem',
  fontWeight: 800,
  fontSize: '0.84rem',
}
