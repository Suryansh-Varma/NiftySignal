import React from 'react'
import Link from 'next/link'

type Position = {
  symbol: string
  name: string
  qty: number
  price: number
  changePct: number
}

export default function StockList({ positions }: { positions: Position[] }) {
  return (
    <div className="skeuo-card">
      <h2 className="flex items-center gap-3" style={{ fontSize: '1.25rem', marginBottom: '1.5rem', marginTop: 0, color: 'var(--slate-700)' }}>
        <span className="skeuo-knob" style={{ width: '28px', height: '28px' }}></span>
        Active Holdings
      </h2>
      {positions.length === 0 ? (
        <div className="skeuo-recessed" style={{ textAlign: 'center', padding: '4rem 1.5rem', color: 'var(--slate-400)' }}>
          <span style={{ fontSize: '3rem', display: 'block', marginBottom: '1.5rem', opacity: 0.3 }}>💼</span>
          <p style={{ margin: '0 0 2rem 0', fontWeight: 700, fontSize: '1rem' }}>Vault is currently empty.</p>
          <Link href="/portfolio" className="skeuo-button" style={{ padding: '0.75rem 1.5rem', background: 'var(--primary-600)', color: 'white' }}>
            + INITIALIZE ASSETS
          </Link>
        </div>
      ) : (
        <div className="skeuo-recessed" style={{ padding: 0, overflow: 'hidden' }}>
          <table className="premium-table" style={{ background: 'transparent' }}>
            <thead>
              <tr style={{ background: 'rgba(0,0,0,0.02)' }}>
                <th style={{ padding: '1rem 1.5rem', color: 'var(--slate-500)', fontSize: '0.7rem' }}>Ticker</th>
                <th className="mobile-hide" style={{ padding: '1rem 1.5rem', color: 'var(--slate-500)', fontSize: '0.7rem' }}>Security</th>
                <th style={{ textAlign: 'right', padding: '1rem 1.5rem', color: 'var(--slate-500)', fontSize: '0.7rem' }}>Volume</th>
                <th style={{ textAlign: 'right', padding: '1rem 1.5rem', color: 'var(--slate-500)', fontSize: '0.7rem' }}>Valuation</th>
                <th style={{ textAlign: 'center', padding: '1rem 1.5rem', color: 'var(--slate-500)', fontSize: '0.7rem' }}>Momentum</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((p, idx) => (
                <tr key={p.symbol} style={{ borderBottom: idx === positions.length - 1 ? 'none' : '1px solid rgba(0,0,0,0.03)' }}>
                  <td style={{ padding: '1.25rem 1.5rem' }}>
                    <span style={{ fontWeight: 900, fontFamily: 'var(--font-mono)', fontSize: '1rem', color: 'var(--slate-800)' }}>{p.symbol}</span>
                  </td>
                  <td className="mobile-hide" style={{ padding: '1.25rem 1.5rem', color: 'var(--slate-500)', fontSize: '0.8rem', fontWeight: 600 }}>{p.name}</td>
                  <td style={{ textAlign: 'right', padding: '1.25rem 1.5rem', fontWeight: 800, color: 'var(--slate-600)', fontFamily: 'var(--font-mono)' }}>{p.qty}</td>
                  <td style={{ textAlign: 'right', padding: '1.25rem 1.5rem', fontWeight: 900, fontFamily: 'var(--font-mono)', color: 'var(--slate-700)' }}>₹{p.price.toFixed(2)}</td>
                  <td style={{ textAlign: 'center', padding: '1.25rem 1.5rem' }}>
                    <div style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '0.4rem',
                      padding: '0.4rem 0.8rem',
                      borderRadius: '4px',
                      background: 'var(--skeuo-bg)',
                      boxShadow: 'var(--skeuo-inset-shadow)',
                      fontSize: '0.75rem',
                      fontWeight: 900,
                      color: p.changePct >= 0 ? 'var(--accent-600)' : '#ef4444'
                    }}>
                      <span style={{
                        width: '6px',
                        height: '6px',
                        borderRadius: '50%',
                        background: p.changePct >= 0 ? 'var(--accent-500)' : '#ef4444',
                        boxShadow: `0 0 6px ${p.changePct >= 0 ? 'var(--accent-500)' : '#ef4444'}`
                      }}></span>
                      {p.changePct >= 0 ? '+' : ''}{p.changePct.toFixed(2)}%
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
