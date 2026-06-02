'use client'
import React, { useEffect, useMemo, useState } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'
import PageLoader from '../components/PageLoader'
import { useAuth } from '../lib/auth'
import { supabase, isValidNiftySymbol, getCompanyName, NIFTY_50 } from '../lib/supabase'
import { getClientApiBase, buildApiUrl } from '../lib/api-base'

type PortfolioPosition = {
  id: number
  symbol: string
  company_name: string
  quantity: number
  buy_price: number
  buy_date: string
}

export default function PortfolioPage() {
  const router = useRouter()
  const { user, loading: authLoading, isAuthenticated } = useAuth()

  const [positions, setPositions] = useState<PortfolioPosition[]>([])
  const [currentPrices, setCurrentPrices] = useState<Record<string, { price: number; date: string }>>({})
  const [loading, setLoading] = useState(true)
  const [analytics, setAnalytics] = useState({ sharpe_ratio: 0, risk_of_ruin: 0, volatility_ann: 0 })

  const [showAddForm, setShowAddForm] = useState(false)
  const [formData, setFormData] = useState({
    symbol: '',
    quantity: 1,
    buy_price: 0,
    buy_date: new Date().toISOString().split('T')[0],
  })

  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [lastSubmitTime, setLastSubmitTime] = useState(0)
  const apiUrl = getClientApiBase()

  useEffect(() => {
    if (authLoading) return
    if (!isAuthenticated) {
      router.push('/login')
      return
    }
    loadPortfolio()
  }, [authLoading, isAuthenticated])

  useEffect(() => {
    if (positions.length > 0) {
      fetchAnalytics()
    } else {
      setAnalytics({ sharpe_ratio: 0, risk_of_ruin: 0, volatility_ann: 0 })
    }
  }, [positions])

  useEffect(() => {
    if (!router.isReady) return
    const addSymbol = typeof router.query.add === 'string' ? router.query.add.toUpperCase() : ''
    if (!addSymbol) return

    const normalized = addSymbol.endsWith('.NS') ? addSymbol : `${addSymbol}.NS`
    if (isValidNiftySymbol(normalized)) {
      setFormData((prev) => ({ ...prev, symbol: normalized }))
      setShowAddForm(true)
      setSuccess(`Ready to add ${normalized} to your portfolio.`)
    }
  }, [router.isReady, router.query.add])

  const loadPortfolio = async () => {
    try {
      setLoading(true)
      setError('')
      setSuccess('')
      setCurrentPrices({})
      if (!user) return

      const { data, error: sbError } = await supabase
        .from('portfolios')
        .select('*')
        .eq('user_id', user.id)
        .order('symbol', { ascending: true })

      if (sbError) throw sbError
      setPositions((data || []) as PortfolioPosition[])

      if (data && data.length > 0) {
        const recRes = await fetch(buildApiUrl(apiUrl, '/api/recommendations'))
        const recommendations = await recRes.json()
        const priceMap: Record<string, { price: number; date: string }> = {}
        recommendations.forEach((rec: any) => {
          if (rec.symbol && rec.last_price) {
            priceMap[rec.symbol] = { price: rec.last_price, date: rec.last_date || 'N/A' }
          }
        })
        setCurrentPrices(priceMap)
      }
    } catch (err: any) {
      console.error('Portfolio load error:', err)
      setError(err.message || 'Unable to load your portfolio right now.')
    } finally {
      setLoading(false)
    }
  }

  const fetchAnalytics = async () => {
    try {
      const holdings = positions.map((p) => ({ symbol: p.symbol, shares: p.quantity, avg_buy_price: p.buy_price }))
      const res = await fetch(buildApiUrl(apiUrl, '/api/portfolio/analyze'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(holdings),
      })
      const data = await res.json()
      setAnalytics({
        sharpe_ratio: Number(data.sharpe_ratio || 0),
        risk_of_ruin: Number(data.risk_of_ruin || 0),
        volatility_ann: Number(data.volatility_ann || 0),
      })
    } catch (err) {
      console.error('Analytics error:', err)
    }
  }

  const handleAddPosition = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    // Rate limiting: prevent rapid successive submissions (3 sec minimum)
    const now = Date.now()
    if (now - lastSubmitTime < 3000) {
      setError('Please wait before submitting again. (3 second cooldown)')
      return
    }

    if (!user || !formData.symbol) {
      setError('User session invalid or symbol missing.')
      return
    }

    const symbol = formData.symbol.trim().toUpperCase()

    // Input validation - symbol format
    if (!isValidNiftySymbol(symbol)) {
      setError('Please enter a valid NSE symbol (example: RELIANCE.NS or RELIANCE).')
      return
    }

    // Input validation - quantity
    if (!formData.quantity || formData.quantity < 1 || !Number.isInteger(formData.quantity)) {
      setError('Quantity must be at least 1 share (whole numbers only).')
      return
    }

    if (formData.quantity > 1000000) {
      setError('Quantity cannot exceed 1,000,000 shares per position.')
      return
    }

    // Input validation - buy price
    if (!formData.buy_price || formData.buy_price <= 0 || formData.buy_price > 1000000) {
      setError('Buy price must be between ₹0.01 and ₹1,000,000.')
      return
    }

    // Input validation - buy date
    const buyDate = new Date(formData.buy_date)
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    if (buyDate > today) {
      setError('Buy date cannot be in the future.')
      return
    }

    // Check if date is too old (more than 50 years)
    const fiftyYearsAgo = new Date()
    fiftyYearsAgo.setFullYear(fiftyYearsAgo.getFullYear() - 50)
    if (buyDate < fiftyYearsAgo) {
      setError('Buy date seems too far in the past. Please check the date.')
      return
    }

    setIsSubmitting(true)

    try {
      const newPosition = {
        user_id: user.id,
        symbol,
        company_name: getCompanyName(symbol),
        quantity: Number(formData.quantity),
        buy_price: Number(formData.buy_price),
        buy_date: formData.buy_date,
      }

      const { error: insertError } = await supabase.from('portfolios').insert([newPosition])
      if (insertError) throw insertError

      setSuccess(`${symbol} added successfully to your portfolio.`)
      setLastSubmitTime(Date.now())
      setFormData({
        symbol: '',
        quantity: 1,
        buy_price: 0,
        buy_date: new Date().toISOString().split('T')[0],
      })
      await loadPortfolio()

      if (router.query.add) {
        router.replace('/portfolio', undefined, { shallow: true })
      }
    } catch (err: any) {
      console.error('Portfolio error:', err)
      setError(err.message || 'Could not add this position. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleRemovePosition = async (id: number, symbolName: string) => {
    setError('')
    setSuccess('')

    // Confirm deletion to prevent accidental removals
    const confirmed = window.confirm(
      `Are you sure you want to remove ${symbolName} from your portfolio? This action cannot be undone.`
    )
    if (!confirmed) return

    // Rate limiting: prevent rapid successive submissions
    const now = Date.now()
    if (now - lastSubmitTime < 2000) {
      setError('Please wait before performing another action. (2 second cooldown)')
      return
    }

    try {
      const { error: deleteError } = await supabase.from('portfolios').delete().eq('id', id)
      if (deleteError) throw deleteError
      setSuccess('Position removed successfully.')
      setLastSubmitTime(Date.now())
      await loadPortfolio()
    } catch (err: any) {
      console.error('Remove error:', err)
      setError(err.message || 'Could not remove this position.')
    }
  }

  const totals = useMemo(() => {
    const totalInvestment = positions.reduce((sum, p) => sum + p.quantity * p.buy_price, 0)
    const totalCurrentValue = positions.reduce((sum, p) => {
      const current = currentPrices[p.symbol]?.price || p.buy_price
      return sum + p.quantity * current
    }, 0)
    const totalPnl = totalCurrentValue - totalInvestment
    return { totalInvestment, totalCurrentValue, totalPnl }
  }, [positions, currentPrices])

  if (authLoading || loading) {
    return <PageLoader isLoading={true} message="Loading portfolio..." />
  }

  return (
    <div className="min-h-screen animate-in">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8" style={{ maxWidth: '1240px', paddingBottom: '2.5rem' }}>
        <div style={headerPanelStyle}>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between sm:flex-wrap">
            <div>
              <h1 style={{ margin: 0, fontSize: '1.72rem', fontWeight: 900, color: 'var(--text-primary)' }}>Portfolio</h1>
              <p style={{ marginTop: '0.35rem', color: 'var(--text-secondary)' }}>
                Track holdings, monitor performance, and update positions in one place.
              </p>
            </div>
            <div className="flex gap-2 w-full sm:w-auto flex-wrap">
              <Link href="/dashboard" className="flex-1 sm:flex-none" style={secondaryActionStyle}>
                Back to dashboard
              </Link>
              <button onClick={() => setShowAddForm((prev) => !prev)} className="flex-1 sm:flex-none" style={primaryActionStyle}>
                {showAddForm ? 'Close form' : 'Add position'}
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" style={{ marginBottom: '1rem' }}>
          <StatCard label="Total Investment" value={`₹${totals.totalInvestment.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`} />
          <StatCard label="Current Value" value={`₹${totals.totalCurrentValue.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`} />
          <StatCard
            label="Unrealized P&L"
            value={`${totals.totalPnl >= 0 ? '+' : '-'}₹${Math.abs(totals.totalPnl).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`}
            valueColor={totals.totalPnl >= 0 ? 'var(--status-buy)' : 'var(--status-sell)'}
          />
          <StatCard label="Open Positions" value={String(positions.length)} />
        </div>

        {positions.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4" style={{ marginBottom: '1rem' }}>
            <StatCard label="Sharpe Ratio" value={analytics.sharpe_ratio.toFixed(2)} />
            <StatCard
              label="Risk of Ruin"
              value={`${analytics.risk_of_ruin.toFixed(1)}%`}
              valueColor={analytics.risk_of_ruin > 10 ? 'var(--status-sell)' : 'var(--status-buy)'}
            />
            <StatCard label="Volatility (Annual)" value={`${analytics.volatility_ann.toFixed(1)}%`} />
          </div>
        )}

        {error && <Message kind="error" text={error} />}
        {success && <Message kind="success" text={success} />}

        {showAddForm && (
          <div style={panelStyle}>
            <h2 style={panelTitleStyle}>Add a new position</h2>
            <form onSubmit={handleAddPosition} className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3" style={{ marginTop: '0.9rem' }}>
              <div style={{ position: 'relative' }}>
                <label style={labelStyle}>Symbol</label>
                <input
                  type="text"
                  value={formData.symbol}
                  onChange={(e) => setFormData((prev) => ({ ...prev, symbol: e.target.value.toUpperCase() }))}
                  placeholder="RELIANCE.NS"
                  style={inputStyle}
                />

                {formData.symbol.length > 0 && NIFTY_50.some((symbol) => symbol.startsWith(formData.symbol) && symbol !== formData.symbol) && (
                  <div style={suggestionPanelStyle}>
                    {NIFTY_50.filter((symbol) => symbol.startsWith(formData.symbol))
                      .slice(0, 6)
                      .map((symbol) => (
                        <button
                          key={symbol}
                          type="button"
                          onClick={() => setFormData((prev) => ({ ...prev, symbol }))}
                          style={suggestionItemStyle}
                        >
                          <span>{getCompanyName(symbol)}</span>
                          <span style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '0.74rem' }}>{symbol}</span>
                        </button>
                      ))}
                  </div>
                )}
              </div>

              <div>
                <label style={labelStyle}>Quantity</label>
                <input
                  type="number"
                  min={1}
                  value={formData.quantity}
                  onChange={(e) => setFormData((prev) => ({ ...prev, quantity: Number(e.target.value || 0) }))}
                  style={inputStyle}
                />
              </div>

              <div>
                <label style={labelStyle}>Buy price</label>
                <input
                  type="number"
                  min={0}
                  step="0.01"
                  value={formData.buy_price}
                  onChange={(e) => setFormData((prev) => ({ ...prev, buy_price: Number(e.target.value || 0) }))}
                  style={inputStyle}
                />
              </div>

              <div>
                <label style={labelStyle}>Buy date</label>
                <input
                  type="date"
                  value={formData.buy_date}
                  onChange={(e) => setFormData((prev) => ({ ...prev, buy_date: e.target.value }))}
                  style={inputStyle}
                />
              </div>

              <div className="sm:col-span-2 lg:col-span-4 flex justify-end gap-2">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  style={{
                    ...primaryActionStyle,
                    opacity: isSubmitting ? 0.6 : 1,
                    cursor: isSubmitting ? 'not-allowed' : 'pointer',
                  }}
                >
                  {isSubmitting ? 'Saving...' : 'Save position'}
                </button>
              </div>
            </form>
          </div>
        )}

        <div style={panelStyle}>
          <div className="flex items-center justify-between" style={{ marginBottom: '0.9rem' }}>
            <h2 style={panelTitleStyle}>Your holdings</h2>
            <span style={chipStyle}>{positions.length} items</span>
          </div>

          {positions.length === 0 ? (
            <p style={{ margin: 0, color: 'var(--text-secondary)' }}>No holdings yet. Add your first position to begin tracking performance.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr style={tableHeadRowStyle}>
                    <th style={thLeftStyle}>Stock</th>
                    <th style={thRightStyle} className="hide-xs">Qty</th>
                    <th style={thRightStyle} className="hide-xs">Buy Price</th>
                    <th style={thRightStyle}>Current Price</th>
                    <th style={thRightStyle}>P&L</th>
                    <th style={thRightStyle}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {positions.map((position) => {
                    const currentPrice = currentPrices[position.symbol]?.price || position.buy_price
                    const pnlValue = (currentPrice - position.buy_price) * position.quantity
                    const pnlPct = ((currentPrice - position.buy_price) / position.buy_price) * 100

                    return (
                      <tr key={position.id} style={tableBodyRowStyle}>
                        <td style={tdLeftStyle}>
                          <div className="flex flex-col">
                            <span style={{ color: 'var(--text-primary)', fontWeight: 800 }}>{position.company_name || position.symbol}</span>
                            <span style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                              {position.symbol} • {position.quantity} qty
                            </span>
                          </div>
                        </td>
                        <td style={tdRightStyle} className="hide-xs">{position.quantity}</td>
                        <td style={tdRightStyle} className="hide-xs">₹{position.buy_price.toFixed(2)}</td>
                        <td style={tdRightStyle}>₹{currentPrice.toFixed(2)}</td>
                        <td style={{ ...tdRightStyle, color: pnlValue >= 0 ? 'var(--status-buy)' : 'var(--status-sell)' }}>
                          <div>
                            <div>{pnlValue >= 0 ? '+' : ''}₹{Math.abs(pnlValue).toFixed(0)}</div>
                            <div style={{ fontSize: '0.74rem' }}>{pnlPct >= 0 ? '+' : ''}{pnlPct.toFixed(1)}%</div>
                          </div>
                        </td>
                        <td style={tdRightStyle}>
                          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.35rem', flexWrap: 'wrap' }}>
                            <Link href={`/company/${position.symbol}`} style={{ ...secondaryActionStyle, padding: '0.35rem 0.5rem', fontSize: '0.75rem' }}>
                              View
                            </Link>
                            <button
                              onClick={() => handleRemovePosition(position.id, position.company_name || position.symbol)}
                              style={{ ...dangerActionStyle, padding: '0.35rem 0.5rem', fontSize: '0.75rem' }}
                            >
                              Remove
                            </button>
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value, valueColor }: { label: string; value: string; valueColor?: string }) {
  return (
    <div style={statCardStyle}>
      <p style={{ margin: 0, color: 'var(--text-muted)', fontWeight: 700, fontSize: '0.8rem' }}>{label}</p>
      <p style={{ margin: '0.35rem 0 0', color: valueColor || 'var(--text-primary)', fontWeight: 900, fontSize: '1.4rem' }}>{value}</p>
    </div>
  )
}

function Message({ kind, text }: { kind: 'error' | 'success'; text: string }) {
  const isError = kind === 'error'
  return (
    <div
      style={{
        marginBottom: '1rem',
        border: `1px solid ${isError ? 'rgba(239,68,68,0.35)' : 'rgba(16,185,129,0.35)'}`,
        background: isError ? 'rgba(127,29,29,0.2)' : 'rgba(6,78,59,0.2)',
        color: isError ? '#fecaca' : '#a7f3d0',
        borderRadius: '10px',
        padding: '0.68rem 0.8rem',
        fontWeight: 700,
        fontSize: '0.88rem',
      }}
    >
      {text}
    </div>
  )
}

const statCardStyle: React.CSSProperties = {
  border: '1px solid var(--border-glass)',
  borderRadius: '16px',
  background: 'rgba(12, 17, 26, 0.72)',
  padding: '1rem',
}

const headerPanelStyle: React.CSSProperties = {
  border: '1px solid var(--border-glass)',
  borderRadius: '18px',
  background: 'rgba(12, 17, 26, 0.72)',
  padding: '1.2rem',
  marginBottom: '1rem',
}

const panelStyle: React.CSSProperties = {
  border: '1px solid var(--border-glass)',
  borderRadius: '16px',
  background: 'rgba(12, 17, 26, 0.72)',
  padding: '1rem',
  marginBottom: '1rem',
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
  color: 'var(--text-secondary)',
  fontSize: '0.86rem',
}

const tdRightStyle: React.CSSProperties = {
  textAlign: 'right',
  padding: '0.62rem 0.2rem',
  color: 'var(--text-secondary)',
  fontWeight: 700,
  fontSize: '0.84rem',
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
  whiteSpace: 'nowrap',
  display: 'inline-block',
}

const dangerActionStyle: React.CSSProperties = {
  borderRadius: '10px',
  border: '1px solid rgba(239,68,68,0.35)',
  background: 'rgba(127,29,29,0.2)',
  color: '#fecaca',
  padding: '0.52rem 0.75rem',
  cursor: 'pointer',
  fontWeight: 700,
  fontSize: '0.82rem',
}

const chipStyle: React.CSSProperties = {
  borderRadius: '999px',
  border: '1px solid var(--border-glass)',
  color: 'var(--text-muted)',
  fontWeight: 700,
  fontSize: '0.76rem',
  padding: '0.36rem 0.7rem',
}

const labelStyle: React.CSSProperties = {
  color: 'var(--text-muted)',
  fontSize: '0.75rem',
  fontWeight: 700,
  display: 'block',
  marginBottom: '0.35rem',
}

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '0.62rem 0.72rem',
  borderRadius: '10px',
  border: '1px solid var(--border-glass)',
  background: 'rgba(15,23,42,0.7)',
  color: 'var(--text-primary)',
  outline: 'none',
  fontWeight: 600,
}

const suggestionPanelStyle: React.CSSProperties = {
  position: 'absolute',
  left: 0,
  right: 0,
  top: '100%',
  marginTop: '0.35rem',
  borderRadius: '10px',
  border: '1px solid var(--border-glass)',
  background: 'rgba(12, 17, 26, 0.98)',
  zIndex: 20,
  overflow: 'hidden',
}

const suggestionItemStyle: React.CSSProperties = {
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  width: '100%',
  border: 'none',
  background: 'transparent',
  color: 'var(--text-primary)',
  padding: '0.55rem 0.65rem',
  cursor: 'pointer',
  fontWeight: 700,
  fontSize: '0.82rem',
}
