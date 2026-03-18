import React, { useEffect, useState } from 'react'
import axios from 'axios'

interface GoalRec {
  symbol: string
  last_price: number | null
  last_date: string
  recommendation: string
  confidence: number
  buy_prob: number
  weight: number
  allocation_inr: number
}

function formatINR(v: number | null | undefined) {
  if (v === null || v === undefined || isNaN(Number(v))) return '-'
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(Number(v))
}

function formatPct(v: number | null | undefined) {
  if (v === null || v === undefined || isNaN(Number(v))) return '-'
  return `${(Number(v) * 100).toFixed(1)}%`
}

export default function GoalPage() {
  const [targetPct, setTargetPct] = useState(0.15)
  const [horizonDays, setHorizonDays] = useState(126)
  const [capital, setCapital] = useState(1200000)
  const [rows, setRows] = useState<GoalRec[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchGoal = async () => {
    setLoading(true)
    setError(null)
    try {
      // Backend serves precomputed goal CSV; training is done via script
      const res = await axios.get<GoalRec[]>(`http://127.0.0.1:8000/api/goal_recommendations`)
      setRows(res.data || [])
    } catch (e) {
      setError('Goal recommendations not found. Run training first.')
      setRows([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchGoal() }, [])

  return (
    <div className="container">
      <h1>Goal-Based Portfolio</h1>
      <p>Target: {formatPct(targetPct)} | Horizon: {horizonDays} days | Capital: {formatINR(capital)}</p>
      <div style={{ display: 'flex', gap: 12, margin: '12px 0' }}>
        <input type="number" step="0.01" value={targetPct} onChange={e => setTargetPct(Number(e.target.value))} placeholder="Target %" style={{ padding: '8px 10px', width: 140 }} />
        <input type="number" value={horizonDays} onChange={e => setHorizonDays(Number(e.target.value))} placeholder="Horizon (days)" style={{ padding: '8px 10px', width: 160 }} />
        <input type="number" value={capital} onChange={e => setCapital(Number(e.target.value))} placeholder="Capital (INR)" style={{ padding: '8px 10px', width: 160 }} />
        <button onClick={fetchGoal} style={{ padding: '8px 16px' }}>Refresh</button>
      </div>

      {loading && <div>Loading...</div>}
      {error && <div style={{ color: 'red' }}>{error}</div>}

      <table className="rec-table">
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Last Price</th>
            <th>Recommendation</th>
            <th>Confidence</th>
            <th>Expected Buy Prob</th>
            <th>Weight</th>
            <th>Allocation</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(r => (
            <tr key={r.symbol}>
              <td>{r.symbol}</td>
              <td>{formatINR(r.last_price)}</td>
              <td>{r.recommendation || '-'}</td>
              <td>{formatPct(r.confidence)}</td>
              <td>{formatPct(r.buy_prob)}</td>
              <td>{(r.weight * 100).toFixed(1)}%</td>
              <td>{formatINR(r.allocation_inr)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <style jsx>{`
        .container { max-width: 900px; margin: 0 auto; padding: 24px; }
        .rec-table { width: 100%; border-collapse: collapse; }
        .rec-table th, .rec-table td { padding: 8px 10px; border-bottom: 1px solid #eee; text-align: left; }
        thead th { background: #fafafa; font-weight: 600; }
      `}</style>
    </div>
  )
}
