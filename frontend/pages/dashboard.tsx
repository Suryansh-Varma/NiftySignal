'use client'
import React, { useEffect, useState } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'
import { io, Socket } from 'socket.io-client'
import StockList from '../components/StockList'
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
  const [portfolioSymbols, setPortfolioSymbols] = useState<Set<string>>(new Set())
  const [buyOpportunities, setBuyOpportunities] = useState<Recommendation[]>([])
  const [portfolioRecommendations, setPortfolioRecommendations] = useState<Recommendation[]>([])
  const [totalAnalyzed, setTotalAnalyzed] = useState(0)
  const [trendLabels, setTrendLabels] = useState<string[]>([])
  const [trendData, setTrendData] = useState<number[]>([])
  const [intradayLabels, setIntradayLabels] = useState<string[]>([])
  const [intradayData, setIntradayData] = useState<number[]>([])
  const [risk, setRisk] = useState({ score: 0.12, factors: [] as any[] })
  const [wsConnected, setWsConnected] = useState(false)
  const [socket, setSocket] = useState<Socket | null>(null)
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

      // First, fetch user's portfolio from Supabase
      let userPortfolioSymbols = new Set<string>()
      if (user) {
        const { data: portfolioData } = await supabase
          .from('portfolios')
          .select('symbol')
          .eq('user_id', user.id)

        if (portfolioData) {
          portfolioData.forEach((p: any) => userPortfolioSymbols.add(p.symbol))
        }
      }
      setPortfolioSymbols(userPortfolioSymbols)

      // Fetch ALL stock recommendations from backend API
      const recRes = await fetch(`${apiUrl}/api/recommendations`)
      const allRecs: Recommendation[] = await recRes.json()
      setTotalAnalyzed(allRecs.length)

      // Split recommendations based on portfolio ownership
      const inPortfolio: Recommendation[] = []
      const notInPortfolio: Recommendation[] = []

      allRecs.forEach((rec: Recommendation) => {
        if (userPortfolioSymbols.has(rec.symbol)) {
          inPortfolio.push(rec)
        } else {
          notInPortfolio.push(rec)
        }
      })

      // Portfolio Recommendations: HOLD/SELL for stocks you OWN (show all)
      setPortfolioRecommendations(inPortfolio)

      // Buy Opportunities: Top BUY signals for stocks NOT in portfolio
      const topBuyOpportunities = notInPortfolio
        .filter((r: Recommendation) => r.recommendation === 'BUY')
        .sort((a, b) => (b.buy_prob || b.confidence) - (a.buy_prob || a.confidence))
        .slice(0, 20)
      setBuyOpportunities(topBuyOpportunities)

      // Fetch portfolio positions for display
      const p = await fetch('/api/portfolio').then(r => r.json()).catch(() => ({ positions: [] }))
      setPositions(p.positions || [])

      const m = await fetch('/api/market').then(r => r.json()).catch(() => ({ trend: { labels: [], values: [] }, riskScore: 0.12, factors: [] }))
      setTrendLabels(m.trend.labels || [])
      setTrendData(m.trend.values || [])
      setRisk({ score: m.riskScore ?? 0.12, factors: m.factors ?? [] })

      if (p.positions && p.positions.length) {
        const s = p.positions[0].symbol
        const intr = p.intraday?.[s]
        if (intr) {
          setIntradayLabels(intr.map((d: any) => d.t))
          setIntradayData(intr.map((d: any) => d.v))
        }
      }
    } catch (err) {
      console.error('Failed to load initial data', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Connect to WebSocket server
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || (typeof window !== 'undefined' ? `${window.location.hostname}:4000` : 'http://localhost:4000')
    const newSocket = io(wsUrl, {
      auth: { token: 'demo-token' },
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: Infinity,
    })

    newSocket.on('connect', () => {
      console.log('[Dashboard] WebSocket connected')
      setWsConnected(true)
      // Subscribe to live updates
      newSocket.emit('subscribe_portfolio')
      newSocket.emit('subscribe_risk')
      positions.forEach(p => newSocket.emit('subscribe', p.symbol))
    })

    // Listen for portfolio updates
    newSocket.on('portfolio_update', (data: any) => {
      if (data.positions) {
        setPositions(data.positions.map((p: any) => ({
          symbol: p.symbol,
          name: p.name || p.symbol,
          qty: p.qty,
          price: p.price,
          changePct: p.changePct,
        })))
      }
    })

    // Listen for risk updates
    newSocket.on('risk_update', (data: any) => {
      setRisk({ score: data.riskScore ?? 0.12, factors: data.factors ?? [] })
    })

    // Listen for intraday updates
    newSocket.on('intraday', (data: any) => {
      if (data.symbol === positions[0]?.symbol && data.point) {
        setIntradayLabels(prev => [...prev.slice(-13), data.point.t])
        setIntradayData(prev => [...prev.slice(-13), data.point.v])
      }
    })

    newSocket.on('disconnect', () => {
      console.log('[Dashboard] WebSocket disconnected')
      setWsConnected(false)
    })

    setSocket(newSocket)

    return () => {
      newSocket.disconnect()
    }
  }, [positions])

  // Calculate stats
  const buyCount = buyOpportunities.length
  const portfolioSellCount = portfolioRecommendations.filter(r => r.recommendation === 'SELL').length
  const portfolioHoldCount = portfolioRecommendations.filter(r => r.recommendation === 'HOLD').length
  const portfolioBuyMore = portfolioRecommendations.filter(r => r.recommendation === 'BUY').length

  if (authLoading || loading) {
    return (
      <div className="flex flex-col items-center justify-center" style={{ minHeight: '60vh', gap: '1.5rem' }}>
        <div className="animate-spin" style={{ width: '3rem', height: '3rem', border: '4px solid var(--slate-200)', borderTopColor: 'var(--primary-500)', borderRadius: '50%' }} />
        <p style={{ color: 'var(--slate-500)', fontWeight: 600 }}>Syncing terminal with market flux...</p>
      </div>
    )
  }

  return (
    <div className="animate-in" style={{ backgroundColor: 'var(--skeuo-bg)', minHeight: '100vh' }}>
      <div className="container" style={{ paddingTop: '2rem', paddingBottom: '4rem' }}>
        {/* Header */}
        <div className="flex justify-between items-center" style={{ marginBottom: '2.5rem', flexWrap: 'wrap', gap: '1.5rem' }}>
          <div>
            <h1 className="flex items-center gap-4" style={{ margin: 0, fontSize: '2.5rem', color: 'var(--slate-800)', textShadow: '1px 1px 0px white' }}>
              <span style={{
                width: '48px',
                height: '48px',
                background: 'var(--skeuo-bg)',
                boxShadow: 'var(--skeuo-outset-shadow)',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>📊</span>
              Strategic Dashboard
            </h1>
            <p style={{ color: 'var(--slate-500)', fontSize: '1.1rem', marginTop: '0.5rem', fontWeight: 600 }}>Real-time market intelligence & institutional signals</p>
          </div>
          <div className="skeuo-recessed" style={{ padding: '0.75rem 1.5rem', borderRadius: 'var(--radius-full)', display: 'flex', alignItems: 'center', gap: '0.75rem', fontWeight: 800, fontSize: '0.8rem', letterSpacing: '0.05em' }}>
            <div className={wsConnected ? 'animate-pulse' : ''} style={{
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              backgroundColor: wsConnected ? 'var(--slate-800)' : 'var(--slate-400)',
              boxShadow: wsConnected ? `0 0 10px var(--slate-400), inset -2px -2px 4px rgba(0,0,0,0.2)` : 'inset 1px 1px 2px rgba(0,0,0,0.3)'
            }} />
            <span style={{ color: wsConnected ? 'var(--slate-700)' : 'var(--slate-500)' }}>{wsConnected ? 'TERMINAL LIVE' : 'OFFLINE'}</span>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid-terminal" style={{ marginBottom: '2.5rem' }}>
          {[
            { label: 'Entry Signals', val: buyCount, icon: '📈', color: 'var(--slate-700)' },
            { label: 'Exit Signals', val: portfolioSellCount, icon: '📉', color: 'var(--black)' },
            { label: 'Hold Positions', val: portfolioHoldCount, icon: '⏸️', color: 'var(--slate-400)' },
            { label: 'Quantum Analysis', val: totalAnalyzed, icon: '🎯', color: 'var(--primary-600)' }
          ].map((stat, i) => (
            <div key={i} className="skeuo-card flex items-center gap-6" style={{ padding: '1.5rem', borderLeft: `4px solid ${stat.color}` }}>
              <div style={{
                fontSize: '2rem',
                width: '56px',
                height: '56px',
                background: 'var(--skeuo-bg)',
                boxShadow: 'var(--skeuo-inset-shadow)',
                borderRadius: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>{stat.icon}</div>
              <div>
                <span style={{
                  fontSize: '0.75rem',
                  fontWeight: 800,
                  textTransform: 'uppercase',
                  color: 'var(--slate-500)',
                  display: 'block',
                  marginBottom: '0.25rem'
                }}>{stat.label}</span>
                <span style={{ fontSize: '2rem', fontWeight: 900, color: 'var(--slate-800)', textShadow: '1px 1px 0 white' }}>{stat.val}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="flex gap-6" style={{ marginBottom: '3rem', flexWrap: 'wrap' }}>
          <Link href="/goal-optimizer" className="skeuo-button" style={{ flex: 1, minWidth: '240px', justifyContent: 'center', padding: '1.25rem', background: 'linear-gradient(135deg, var(--slate-800), var(--black))', color: 'white' }}>
            <span style={{ fontSize: '1.5rem' }}>🎯</span>
            <span style={{ fontSize: '1.1rem' }}>Goal Optimizer</span>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" style={{ marginLeft: 'auto' }}>
              <path d="M9 18l6-6-6-6" />
            </svg>
          </Link>
          <Link href="/portfolio" className="skeuo-button" style={{ flex: 1, minWidth: '240px', justifyContent: 'center', padding: '1.25rem', color: 'var(--slate-700)' }}>
            <span style={{ fontSize: '1.5rem' }}>💼</span>
            <span style={{ fontSize: '1.1rem' }}>My Portfolio</span>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" style={{ marginLeft: 'auto' }}>
              <path d="M9 18l6-6-6-6" />
            </svg>
          </Link>
        </div>

        {/* Your Portfolio Recommendations Section */}
        <div className="skeuo-card animate-in" style={{ marginBottom: '3rem' }}>
          <div className="flex justify-between items-center" style={{ marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
            <h2 className="flex items-center gap-3" style={{ margin: 0, fontSize: '1.25rem', color: 'var(--slate-700)' }}>
              <span className="skeuo-knob" style={{ width: '32px', height: '32px' }}></span>
              Portfolio IQ
            </h2>
            <div className="skeuo-recessed" style={{ padding: '0.4rem 1rem', fontSize: '0.75rem', fontWeight: 800, color: 'var(--slate-600)', borderRadius: 'var(--radius-full)' }}>
              ACTIVE SURVEILLANCE
            </div>
          </div>

          {portfolioRecommendations.length === 0 ? (
            <div className="skeuo-recessed" style={{ textAlign: 'center', padding: '5rem', color: 'var(--slate-400)' }}>
              <span style={{ fontSize: '4rem', display: 'block', marginBottom: '1.5rem', opacity: 0.3 }}>💼</span>
              <p style={{ fontWeight: 600 }}>Your portfolio registry is currently empty.</p>
              <Link href="/portfolio" className="skeuo-button" style={{ marginTop: '2rem' }}>+ INITIALIZE ASSETS</Link>
            </div>
          ) : (
            <div className="skeuo-recessed" style={{ padding: 0, overflow: 'hidden' }}>
              <table className="premium-table" style={{ background: 'transparent' }}>
                <thead>
                  <tr style={{ background: 'rgba(0,0,0,0.02)' }}>
                    <th style={{ padding: '1.25rem 1.5rem', color: 'var(--slate-500)', fontSize: '0.7rem' }}>Security</th>
                    <th style={{ padding: '1.25rem 1.5rem', color: 'var(--slate-500)', fontSize: '0.7rem' }}>Signal</th>
                    <th style={{ padding: '1.25rem 1.5rem', color: 'var(--slate-500)', fontSize: '0.7rem', textAlign: 'right' }}>Price</th>
                    <th style={{ padding: '1.25rem 1.5rem', color: 'var(--slate-500)', fontSize: '0.7rem', textAlign: 'right' }}>Strategy</th>
                    <th style={{ padding: '1.25rem 1.5rem', color: 'var(--slate-500)', fontSize: '0.7rem', textAlign: 'center' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {portfolioRecommendations.map((rec, idx) => {
                    const isBuy = rec.recommendation === 'BUY'
                    const isSell = rec.recommendation === 'SELL'
                    const color = isBuy ? 'var(--slate-800)' : isSell ? 'var(--black)' : 'var(--slate-400)'
                    const label = isBuy ? 'ACCUMULATE' : rec.recommendation

                    return (
                      <tr key={idx} className="animate-in" style={{ animationDelay: `${idx * 0.05}s`, borderBottom: idx === portfolioRecommendations.length - 1 ? 'none' : '1px solid rgba(0,0,0,0.03)' }}>
                        <td style={{ padding: '1.5rem' }}>
                          <span style={{ fontWeight: 900, fontFamily: 'var(--font-mono)', fontSize: '1.1rem', color: 'var(--slate-800)' }}>{rec.symbol.replace('.NS', '')}</span>
                        </td>
                        <td style={{ padding: '1.5rem' }}>
                          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.4rem 0.8rem', borderRadius: '4px', background: 'var(--skeuo-bg)', boxShadow: 'var(--skeuo-inset-shadow)', fontSize: '0.75rem', fontWeight: 800, color: color }}>
                            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: color, boxShadow: `0 0 6px ${color}` }}></span>
                            {label}
                          </div>
                        </td>
                        <td style={{ padding: '1.5rem', textAlign: 'right', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--slate-700)' }}>
                          ₹{rec.last_price?.toFixed(2) || 'N/A'}
                        </td>
                        <td style={{ padding: '1.5rem', textAlign: 'right' }}>
                          <div className="flex items-center justify-end gap-4">
                            <div className="skeuo-progress-container" style={{ width: '80px', height: '10px' }}>
                              <div className="skeuo-progress-bar" style={{ width: `${rec.confidence * 100}%`, background: color }} />
                            </div>
                            <span style={{ fontSize: '0.85rem', fontWeight: 900, color: 'var(--slate-500)', minWidth: '40px', fontFamily: 'var(--font-mono)' }}>{(rec.confidence * 100).toFixed(0)}%</span>
                          </div>
                        </td>
                        <td style={{ padding: '1.5rem', textAlign: 'center' }}>
                          <Link href={`/company/${rec.symbol}`} className="skeuo-button" style={{ padding: '0.5rem 1rem', fontSize: '0.75rem', minWidth: '100px' }}>
                            ANALYZE
                          </Link>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Buy Opportunities Section */}
        <div className="skeuo-card animate-in" style={{ marginBottom: '3rem', animationDelay: '0.1s' }}>
          <div className="flex justify-between items-center" style={{ marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
            <h2 className="flex items-center gap-3" style={{ margin: 0, fontSize: '1.25rem', color: 'var(--slate-700)' }}>
              <span className="skeuo-knob" style={{ width: '32px', height: '32px' }}></span>
              Market Alpha
            </h2>
            <div className="skeuo-recessed" style={{ padding: '0.4rem 1rem', fontSize: '0.75rem', fontWeight: 800, color: 'var(--slate-600)', borderRadius: 'var(--radius-full)' }}>
              TOP PROBABILITIES
            </div>
          </div>

          {buyOpportunities.length === 0 ? (
            <div className="skeuo-recessed" style={{ textAlign: 'center', padding: '5rem', color: 'var(--slate-400)' }}>
              <span style={{ fontSize: '4rem', display: 'block', marginBottom: '1.5rem', opacity: 0.3 }}>🔎</span>
              <p style={{ fontWeight: 600 }}>No high-confidence buy signals detected.</p>
            </div>
          ) : (
            <div className="skeuo-recessed" style={{ padding: 0, overflow: 'hidden' }}>
              <table className="premium-table" style={{ background: 'transparent' }}>
                <thead>
                  <tr style={{ background: 'rgba(0,0,0,0.02)' }}>
                    <th style={{ padding: '1.25rem 1.5rem', color: 'var(--slate-500)', fontSize: '0.7rem' }}>Rank</th>
                    <th style={{ padding: '1.25rem 1.5rem', color: 'var(--slate-500)', fontSize: '0.7rem' }}>Ticker</th>
                    <th style={{ padding: '1.25rem 1.5rem', color: 'var(--slate-500)', fontSize: '0.7rem' }}>Intelligence</th>
                    <th style={{ padding: '1.25rem 1.5rem', color: 'var(--slate-500)', fontSize: '0.7rem', textAlign: 'right' }}>Price</th>
                    <th style={{ padding: '1.25rem 1.5rem', color: 'var(--slate-500)', fontSize: '0.7rem', textAlign: 'right' }}>Edge</th>
                    <th style={{ padding: '1.25rem 1.5rem', color: 'var(--slate-500)', fontSize: '0.7rem', textAlign: 'center' }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {buyOpportunities.map((rec, idx) => (
                    <tr key={idx} className="animate-in" style={{ animationDelay: `${idx * 0.05}s`, borderBottom: idx === buyOpportunities.length - 1 ? 'none' : '1px solid rgba(0,0,0,0.03)' }}>
                      <td style={{ padding: '1.5rem', color: 'var(--slate-400)', fontWeight: 900, fontFamily: 'var(--font-mono)' }}>{String(idx + 1).padStart(2, '0')}</td>
                      <td style={{ padding: '1.5rem' }}>
                        <span style={{ fontWeight: 900, fontFamily: 'var(--font-mono)', fontSize: '1.1rem', color: 'var(--slate-800)' }}>{rec.symbol.replace('.NS', '')}</span>
                      </td>
                      <td style={{ padding: '1.5rem' }}>
                        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', padding: '0.4rem 0.8rem', borderRadius: '4px', background: 'var(--skeuo-bg)', boxShadow: 'var(--skeuo-inset-shadow)', fontSize: '0.75rem', fontWeight: 800, color: 'var(--slate-700)' }}>
                          <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--slate-600)', boxShadow: `0 0 6px var(--slate-500)` }}></span>
                          ACCUMULATE
                        </div>
                      </td>
                      <td style={{ padding: '1.5rem', textAlign: 'right', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--slate-700)' }}>
                        ₹{rec.last_price?.toFixed(2) || 'N/A'}
                      </td>
                      <td style={{ padding: '1.5rem', textAlign: 'right' }}>
                        <div className="flex items-center justify-end gap-4">
                          <span style={{ color: 'var(--black)', fontWeight: 900, fontSize: '0.95rem', fontFamily: 'var(--font-mono)' }}>{((rec.buy_prob || 0) * 100).toFixed(0)}%</span>
                          <div className="skeuo-progress-container" style={{ width: '80px', height: '10px' }}>
                            <div className="skeuo-progress-bar" style={{ width: `${rec.confidence * 100}%`, background: 'var(--slate-800)' }} />
                          </div>
                        </div>
                      </td>
                      <td style={{ padding: '1.5rem', textAlign: 'center' }}>
                        <Link href={`/portfolio?add=${rec.symbol.replace('.NS', '')}`} className="skeuo-button" style={{ padding: '0.5rem 1rem', fontSize: '0.75rem', background: 'var(--slate-800)', color: 'white', minWidth: '100px' }}>
                          + DEPLOY
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Charts & Side Panels */}
        <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '2.5rem' }}>
          <div className="skeuo-card flex flex-col gap-8">
            <StockList positions={positions} />
            {positions.length > 0 && intradayData.length > 0 && (
              <div className="skeuo-recessed" style={{ marginTop: '1rem' }}>
                <h3 className="flex items-center gap-3" style={{ fontSize: '1.1rem', marginBottom: '1.5rem', color: 'var(--slate-700)' }}>
                  <span className="skeuo-knob" style={{ width: '24px', height: '24px' }}></span>
                  Intraday Dynamics
                </h3>
                <IntradayChart labels={intradayLabels} data={intradayData} />
              </div>
            )}
          </div>

          <div className="flex flex-col gap-8">
            <div className="skeuo-card" style={{ padding: '1.5rem' }}>
              {trendLabels.length > 0 ? (
                <div className="skeuo-recessed" style={{ padding: '0.5rem' }}>
                  <TrendChart labels={trendLabels} data={trendData} title="30-Day Velocity" />
                </div>
              ) : (
                <div className="skeuo-recessed" style={{ textAlign: 'center', padding: '3rem', color: 'var(--slate-400)' }}>
                  <span style={{ fontSize: '3rem', opacity: 0.3, display: 'block', marginBottom: '1rem' }}>📉</span>
                  <p style={{ fontWeight: 600 }}>Velocity data offline</p>
                </div>
              )}
            </div>
            <RiskPanel riskScore={risk.score} factors={risk.factors} />
          </div>
        </div>
      </div>
    </div>
  )
}
