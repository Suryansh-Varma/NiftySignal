'use client'
import React, { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'
import { io } from 'socket.io-client'
import TrendChart from '../components/TrendChart'
import IntradayChart from '../components/IntradayChart'
import RiskPanel from '../components/RiskPanel'
import { useAuth } from '../lib/auth'
import { supabase } from '../lib/supabase'

type Position = { symbol: string; name: string; qty: number; price: number; changePct: number }
type Recommendation = {
  symbol: string
  recommendation: 'BUY' | 'SELL' | 'HOLD'
  confidence: number
  last_price: number
  risk_score: number
  buy_prob?: number
  sell_prob?: number
  last_date?: string
}

export default function Dashboard() {
  const router = useRouter()
  const { user, loading: authLoading, isAuthenticated } = useAuth()
  const [positions, setPositions] = useState<Position[]>([])
  const [buyOpportunities, setBuyOpportunities] = useState<Recommendation[]>([])
  const [portfolioRecommendations, setPortfolioRecommendations] = useState<Recommendation[]>([])
  const [totalAnalyzed, setTotalAnalyzed] = useState(0)
  const [trendLabels, setTrendLabels] = useState<string[]>([])
  const [trendData, setTrendData] = useState<number[]>([])
  const [intradayLabels, setIntradayLabels] = useState<string[]>([])
  const [intradayData, setIntradayData] = useState<number[]>([])
  const [risk, setRisk] = useState({ score: 0.12, factors: [] as any[] })
  const [wsConnected, setWsConnected] = useState(false)
  const [loading, setLoading] = useState(true)
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    if (authLoading) return
    if (!isAuthenticated) {
      router.push('/login')
      return
    }
    loadInitial()
  }, [authLoading, isAuthenticated])

  async function loadInitial() {
    try {
      setLoading(true)

      const userPortfolioSymbols = new Set<string>()
      if (user) {
        const { data: portfolioData } = await supabase.from('portfolios').select('symbol').eq('user_id', user.id)
        if (portfolioData) {
          portfolioData.forEach((p: any) => userPortfolioSymbols.add(p.symbol))
        }
      }

      const recRes = await fetch(`${apiUrl}/api/recommendations`)
      const allRecs: Recommendation[] = await recRes.json()
      setTotalAnalyzed(allRecs.length)

      const inPortfolio: Recommendation[] = []
      const notInPortfolio: Recommendation[] = []
      allRecs.forEach((rec) => {
        if (userPortfolioSymbols.has(rec.symbol)) {
          inPortfolio.push(rec)
        } else {
          notInPortfolio.push(rec)
        }
      })

      setPortfolioRecommendations(inPortfolio)
      setBuyOpportunities(
        notInPortfolio
          .filter((r) => r.recommendation === 'BUY')
          .sort((a, b) => (b.buy_prob || b.confidence) - (a.buy_prob || a.confidence))
          .slice(0, 12)
      )

      const portfolioPayload = await fetch('/api/portfolio').then((r) => r.json()).catch(() => ({ positions: [] }))
      setPositions(portfolioPayload.positions || [])

      const marketPayload = await fetch('/api/market')
        .then((r) => r.json())
        .catch(() => ({ trend: { labels: [], values: [] }, riskScore: 0.12, factors: [] }))
      setTrendLabels(marketPayload.trend.labels || [])
      setTrendData(marketPayload.trend.values || [])
      setRisk({ score: marketPayload.riskScore ?? 0.12, factors: marketPayload.factors ?? [] })

      if (portfolioPayload.positions?.length) {
        const firstSymbol = portfolioPayload.positions[0].symbol
        const intradaySeries = portfolioPayload.intraday?.[firstSymbol]
        if (intradaySeries) {
          setIntradayLabels(intradaySeries.map((d: any) => d.t))
          setIntradayData(intradaySeries.map((d: any) => d.v))
        }
      }
    } catch (err) {
      console.error('Failed to load dashboard data', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const wsUrl =
      process.env.NEXT_PUBLIC_WS_URL ||
      (typeof window !== 'undefined' ? `http://${window.location.hostname}:4000` : 'http://localhost:4000')

    const socket = io(wsUrl, {
      auth: { token: 'demo-token' },
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: Infinity,
    })

    socket.on('connect', () => {
      setWsConnected(true)
      socket.emit('subscribe_portfolio')
      socket.emit('subscribe_risk')
      positions.forEach((position) => socket.emit('subscribe', position.symbol))
    })

    socket.on('portfolio_update', (data: any) => {
      if (data.positions) {
        setPositions(
          data.positions.map((p: any) => ({
            symbol: p.symbol,
            name: p.name || p.symbol,
            qty: p.qty,
            price: p.price,
            changePct: p.changePct,
          }))
        )
      }
    })

    socket.on('risk_update', (data: any) => {
      setRisk({ score: data.riskScore ?? 0.12, factors: data.factors ?? [] })
    })

    socket.on('intraday', (data: any) => {
      if (data.symbol === positions[0]?.symbol && data.point) {
        setIntradayLabels((prev) => [...prev.slice(-13), data.point.t])
        setIntradayData((prev) => [...prev.slice(-13), data.point.v])
      }
    })

    socket.on('disconnect', () => {
      setWsConnected(false)
    })

    return () => {
      socket.disconnect()
    }
  }, [positions])

  const buyCount = buyOpportunities.length
  const sellCount = portfolioRecommendations.filter((r) => r.recommendation === 'SELL').length
  const holdCount = portfolioRecommendations.filter((r) => r.recommendation === 'HOLD').length
  const avgConfidence = useMemo(() => {
    if (!portfolioRecommendations.length) return 0
    const total = portfolioRecommendations.reduce((sum, row) => sum + row.confidence, 0)
    return (total / portfolioRecommendations.length) * 100
  }, [portfolioRecommendations])

  if (authLoading || loading) {
    return (
      <div className="flex flex-col items-center justify-center" style={{ minHeight: '60vh', gap: '1.5rem' }}>
        <div className="animate-spin" style={{ width: '3rem', height: '3rem', border: '4px solid var(--slate-200)', borderTopColor: 'var(--primary-500)', borderRadius: '50%' }} />
        <p style={{ color: 'var(--slate-500)', fontWeight: 600 }}>Loading dashboard...</p>
      </div>
    )
  }

  return (
    <div className="animate-in" style={{ minHeight: '100vh' }}>
      <div className="container mx-auto px-4 sm:px-6 lg:px-8" style={{ maxWidth: '1240px', paddingBottom: '2.5rem' }}>
        <div
          style={{
            border: '1px solid var(--border-glass)',
            borderRadius: '18px',
            padding: '1.25rem',
            background: 'rgba(12, 17, 26, 0.72)',
            marginBottom: '1rem',
          }}
        >
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 900, color: 'var(--text-primary)' }}>Dashboard</h1>
              <p style={{ marginTop: '0.4rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
                Live overview of your portfolio signals and market opportunities.
              </p>
            </div>
            <div className="flex items-center gap-2" style={{ padding: '0.45rem 0.75rem', border: '1px solid var(--border-glass)', borderRadius: '999px' }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: wsConnected ? 'var(--status-buy)' : 'var(--status-sell)' }} />
              <span style={{ color: 'var(--text-secondary)', fontWeight: 700, fontSize: '0.8rem' }}>{wsConnected ? 'Live updates on' : 'Live updates off'}</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" style={{ marginBottom: '1rem' }}>
          {[
            { label: 'Buy Opportunities', value: buyCount, color: 'var(--status-buy)' },
            { label: 'Sell Alerts', value: sellCount, color: 'var(--status-sell)' },
            { label: 'Hold Signals', value: holdCount, color: 'var(--accent-blue)' },
            { label: 'Avg Confidence', value: `${avgConfidence.toFixed(1)}%`, color: 'var(--primary-glow)' },
          ].map((card) => (
            <div
              key={card.label}
              style={{
                border: '1px solid var(--border-glass)',
                borderRadius: '16px',
                background: 'rgba(12, 17, 26, 0.72)',
                padding: '1rem',
              }}
            >
              <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '0.8rem', fontWeight: 700 }}>{card.label}</p>
              <p style={{ margin: '0.35rem 0 0', color: card.color, fontSize: '1.5rem', fontWeight: 900 }}>{card.value}</p>
            </div>
          ))}
        </div>

        <div className="flex gap-3 flex-wrap" style={{ marginBottom: '1rem' }}>
          <Link href="/portfolio" style={actionLinkStyle}>
            Manage Portfolio
          </Link>
          <Link href="/goal-optimizer" style={actionLinkStyleSecondary}>
            Open Goal Optimizer
          </Link>
          <span style={{ ...chipStyle, color: 'var(--text-secondary)' }}>{totalAnalyzed} stocks analyzed</span>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4" style={{ marginBottom: '1rem' }}>
          <div style={panelStyle}>
            <div className="flex items-center justify-between" style={{ marginBottom: '0.9rem' }}>
              <h2 style={panelTitleStyle}>Signals for your portfolio</h2>
              <Link href="/portfolio" style={inlineLinkStyle}>
                View holdings
              </Link>
            </div>
            {portfolioRecommendations.length === 0 ? (
              <EmptyState text="No holdings found. Add stocks to get portfolio-specific signals." />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr style={tableHeadRowStyle}>
                      <th style={thLeftStyle}>Symbol</th>
                      <th style={thLeftStyle}>Signal</th>
                      <th style={thRightStyle}>Price</th>
                      <th style={thRightStyle}>Confidence</th>
                      <th style={thRightStyle}>Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {portfolioRecommendations.slice(0, 8).map((row) => (
                      <tr key={row.symbol} style={tableBodyRowStyle}>
                        <td style={tdLeftStyle}>{row.symbol.replace('.NS', '')}</td>
                        <td style={tdLeftStyle}>
                          <SignalBadge signal={row.recommendation} />
                        </td>
                        <td style={tdRightStyle}>₹{Number(row.last_price || 0).toFixed(2)}</td>
                        <td style={tdRightStyle}>{(row.confidence * 100).toFixed(0)}%</td>
                        <td style={tdRightStyle}>
                          <Link href={`/company/${row.symbol}`} style={inlineLinkStyle}>
                            Open
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div style={panelStyle}>
            <div className="flex items-center justify-between" style={{ marginBottom: '0.9rem' }}>
              <h2 style={panelTitleStyle}>Top buy opportunities</h2>
              <span style={chipStyle}>Not in portfolio</span>
            </div>
            {buyOpportunities.length === 0 ? (
              <EmptyState text="No high-confidence buy opportunities available right now." />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr style={tableHeadRowStyle}>
                      <th style={thLeftStyle}>Symbol</th>
                      <th style={thRightStyle}>Price</th>
                      <th style={thRightStyle}>Buy Prob.</th>
                      <th style={thRightStyle}>Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {buyOpportunities.slice(0, 8).map((row) => (
                      <tr key={row.symbol} style={tableBodyRowStyle}>
                        <td style={tdLeftStyle}>{row.symbol.replace('.NS', '')}</td>
                        <td style={tdRightStyle}>₹{Number(row.last_price || 0).toFixed(2)}</td>
                        <td style={tdRightStyle}>{((row.buy_prob || row.confidence) * 100).toFixed(0)}%</td>
                        <td style={tdRightStyle}>
                          <Link href={`/company/${row.symbol}`} style={inlineLinkStyle}>
                            Open
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
          <div style={{ ...panelStyle, gridColumn: 'span 2' }}>
            {trendLabels.length > 0 ? (
              <TrendChart labels={trendLabels} data={trendData} title="Market trend (30 days)" />
            ) : (
              <EmptyState text="Trend data is currently unavailable." />
            )}
            {positions.length > 0 && intradayData.length > 0 && (
              <div style={{ marginTop: '1rem', borderTop: '1px solid var(--border-glass)', paddingTop: '1rem' }}>
                <IntradayChart labels={intradayLabels} data={intradayData} />
              </div>
            )}
          </div>
          <div style={panelStyle}>
            <RiskPanel riskScore={risk.score} factors={risk.factors} />
          </div>
        </div>
      </div>
    </div>
  )
}

function SignalBadge({ signal }: { signal: Recommendation['recommendation'] }) {
  const color = signal === 'BUY' ? 'var(--status-buy)' : signal === 'SELL' ? 'var(--status-sell)' : 'var(--text-secondary)'
  const bg = signal === 'BUY' ? 'rgba(16, 185, 129, 0.12)' : signal === 'SELL' ? 'rgba(239, 68, 68, 0.12)' : 'rgba(148, 163, 184, 0.12)'

  return (
    <span
      style={{
        display: 'inline-flex',
        padding: '0.2rem 0.5rem',
        borderRadius: '999px',
        fontSize: '0.72rem',
        fontWeight: 800,
        color,
        background: bg,
        border: `1px solid ${color}33`,
      }}
    >
      {signal}
    </span>
  )
}

function EmptyState({ text }: { text: string }) {
  return <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.92rem' }}>{text}</p>
}

const panelStyle: React.CSSProperties = {
  border: '1px solid var(--border-glass)',
  borderRadius: '16px',
  background: 'rgba(12, 17, 26, 0.72)',
  padding: '1rem',
}

const panelTitleStyle: React.CSSProperties = {
  margin: 0,
  fontSize: '1.02rem',
  fontWeight: 800,
  color: 'var(--text-primary)',
}

const tableHeadRowStyle: React.CSSProperties = {
  borderBottom: '1px solid var(--border-glass)',
}

const tableBodyRowStyle: React.CSSProperties = {
  borderBottom: '1px solid rgba(255,255,255,0.06)',
}

const thLeftStyle: React.CSSProperties = {
  textAlign: 'left',
  padding: '0.6rem 0.2rem',
  color: 'var(--text-muted)',
  fontSize: '0.75rem',
  fontWeight: 700,
}

const thRightStyle: React.CSSProperties = {
  textAlign: 'right',
  padding: '0.6rem 0.2rem',
  color: 'var(--text-muted)',
  fontSize: '0.75rem',
  fontWeight: 700,
}

const tdLeftStyle: React.CSSProperties = {
  textAlign: 'left',
  padding: '0.62rem 0.2rem',
  color: 'var(--text-primary)',
  fontWeight: 700,
  fontSize: '0.88rem',
}

const tdRightStyle: React.CSSProperties = {
  textAlign: 'right',
  padding: '0.62rem 0.2rem',
  color: 'var(--text-secondary)',
  fontWeight: 700,
  fontSize: '0.84rem',
}

const actionLinkStyle: React.CSSProperties = {
  textDecoration: 'none',
  borderRadius: '10px',
  border: '1px solid rgba(0,255,204,0.35)',
  background: 'rgba(0,255,204,0.14)',
  color: 'var(--primary-glow)',
  padding: '0.55rem 0.85rem',
  fontWeight: 800,
  fontSize: '0.84rem',
}

const actionLinkStyleSecondary: React.CSSProperties = {
  textDecoration: 'none',
  borderRadius: '10px',
  border: '1px solid var(--border-glass)',
  background: 'rgba(15,23,42,0.6)',
  color: 'var(--text-primary)',
  padding: '0.55rem 0.85rem',
  fontWeight: 700,
  fontSize: '0.84rem',
}

const chipStyle: React.CSSProperties = {
  borderRadius: '999px',
  border: '1px solid var(--border-glass)',
  padding: '0.4rem 0.7rem',
  fontSize: '0.77rem',
  fontWeight: 700,
  color: 'var(--text-muted)',
}

const inlineLinkStyle: React.CSSProperties = {
  color: 'var(--primary-glow)',
  textDecoration: 'none',
  fontWeight: 700,
  fontSize: '0.8rem',
}
