'use client'
import React, { useState, useEffect } from 'react'
import { useAuth } from '../lib/auth'
import { useRouter } from 'next/router'
import Link from 'next/link'
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
  recommended: string
  generated_at: string
}

type PortfolioPosition = {
  symbol: string
  quantity: number
  buy_price: number
  company_name?: string
}

export default function GoalOptimizer() {
  const router = useRouter()
  const { user, isAuthenticated, loading: authLoading } = useAuth()
  const [portfolioValue, setPortfolioValue] = useState(0)
  const [portfolioPositions, setPortfolioPositions] = useState<PortfolioPosition[]>([])
  const [currentPrices, setCurrentPrices] = useState<Record<string, number>>({})
  const [targetReturn, setTargetReturn] = useState(40)
  const [result, setResult] = useState<OptimizerResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [portfolioLoading, setPortfolioLoading] = useState(true)
  const [selectedStrategy, setSelectedStrategy] = useState<string>('moderate')
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [authLoading, isAuthenticated])

  // Load portfolio from Supabase and calculate value
  useEffect(() => {
    if (!user) return
    loadPortfolioValue()
  }, [user])

  const loadPortfolioValue = async () => {
    try {
      setPortfolioLoading(true)

      // Fetch portfolio from Supabase
      const { data: positions, error } = await supabase
        .from('portfolios')
        .select('*')
        .eq('user_id', user?.id)

      if (error) {
        console.error('Error loading portfolio:', error)
        return
      }

      setPortfolioPositions(positions || [])

      // Fetch current prices from recommendations API
      const recRes = await fetch(`${apiUrl}/api/recommendations`)
      const recommendations = await recRes.json()

      const priceMap: Record<string, number> = {}
      recommendations.forEach((rec: any) => {
        if (rec.symbol && rec.last_price) {
          priceMap[rec.symbol] = rec.last_price
        }
      })
      setCurrentPrices(priceMap)

      // Calculate total portfolio value
      let totalValue = 0
      if (positions && positions.length > 0) {
        positions.forEach((pos: PortfolioPosition) => {
          const currentPrice = priceMap[pos.symbol] || pos.buy_price
          totalValue += currentPrice * pos.quantity
        })
      }

      setPortfolioValue(Math.round(totalValue))
    } catch (err) {
      console.error('Failed to load portfolio:', err)
    } finally {
      setPortfolioLoading(false)
    }
  }

  const runOptimizer = async () => {
    if (portfolioValue <= 0) {
      alert('Your portfolio is empty. Add stocks to your portfolio first!')
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

  if (authLoading || portfolioLoading) {
    return (
      <div className="container" style={{ maxWidth: 1000, padding: '32px 16px' }}>
        <style jsx global>{`
          @keyframes shimmer {
            0% { background-position: -200% 0; }
            100% { background-position: 200% 0; }
          }
          .skeleton {
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
            border-radius: 8px;
          }
        `}</style>
        <div className="skeleton" style={{ height: 40, width: 300, marginBottom: 16 }} />
        <div className="skeleton" style={{ height: 20, width: 400, marginBottom: 32 }} />
        <div className="skeleton" style={{ height: 300, marginBottom: 24 }} />
      </div>
    )
  }

  const strategyColors: Record<string, { bg: string; border: string; text: string; gradient: string }> = {
    conservative: { bg: 'var(--slate-50)', border: 'var(--slate-200)', text: 'var(--slate-600)', gradient: 'linear-gradient(135deg, var(--slate-100) 0%, var(--slate-50) 100%)' },
    moderate: { bg: 'var(--slate-100)', border: 'var(--slate-300)', text: 'var(--slate-800)', gradient: 'linear-gradient(135deg, var(--slate-200) 0%, var(--slate-100) 100%)' },
    aggressive: { bg: 'var(--slate-200)', border: 'var(--slate-400)', text: 'var(--black)', gradient: 'linear-gradient(135deg, var(--slate-300) 0%, var(--slate-200) 100%)' }
  }

  const strategyIcons: Record<string, string> = {
    conservative: '🛡️',
    moderate: '⚖️',
    aggressive: '🚀'
  }

  return (
    <div className="animate-in" style={{ backgroundColor: 'var(--skeuo-bg)', minHeight: '100vh', padding: '2rem 1rem' }}>
      <div className="container" style={{ maxWidth: 1000 }}>
        {/* Header */}
        <div className="flex flex-col gap-2" style={{ marginBottom: '3rem' }}>
          <h1 style={{
            margin: 0,
            fontSize: '2.5rem',
            fontWeight: 900,
            color: 'var(--slate-800)',
            textShadow: '1px 1px 0px white',
            display: 'flex',
            alignItems: 'center',
            gap: '1rem'
          }}>
            <span className="skeuo-knob" style={{ width: '48px', height: '48px' }}></span>
            Goal Optimizer
          </h1>
          <p style={{ color: 'var(--slate-500)', fontSize: '1.2rem', fontWeight: 600 }}>
            Precision capital allocation for strategic wealth building
          </p>
        </div>

        {/* Current Portfolio Summary */}
        <div className="skeuo-card" style={{ marginBottom: '3rem' }}>
          <div className="flex justify-between items-center" style={{ marginBottom: '2rem' }}>
            <h2 className="flex items-center gap-3" style={{ margin: 0, fontSize: '1.25rem', color: 'var(--slate-700)' }}>
              <span style={{ fontSize: '1.5rem' }}>📊</span> Segment Analysis
            </h2>
            <div className="skeuo-recessed" style={{ padding: '0.4rem 1rem', fontSize: '0.75rem', fontWeight: 800, color: 'var(--slate-600)', borderRadius: 'var(--radius-full)' }}>
              {portfolioPositions.length} ACTIVE HOLDINGS
            </div>
          </div>

          {portfolioPositions.length === 0 ? (
            <div className="skeuo-recessed" style={{ textAlign: 'center', padding: '5rem', color: 'var(--slate-400)' }}>
              <span style={{ fontSize: '4rem', display: 'block', marginBottom: '1.5rem', opacity: 0.3 }}>💼</span>
              <p style={{ fontWeight: 700, margin: 0 }}>Register your base capital in the Portfolio Terminal first.</p>
              <Link href="/portfolio" className="skeuo-button" style={{ marginTop: '2.5rem' }}>→ INITIALIZE PORTFOLIO</Link>
            </div>
          ) : (
            <>
              {/* Stats Highlights */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '2rem', marginBottom: '3rem' }}>
                <div className="skeuo-recessed">
                  <span style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--slate-500)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Working Capital</span>
                  <div style={{ fontSize: '2.25rem', fontWeight: 900, color: 'var(--slate-800)', marginTop: '0.25rem' }}>₹{portfolioValue.toLocaleString()}</div>
                </div>
                <div className="skeuo-recessed" style={{ borderLeft: '4px solid var(--slate-400)' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 800, color: 'var(--slate-500)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Target Projection</span>
                  <div style={{ fontSize: '2.25rem', fontWeight: 900, color: 'var(--slate-800)', marginTop: '0.25rem' }}>₹{Math.round(portfolioValue * (1 + targetReturn / 100)).toLocaleString()}</div>
                </div>
              </div>

              {/* Input Control Panel */}
              <div className="skeuo-recessed" style={{ marginBottom: '3rem' }}>
                <label style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                  <span style={{ fontWeight: 800, color: 'var(--slate-700)', fontSize: '1rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Desired Velocity (Return)</span>
                  <span style={{
                    fontSize: '2rem',
                    fontWeight: 900,
                    color: 'var(--slate-800)',
                    padding: '0.25rem 1rem',
                    background: 'var(--skeuo-bg)',
                    boxShadow: 'var(--skeuo-inset-shadow)',
                    borderRadius: '8px',
                    fontFamily: 'var(--font-mono)'
                  }}>{targetReturn}%</span>
                </label>

                <div style={{ padding: '1rem 0', position: 'relative' }}>
                  <input
                    type="range"
                    min="10"
                    max="100"
                    step="5"
                    value={targetReturn}
                    onChange={(e) => setTargetReturn(Number(e.target.value))}
                    style={{
                      width: '100%',
                      height: '12px',
                      appearance: 'none',
                      background: 'var(--skeuo-bg)',
                      boxShadow: 'var(--skeuo-inset-shadow)',
                      borderRadius: '6px',
                      outline: 'none',
                      cursor: 'pointer'
                    }}
                  />
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', fontWeight: 800, marginTop: '1rem', color: 'var(--slate-400)', textTransform: 'uppercase' }}>
                  <span>🛡️ Low Risk</span>
                  <span>⚖️ Balanced</span>
                  <span>🚀 Hyper Growth</span>
                </div>
              </div>

              <button
                onClick={runOptimizer}
                disabled={loading}
                className="skeuo-button"
                style={{
                  width: '100%',
                  padding: '1.5rem',
                  fontSize: '1.25rem',
                  fontWeight: 900,
                  color: 'white',
                  background: 'linear-gradient(180deg, var(--slate-800) 0%, var(--black) 100%)',
                  justifyContent: 'center',
                  gap: '1rem',
                  textTransform: 'uppercase',
                  letterSpacing: '0.1em'
                }}
              >
                {loading ? 'Processing Neural Matrices...' : `Generate ${targetReturn}% Strategic Path`}
              </button>
            </>
          )}
        </div>

        {/* Results */}
        {result && (
          <div className="animate-in" style={{ marginTop: '4rem' }}>
            <h2 className="flex items-center gap-3" style={{ fontSize: '1.5rem', fontWeight: 900, color: 'var(--slate-800)', marginBottom: '2rem' }}>
              <span className="skeuo-knob" style={{ width: '24px', height: '24px' }}></span>
              Strategic Options
            </h2>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem', marginBottom: '3rem' }}>
              {(['conservative', 'moderate', 'aggressive'] as const).map((key) => {
                const strat = result.strategies[key]
                const isSelected = selectedStrategy === key
                const isRecommended = result.recommended === key

                return (
                  <div
                    key={key}
                    onClick={() => setSelectedStrategy(key)}
                    className={isSelected ? 'skeuo-card' : 'skeuo-button'}
                    style={{
                      padding: '2rem',
                      cursor: 'pointer',
                      flexDirection: 'column',
                      alignItems: 'flex-start',
                      height: 'auto',
                      border: isSelected ? '2px solid var(--slate-800)' : 'none',
                      background: isSelected ? 'white' : 'var(--skeuo-bg)',
                      transform: isSelected ? 'scale(1.02)' : 'none'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', marginBottom: '1.5rem' }}>
                      <span style={{ fontSize: '2rem' }}>{strategyIcons[key]}</span>
                      {isRecommended && (
                        <span className="badge" style={{ height: 'fit-content', background: 'var(--slate-700)', color: 'white' }}>RECOMMENDED</span>
                      )}
                    </div>
                    <h3 style={{ margin: '0 0 0.5rem 0', textTransform: 'capitalize', fontSize: '1.5rem', fontWeight: 900, color: 'var(--slate-800)' }}>{key}</h3>
                    <p style={{ margin: 0, fontSize: '0.85rem', fontWeight: 700, color: 'var(--slate-500)' }}>
                      {strat.num_stocks} Assets • {strat.expected_monthly_return.toFixed(1)}%/mo
                    </p>
                    <div className="skeuo-recessed" style={{ width: '100%', marginTop: '1.5rem', padding: '1rem', textAlign: 'center' }}>
                      <span style={{ fontSize: '1.25rem', fontWeight: 900, color: 'var(--slate-800)' }}>{strat.estimated_months} Months</span>
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Selected Strategy Detail */}
            {selectedStrategy && result.strategies[selectedStrategy as keyof typeof result.strategies] && (
              <div className="skeuo-card">
                <div className="flex justify-between items-end" style={{ marginBottom: '2rem' }}>
                  <div>
                    <h3 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 900, color: 'var(--slate-800)' }}>
                      {selectedStrategy.toUpperCase()} EXECUTION PLAN
                    </h3>
                    <p style={{ margin: '0.5rem 0 0 0', color: 'var(--slate-500)', fontWeight: 600 }}>
                      Expected Target Date: <span style={{ color: 'var(--slate-600)' }}>{result.strategies[selectedStrategy as keyof typeof result.strategies].target_date}</span>
                    </p>
                  </div>
                  <div className="skeuo-recessed" style={{ padding: '0.75rem 1.5rem', textAlign: 'right' }}>
                    <div style={{ fontSize: '1.5rem', fontWeight: 900, color: 'var(--slate-800)' }}>₹{result.strategies[selectedStrategy as keyof typeof result.strategies].total_allocated.toLocaleString()}</div>
                    <div style={{ fontSize: '0.7rem', fontWeight: 800, color: 'var(--slate-400)' }}>TOTAL DEPLOYED</div>
                  </div>
                </div>

                <div className="skeuo-recessed" style={{ padding: 0, overflow: 'hidden', marginBottom: '2rem' }}>
                  <table className="premium-table" style={{ background: 'transparent' }}>
                    <thead>
                      <tr style={{ background: 'rgba(0,0,0,0.02)' }}>
                        <th style={{ padding: '1rem 1.5rem' }}>Asset</th>
                        <th style={{ padding: '1rem 1.5rem', textAlign: 'right' }}>Price</th>
                        <th style={{ padding: '1rem 1.5rem', textAlign: 'right' }}>Unit Qty</th>
                        <th style={{ padding: '1rem 1.5rem', textAlign: 'right' }}>Deployment</th>
                        <th style={{ padding: '1rem 1.5rem', textAlign: 'center' }}>AI Confidence</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.strategies[selectedStrategy as keyof typeof result.strategies].stocks.map((stock, idx) => (
                        <tr key={idx} style={{ borderBottom: '1px solid rgba(0,0,0,0.03)' }}>
                          <td style={{ padding: '1.25rem 1.5rem', fontWeight: 900, color: 'var(--slate-800)' }}>{stock.symbol.replace('.NS', '')}</td>
                          <td style={{ padding: '1.25rem 1.5rem', textAlign: 'right', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>₹{stock.last_price.toLocaleString()}</td>
                          <td style={{ padding: '1.25rem 1.5rem', textAlign: 'right', fontWeight: 800 }}>{stock.shares}</td>
                          <td style={{ padding: '1.25rem 1.5rem', textAlign: 'right', fontWeight: 900, color: 'var(--slate-800)', fontFamily: 'var(--font-mono)' }}>₹{stock.actual_allocation.toLocaleString()}</td>
                          <td style={{ padding: '1.25rem 1.5rem', textAlign: 'center' }}>
                            <div className="skeuo-progress-container" style={{ width: '100px', margin: '0 auto' }}>
                              <div className="skeuo-progress-bar" style={{ width: `${(stock.buy_prob * 100)}%`, background: 'var(--slate-800)' }}></div>
                            </div>
                            <span style={{ fontSize: '0.7rem', fontWeight: 800, color: 'var(--slate-600)', display: 'block', marginTop: '0.4rem' }}>{(stock.buy_prob * 100).toFixed(1)}%</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1.5rem' }}>
                  <div className="skeuo-recessed" style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '0.7rem', fontWeight: 800, color: 'var(--slate-400)', marginBottom: '0.5rem' }}>MONTHLY ALPHA</div>
                    <div style={{ fontSize: '1.5rem', fontWeight: 900, color: 'var(--slate-700)' }}>{result.strategies[selectedStrategy as keyof typeof result.strategies].expected_monthly_return.toFixed(1)}%</div>
                  </div>
                  <div className="skeuo-recessed" style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '0.7rem', fontWeight: 800, color: 'var(--slate-400)', marginBottom: '0.5rem' }}>LIQUID CASH</div>
                    <div style={{ fontSize: '1.5rem', fontWeight: 900, color: 'var(--slate-800)' }}>₹{result.strategies[selectedStrategy as keyof typeof result.strategies].cash_remaining.toLocaleString()}</div>
                  </div>
                  <div className="skeuo-recessed" style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '0.7rem', fontWeight: 800, color: 'var(--slate-400)', marginBottom: '0.5rem' }}>GOAL MAGNITUDE</div>
                    <div style={{ fontSize: '1.5rem', fontWeight: 900, color: 'var(--slate-800)' }}>₹{result.target_amount.toLocaleString()}</div>
                  </div>
                </div>
              </div>
            )}

            {/* Risk Protocol Warning */}
            <div className="skeuo-recessed" style={{ marginTop: '3rem', borderLeft: '4px solid var(--slate-400)', background: 'rgba(0,0,0,0.02)' }}>
              <h4 style={{ margin: '0 0 1rem 0', color: 'var(--slate-800)', fontWeight: 900, fontSize: '1rem' }}>⚠️ RISK MITIGATION PROTOCOLS</h4>
              <ul style={{ margin: 0, paddingLeft: '1.5rem', color: 'var(--slate-600)', fontSize: '0.9rem', fontWeight: 600, lineHeight: 1.6 }}>
                <li>Past performance metrics are historical and do not guarantee future velocity.</li>
                <li>ML predictive accuracy is currently calibrated at ~47%.</li>
                <li>Implement hard stop-loss buffers to protect principal capital.</li>
                <li>This terminal output does not constitute SEBI-regulated financial advice.</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
