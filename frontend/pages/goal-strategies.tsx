import React, { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import axios from 'axios'
import { getClientApiBase, buildApiUrl } from '../lib/api-base'

const API_BASE = getClientApiBase()

type StrategyType = 'conservative' | 'moderate' | 'aggressive'

interface Recommendation {
  symbol: string
  date: string
  close: number
  buy_prob: number
  confidence: number
  weight: number
}

interface Strategy {
  name: string
  target_return: string
  horizon: string
  description: string
  risk_level: string
}

const formatINR = (value: number): string =>
  new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)

export default function GoalStrategiesPage() {
  const [strategies, setStrategies] = useState<Record<string, Strategy>>({})
  const [selectedStrategy, setSelectedStrategy] = useState<StrategyType>('aggressive')
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [capital, setCapital] = useState<number>(1200000)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [best, setBest] = useState<{ recommended?: StrategyType } | null>(null)
  const [bestLoading, setBestLoading] = useState<boolean>(true)

  useEffect(() => {
    const fetchStrategies = async () => {
      try {
        const res = await axios.get(buildApiUrl(API_BASE, '/api/goal_strategies'))
        setStrategies(res.data)
      } catch (err) {
        console.error('Failed to fetch strategies:', err)
      }
    }
    fetchStrategies()
  }, [])

  useEffect(() => {
    const fetchBest = async () => {
      setBestLoading(true)
      try {
        const res = await axios.get(buildApiUrl(API_BASE, '/api/goal_best'))
        setBest(res.data)
      } catch (err) {
        console.error('Failed to fetch best strategy:', err)
      } finally {
        setBestLoading(false)
      }
    }
    fetchBest()
  }, [])

  useEffect(() => {
    const fetchRecommendations = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await axios.get(buildApiUrl(API_BASE, `/api/goal_recommendations/${selectedStrategy}`))
        setRecommendations(res.data)
      } catch (err) {
        setError(`Failed to load ${selectedStrategy} recommendations. Train models and try again.`)
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    fetchRecommendations()
  }, [selectedStrategy])

  const computedRecs = useMemo(
    () =>
      recommendations.map((rec) => ({
        ...rec,
        allocationComputed: rec.weight * capital,
      })),
    [recommendations, capital]
  )

  const totalAllocation = useMemo(
    () => computedRecs.reduce((sum, rec) => sum + rec.allocationComputed, 0),
    [computedRecs]
  )

  return (
    <div className="min-h-screen animate-in">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8" style={{ maxWidth: '1240px', paddingBottom: '2.5rem' }}>
        <section style={panelStyle}>
          <div className="flex items-start justify-between flex-wrap gap-3">
            <div>
              <h1 style={titleStyle}>Goal Strategies</h1>
              <p style={subtitleStyle}>Compare investment styles and get strategy-specific allocations.</p>
            </div>
            <div className="flex gap-2">
              <Link href="/goal-optimizer" style={secondaryActionStyle}>Goal Optimizer</Link>
              <Link href="/portfolio" style={secondaryActionStyle}>Portfolio</Link>
            </div>
          </div>
        </section>

        <section style={panelStyle}>
          <div className="flex items-center justify-between gap-3 flex-wrap">
            <h2 style={panelTitleStyle}>Recommended approach</h2>
            {bestLoading ? (
              <span style={chipStyle}>Evaluating...</span>
            ) : best?.recommended ? (
              <span style={chipStyle}>Best: {best.recommended}</span>
            ) : (
              <span style={chipStyle}>No recommendation yet</span>
            )}
          </div>

          {best?.recommended && (
            <div className="flex justify-end" style={{ marginTop: '0.8rem' }}>
              <button onClick={() => setSelectedStrategy(best.recommended!)} style={primaryActionStyle}>
                View best strategy
              </button>
            </div>
          )}
        </section>

        <section className="grid grid-cols-1 md:grid-cols-3 gap-3" style={{ marginBottom: '1rem' }}>
          {Object.entries(strategies).map(([key, strategy]) => {
            const selected = selectedStrategy === key
            return (
              <button
                key={key}
                onClick={() => setSelectedStrategy(key as StrategyType)}
                style={{
                  textAlign: 'left',
                  borderRadius: '12px',
                  border: selected ? '1px solid rgba(0,255,204,0.35)' : '1px solid var(--border-glass)',
                  background: selected ? 'rgba(0,255,204,0.1)' : 'rgba(15,23,42,0.6)',
                  color: 'var(--text-primary)',
                  padding: '0.9rem',
                  cursor: 'pointer',
                }}
              >
                <strong style={{ textTransform: 'capitalize' }}>{strategy.name}</strong>
                <div style={{ color: 'var(--text-secondary)', marginTop: '0.38rem', fontSize: '0.84rem' }}>{strategy.description}</div>
                <div className="flex items-center justify-between" style={{ marginTop: '0.65rem', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                  <span>{strategy.risk_level} risk</span>
                  <span>{strategy.horizon}</span>
                </div>
              </button>
            )
          })}
        </section>

        <section style={panelStyle}>
          <div className="flex items-center justify-between gap-3 flex-wrap" style={{ marginBottom: '0.9rem' }}>
            <h2 style={panelTitleStyle}>{strategies[selectedStrategy]?.name || 'Selected'} recommendations</h2>
            <div className="flex items-center gap-2">
              <label htmlFor="capital" style={labelStyle}>Capital</label>
              <input
                id="capital"
                type="number"
                min={100000}
                step={10000}
                value={capital}
                onChange={(e) => setCapital(Math.max(0, Number(e.target.value) || 0))}
                style={inputStyle}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3" style={{ marginBottom: '0.9rem' }}>
            <StatCard label="Total Allocation" value={formatINR(totalAllocation)} />
            <StatCard label="Target Return" value={strategies[selectedStrategy]?.target_return || '-'} valueColor="var(--primary-glow)" />
            <StatCard label="Horizon" value={strategies[selectedStrategy]?.horizon || '-'} />
          </div>

          {loading ? (
            <p style={{ margin: 0, color: 'var(--text-secondary)' }}>Loading recommendations...</p>
          ) : error ? (
            <div style={errorStyle}>{error}</div>
          ) : computedRecs.length === 0 ? (
            <p style={{ margin: 0, color: 'var(--text-secondary)' }}>No recommendations available for this strategy.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[760px] table-fixed">
                <thead>
                  <tr style={tableHeadRowStyle}>
                    <th style={{ ...thLeftStyle, width: '10%' }}>Rank</th>
                    <th style={{ ...thLeftStyle, width: '20%' }}>Symbol</th>
                    <th style={{ ...thRightStyle, width: '18%' }}>Price</th>
                    <th style={{ ...thRightStyle, width: '16%' }}>Confidence</th>
                    <th style={{ ...thRightStyle, width: '14%' }}>Weight</th>
                    <th style={{ ...thRightStyle, width: '22%' }}>Allocation</th>
                  </tr>
                </thead>
                <tbody>
                  {computedRecs.map((rec, idx) => (
                    <tr key={`${rec.symbol}-${idx}`} style={tableBodyRowStyle}>
                      <td style={tdNumberStyle}>{idx + 1}</td>
                      <td style={{ ...tdLeftStyle, whiteSpace: 'nowrap' }}>{rec.symbol.replace('.NS', '')}</td>
                      <td style={tdNumberStyle}>{formatINR(rec.close)}</td>
                      <td style={tdNumberStyle}>{rec.confidence.toFixed(1)}%</td>
                      <td style={tdNumberStyle}>{(rec.weight * 100).toFixed(1)}%</td>
                      <td style={tdNumberStyle}>{formatINR(rec.allocationComputed)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

function StatCard({ label, value, valueColor }: { label: string; value: string; valueColor?: string }) {
  return (
    <div style={statCardStyle}>
      <p style={{ margin: 0, color: 'var(--text-muted)', fontWeight: 700, fontSize: '0.78rem' }}>{label}</p>
      <p style={{ margin: '0.32rem 0 0', color: valueColor || 'var(--text-primary)', fontWeight: 900, fontSize: '1.24rem' }}>{value}</p>
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
  borderRadius: '12px',
  background: 'rgba(15,23,42,0.6)',
  padding: '0.8rem',
}

const errorStyle: React.CSSProperties = {
  border: '1px solid rgba(239,68,68,0.35)',
  background: 'rgba(127,29,29,0.2)',
  color: '#fecaca',
  borderRadius: '10px',
  padding: '0.68rem 0.8rem',
  fontWeight: 700,
  fontSize: '0.88rem',
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

const inputStyle: React.CSSProperties = {
  width: '150px',
  padding: '0.52rem 0.65rem',
  borderRadius: '10px',
  border: '1px solid var(--border-glass)',
  background: 'rgba(15,23,42,0.7)',
  color: 'var(--text-primary)',
  outline: 'none',
  fontWeight: 600,
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

const tdNumberStyle: React.CSSProperties = {
  ...tdRightStyle,
  fontVariantNumeric: 'tabular-nums',
  whiteSpace: 'nowrap',
}
