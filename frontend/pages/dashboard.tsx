'use client'
import React, { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'
import TrendChart from '../components/TrendChart'
import IntradayChart from '../components/IntradayChart'
import RiskPanel from '../components/RiskPanel'
import PageLoader from '../components/PageLoader'
import { useAuth } from '../lib/auth'
import { supabase } from '../lib/supabase'
import { getClientApiBase, buildApiUrl } from '../lib/api-base'

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
  const [allRecommendations, setAllRecommendations] = useState<Recommendation[]>([])
  const [totalAnalyzed, setTotalAnalyzed] = useState(0)
  const [trendLabels, setTrendLabels] = useState<string[]>([])
  const [trendData, setTrendData] = useState<number[]>([])
  const [intradayLabels, setIntradayLabels] = useState<string[]>([])
  const [intradayData, setIntradayData] = useState<number[]>([])
  const [risk, setRisk] = useState({ score: 0.12, factors: [] as any[] })
  const [lastRefreshedAt, setLastRefreshedAt] = useState<Date | null>(null)
  const [loading, setLoading] = useState(true)
  const apiUrl = getClientApiBase()

  useEffect(() => {
    if (authLoading) return
    if (!isAuthenticated) {
      router.push('/login')
      return
    }
    loadInitial(true)
  }, [authLoading, isAuthenticated])

  useEffect(() => {
    if (authLoading || !isAuthenticated) return

    const intervalId = setInterval(() => {
      loadInitial(false)
    }, 15000)

    return () => clearInterval(intervalId)
  }, [authLoading, isAuthenticated, user])

  async function loadInitial(showLoader = false) {
    try {
      if (showLoader) setLoading(true)

      const userPortfolioSymbols = new Set<string>()
      if (user) {
        const { data: portfolioData } = await supabase.from('portfolios').select('symbol').eq('user_id', user.id)
        if (portfolioData) {
          portfolioData.forEach((p: any) => userPortfolioSymbols.add(p.symbol))
        }
      }

      const recRes = await fetch('/api/recommendations')
      const allRecs: Recommendation[] = await recRes.json()
      setAllRecommendations(allRecs)
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
      const labels = marketPayload.trend?.labels || []
      const values = marketPayload.trend?.values || []
      const hasValidTrend = Array.isArray(labels) && Array.isArray(values) && labels.length > 1 && values.length > 1
      setTrendLabels(hasValidTrend ? labels : [])
      setTrendData(hasValidTrend ? values : [])
      setRisk({ score: marketPayload.riskScore ?? 0.12, factors: marketPayload.factors ?? [] })

      if (portfolioPayload.positions?.length) {
        const firstSymbol = portfolioPayload.positions[0].symbol
        const intradaySeries = portfolioPayload.intraday?.[firstSymbol]
        if (intradaySeries) {
          setIntradayLabels(intradaySeries.map((d: any) => d.t))
          setIntradayData(intradaySeries.map((d: any) => d.v))
        }
      }

      setLastRefreshedAt(new Date())
    } catch (err) {
      console.error('Failed to load dashboard data', err)
    } finally {
      if (showLoader) setLoading(false)
    }
  }

  const effectiveRecommendations = portfolioRecommendations.length > 0 ? portfolioRecommendations : allRecommendations

  const buyCount = effectiveRecommendations.filter((r) => r.recommendation === 'BUY').length
  const sellCount = effectiveRecommendations.filter((r) => r.recommendation === 'SELL').length
  const holdCount = effectiveRecommendations.filter((r) => r.recommendation === 'HOLD').length
  const avgConfidence = useMemo(() => {
    if (!effectiveRecommendations.length) return 0
    const total = effectiveRecommendations.reduce((sum, row) => sum + row.confidence, 0)
    return (total / effectiveRecommendations.length) * 100
  }, [effectiveRecommendations])

  if (authLoading) {
    return <PageLoader isLoading={true} message="Authenticating..." />
  }

  if (loading) {
    return <PageLoader isLoading={true} message="Loading dashboard..." />
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
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--status-buy)' }} />
              <span style={{ color: 'var(--text-secondary)', fontWeight: 700, fontSize: '0.8rem' }}>
                Auto-refresh every 15s{lastRefreshedAt ? ` • ${lastRefreshedAt.toLocaleTimeString()}` : ''}
              </span>
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
                <table className="w-full min-w-[700px] table-fixed">
                  <thead>
                    <tr style={tableHeadRowStyle}>
                      <th style={{ ...thLeftStyle, width: '24%' }}>Symbol</th>
                      <th style={{ ...thLeftStyle, width: '18%' }}>Signal</th>
                      <th style={{ ...thRightStyle, width: '20%' }}>Price</th>
                      <th style={{ ...thRightStyle, width: '20%' }}>Confidence</th>
                      <th style={{ ...thRightStyle, width: '18%' }}>Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {portfolioRecommendations.slice(0, 8).map((row) => (
                      <tr key={row.symbol} style={tableBodyRowStyle}>
                        <td style={{ ...tdLeftStyle, whiteSpace: 'nowrap' }}>{row.symbol.replace('.NS', '')}</td>
                        <td style={tdLeftStyle}>
                          <SignalBadge signal={row.recommendation} />
                        </td>
                        <td style={tdNumberStyle}>₹{Number(row.last_price || 0).toFixed(2)}</td>
                        <td style={tdNumberStyle}>{(row.confidence * 100).toFixed(1)}%</td>
                        <td style={{ ...tdRightStyle, whiteSpace: 'nowrap' }}>
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
                <table className="w-full min-w-[620px] table-fixed">
                  <thead>
                    <tr style={tableHeadRowStyle}>
                      <th style={{ ...thLeftStyle, width: '34%' }}>Symbol</th>
                      <th style={{ ...thRightStyle, width: '24%' }}>Price</th>
                      <th style={{ ...thRightStyle, width: '24%' }}>Buy Prob.</th>
                      <th style={{ ...thRightStyle, width: '18%' }}>Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {buyOpportunities.slice(0, 8).map((row) => (
                      <tr key={row.symbol} style={tableBodyRowStyle}>
                        <td style={{ ...tdLeftStyle, whiteSpace: 'nowrap' }}>{row.symbol.replace('.NS', '')}</td>
                        <td style={tdNumberStyle}>₹{Number(row.last_price || 0).toFixed(2)}</td>
                        <td style={tdNumberStyle}>{((row.buy_prob || row.confidence) * 100).toFixed(1)}%</td>
                        <td style={{ ...tdRightStyle, whiteSpace: 'nowrap' }}>
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

const tdNumberStyle: React.CSSProperties = {
  ...tdRightStyle,
  fontVariantNumeric: 'tabular-nums',
  whiteSpace: 'nowrap',
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
