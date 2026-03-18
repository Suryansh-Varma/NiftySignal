'use client'
import React, { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/router'
import { useAuth } from '../lib/auth'
import { supabase } from '../lib/supabase'

type Stock = {
  symbol: string
  last_price: number
  shares: number
  actual_allocation: number
  buy_prob: number
  confidence: number
}

type Strategy = {
  risk_level: string
  num_stocks: number
  expected_monthly_return: number
  estimated_months: number
  target_date: string
  total_allocated: number
  cash_remaining: number
  stocks: Stock[]
}

type OptimizerResult = {
  capital: number
  target_return: number
  target_amount: number
  strategies: {
    conservative: Strategy
    moderate: Strategy
    aggressive: Strategy
  }
  recommended: 'conservative' | 'moderate' | 'aggressive'
  generated_at: string
}

type PortfolioPosition = {
  symbol: string
  quantity: number
  buy_price: number
}

export default function GoalOptimizer() {
  const router = useRouter()
  const { user, isAuthenticated, loading: authLoading } = useAuth()

  const [portfolioValue, setPortfolioValue] = useState(0)
  const [portfolioPositions, setPortfolioPositions] = useState<PortfolioPosition[]>([])
  const [targetReturn, setTargetReturn] = useState(40)
  const [result, setResult] = useState<OptimizerResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [portfolioLoading, setPortfolioLoading] = useState(true)
  const [selectedStrategy, setSelectedStrategy] = useState<'conservative' | 'moderate' | 'aggressive'>('moderate')
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [authLoading, isAuthenticated])

  useEffect(() => {
    if (!user) return
    loadPortfolioValue()
  }, [user])

  const loadPortfolioValue = async () => {
    try {
      setPortfolioLoading(true)

      const { data: positions, error } = await supabase.from('portfolios').select('*').eq('user_id', user?.id)
      if (error) {
        console.error('Error loading portfolio:', error)
        return
      }

      const normalized = (positions || []) as PortfolioPosition[]
      setPortfolioPositions(normalized)

      const recRes = await fetch(`${apiUrl}/api/recommendations`)
      const recommendations = await recRes.json()
      const priceMap: Record<string, number> = {}
      recommendations.forEach((rec: any) => {
        if (rec.symbol && rec.last_price) {
          priceMap[rec.symbol] = rec.last_price
        }
      })

      const totalValue = normalized.reduce((acc, position) => {
        const current = priceMap[position.symbol] || position.buy_price
        return acc + current * position.quantity
      }, 0)

      setPortfolioValue(Math.round(totalValue))
    } catch (err) {
      console.error('Failed to load portfolio:', err)
    } finally {
      setPortfolioLoading(false)
    }
  }

  const runOptimizer = async () => {
    if (portfolioValue <= 0) {
      window.alert('Your portfolio is empty. Add stocks first to run optimization.')
      return
    }

    setLoading(true)
    try {
      const res = await fetch(`${apiUrl}/api/portfolio_optimizer?capital=${portfolioValue}&target=${targetReturn}`)
      const data = await res.json()
      setResult(data)
      setSelectedStrategy(data.recommended)
    } catch (err) {
      console.error('Optimizer error:', err)
    } finally {
      setLoading(false)
    }
  }

  const targetAmount = useMemo(() => Math.round(portfolioValue * (1 + targetReturn / 100)), [portfolioValue, targetReturn])

  if (authLoading || portfolioLoading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center" style={{ gap: '0.9rem' }}>
        <div className="animate-spin" style={{ width: '2.75rem', height: '2.75rem', border: '4px solid var(--slate-200)', borderTopColor: 'var(--primary-500)', borderRadius: '50%' }} />
        <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>Loading goal optimizer...</span>
      </div>
    )
  }

  return (
    <div className="min-h-screen animate-in">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8" style={{ maxWidth: '1240px', paddingBottom: '2.5rem' }}>
        <section style={panelStyle}>
          <div className="flex items-start justify-between gap-3 flex-wrap">
            <div>
              <h1 style={titleStyle}>Goal Optimizer</h1>
              <p style={subtitleStyle}>Set your return target and generate an actionable strategy mix.</p>
            </div>
            <div className="flex gap-2">
              <Link href="/portfolio" style={secondaryActionStyle}>Portfolio</Link>
              <Link href="/goal-strategies" style={secondaryActionStyle}>Goal Strategies</Link>
            </div>
          </div>
        </section>

        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4" style={{ marginBottom: '1rem' }}>
          <StatCard label="Portfolio Value" value={`₹${portfolioValue.toLocaleString('en-IN')}`} />
          <StatCard label="Target Return" value={`${targetReturn}%`} valueColor="var(--primary-glow)" />
          <StatCard label="Target Amount" value={`₹${targetAmount.toLocaleString('en-IN')}`} />
        </section>

        <section style={panelStyle}>
          <h2 style={panelTitleStyle}>Optimization inputs</h2>
          {portfolioPositions.length === 0 ? (
            <div style={{ marginTop: '0.9rem' }}>
              <p style={{ margin: 0, color: 'var(--text-secondary)' }}>No positions found. Add stocks to your portfolio to run optimization.</p>
              <Link href="/portfolio" style={{ ...primaryActionStyle, display: 'inline-block', marginTop: '0.8rem', textDecoration: 'none' }}>
                Add positions
              </Link>
            </div>
          ) : (
            <>
              <div style={{ marginTop: '0.9rem' }}>
                <div className="flex items-center justify-between" style={{ marginBottom: '0.45rem' }}>
                  <label htmlFor="target-return" style={labelStyle}>Desired return</label>
                  <span style={{ color: 'var(--text-primary)', fontWeight: 800 }}>{targetReturn}%</span>
                </div>
                <input
                  id="target-return"
                  type="range"
                  min={10}
                  max={100}
                  step={5}
                  value={targetReturn}
                  onChange={(e) => setTargetReturn(Number(e.target.value))}
                  style={{ width: '100%' }}
                />
                <div className="flex justify-between" style={{ marginTop: '0.3rem', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                  <span>Low risk</span>
                  <span>Balanced</span>
                  <span>High growth</span>
                </div>
              </div>

              <div className="flex justify-end" style={{ marginTop: '0.9rem' }}>
                <button onClick={runOptimizer} disabled={loading} style={primaryActionStyle}>
                  {loading ? 'Running optimizer...' : 'Generate plan'}
                </button>
              </div>
            </>
          )}
        </section>

        {result && (
          <section style={panelStyle}>
            <div className="flex items-center justify-between gap-3 flex-wrap" style={{ marginBottom: '0.9rem' }}>
              <h2 style={panelTitleStyle}>Strategy options</h2>
              <span style={chipStyle}>Recommended: {result.recommended}</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3" style={{ marginBottom: '0.9rem' }}>
              {(['conservative', 'moderate', 'aggressive'] as const).map((key) => {
                const strategy = result.strategies[key]
                const isSelected = selectedStrategy === key
                const isRecommended = result.recommended === key

                return (
                  <button
                    key={key}
                    onClick={() => setSelectedStrategy(key)}
                    style={{
                      textAlign: 'left',
                      borderRadius: '12px',
                      border: isSelected ? '1px solid rgba(0,255,204,0.35)' : '1px solid var(--border-glass)',
                      background: isSelected ? 'rgba(0,255,204,0.1)' : 'rgba(15,23,42,0.6)',
                      color: 'var(--text-primary)',
                      padding: '0.8rem',
                      cursor: 'pointer',
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <strong style={{ textTransform: 'capitalize' }}>{key}</strong>
                      {isRecommended && <span style={smallChipStyle}>Best</span>}
                    </div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '0.84rem', marginTop: '0.35rem' }}>
                      {strategy.num_stocks} stocks • {strategy.expected_monthly_return.toFixed(1)}% / month
                    </div>
                    <div style={{ color: 'var(--text-muted)', fontSize: '0.78rem', marginTop: '0.22rem' }}>
                      ETA: {strategy.estimated_months} months
                    </div>
                  </button>
                )
              })}
            </div>

            <SelectedPlanTable strategy={result.strategies[selectedStrategy]} />

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3" style={{ marginTop: '0.9rem' }}>
              <StatCard label="Expected Monthly Return" value={`${result.strategies[selectedStrategy].expected_monthly_return.toFixed(1)}%`} compact />
              <StatCard label="Total Allocated" value={`₹${Math.round(result.strategies[selectedStrategy].total_allocated).toLocaleString('en-IN')}`} compact />
              <StatCard label="Cash Remaining" value={`₹${Math.round(result.strategies[selectedStrategy].cash_remaining).toLocaleString('en-IN')}`} compact />
            </div>
          </section>
        )}
      </div>
    </div>
  )
}

function SelectedPlanTable({ strategy }: { strategy: Strategy }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr style={tableHeadRowStyle}>
            <th style={thLeftStyle}>Stock</th>
            <th style={thRightStyle}>Price</th>
            <th style={thRightStyle}>Shares</th>
            <th style={thRightStyle}>Allocation</th>
            <th style={thRightStyle}>Buy Prob.</th>
          </tr>
        </thead>
        <tbody>
          {strategy.stocks.map((stock) => (
            <tr key={stock.symbol} style={tableBodyRowStyle}>
              <td style={tdLeftStyle}>{stock.symbol.replace('.NS', '')}</td>
              <td style={tdRightStyle}>₹{Number(stock.last_price || 0).toFixed(2)}</td>
              <td style={tdRightStyle}>{stock.shares}</td>
              <td style={tdRightStyle}>₹{Math.round(stock.actual_allocation || 0).toLocaleString('en-IN')}</td>
              <td style={tdRightStyle}>{((stock.buy_prob || 0) * 100).toFixed(1)}%</td>
            </tr>
          ))}
        </tbody>
      </table>
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
      <p style={{ margin: '0.32rem 0 0', color: valueColor || 'var(--text-primary)', fontWeight: 900, fontSize: compact ? '1.15rem' : '1.38rem' }}>{value}</p>
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
}

const panelTitleStyle: React.CSSProperties = {
  margin: 0,
  fontSize: '1.02rem',
  fontWeight: 800,
  color: 'var(--text-primary)',
}

const labelStyle: React.CSSProperties = {
  color: 'var(--text-muted)',
  fontSize: '0.8rem',
  fontWeight: 700,
}

const chipStyle: React.CSSProperties = {
  borderRadius: '999px',
  border: '1px solid var(--border-glass)',
  color: 'var(--text-muted)',
  fontWeight: 700,
  fontSize: '0.75rem',
  padding: '0.36rem 0.7rem',
}

const smallChipStyle: React.CSSProperties = {
  borderRadius: '999px',
  border: '1px solid rgba(0,255,204,0.35)',
  color: 'var(--primary-glow)',
  fontWeight: 700,
  fontSize: '0.68rem',
  padding: '0.18rem 0.5rem',
}

const primaryActionStyle: React.CSSProperties = {
  borderRadius: '10px',
  border: '1px solid rgba(0,255,204,0.35)',
  background: 'rgba(0,255,204,0.14)',
  color: 'var(--primary-glow)',
  padding: '0.52rem 0.8rem',
  cursor: 'pointer',
  fontWeight: 800,
  fontSize: '0.84rem',
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

const tableHeadRowStyle: React.CSSProperties = {
  borderBottom: '1px solid var(--border-glass)',
}

const tableBodyRowStyle: React.CSSProperties = {
  borderBottom: '1px solid rgba(255,255,255,0.06)',
}

const thLeftStyle: React.CSSProperties = {
  textAlign: 'left',
  padding: '0.65rem 0.2rem',
  color: 'var(--text-muted)',
  fontWeight: 700,
  fontSize: '0.75rem',
}

const thRightStyle: React.CSSProperties = {
  textAlign: 'right',
  padding: '0.65rem 0.2rem',
  color: 'var(--text-muted)',
  fontWeight: 700,
  fontSize: '0.75rem',
}

const tdLeftStyle: React.CSSProperties = {
  textAlign: 'left',
  padding: '0.62rem 0.2rem',
  color: 'var(--text-primary)',
  fontWeight: 700,
  fontSize: '0.86rem',
}

const tdRightStyle: React.CSSProperties = {
  textAlign: 'right',
  padding: '0.62rem 0.2rem',
  color: 'var(--text-secondary)',
  fontWeight: 700,
  fontSize: '0.84rem',
}
