import React from 'react'

type Factor = { name: string; contribution: number }

export default function RiskPanel({ riskScore, factors }: { riskScore: number; factors: Factor[] }) {
  const getRiskLabel = (score: number) => {
    if (score >= 0.7) return { label: 'High', color: '#000000', bg: '#e5e5e5' }
    if (score >= 0.4) return { label: 'Moderate', color: '#404040', bg: '#f5f5f5' }
    return { label: 'Low', color: '#737373', bg: '#fafafa' }
  }

  const riskInfo = getRiskLabel(riskScore)

  return (
    <div className="skeuo-card">
      <h2 className="flex items-center gap-2" style={{ fontSize: '1.25rem', marginBottom: '1.5rem', marginTop: 0, color: 'var(--slate-700)' }}>
        <span style={{
          width: '12px',
          height: '12px',
          borderRadius: '50%',
          background: riskInfo.color,
          boxShadow: `0 0 10px ${riskInfo.color}, inset -2px -2px 4px rgba(0,0,0,0.3)`
        }}></span>
        Risk Analysis
      </h2>

      <div className="skeuo-recessed flex justify-between items-center" style={{ marginBottom: '2rem' }}>
        <div>
          <div style={{ fontSize: '2.5rem', fontVariantNumeric: 'tabular-nums', fontWeight: 900, color: 'var(--slate-800)', textShadow: '1px 1px 0px white' }}>
            {(riskScore * 100).toFixed(0)}%
          </div>
          <div style={{ color: 'var(--slate-500)', fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
            Market Vulnerability
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div style={{
            padding: '0.5rem 1rem',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--skeuo-bg)',
            boxShadow: 'var(--skeuo-outset-shadow)',
            color: riskInfo.color,
            fontWeight: 800,
            fontSize: '0.85rem',
            textTransform: 'uppercase'
          }}>
            {riskInfo.label} Risk
          </div>
        </div>
      </div>

      <div style={{ marginBottom: '2rem' }}>
        <div className="skeuo-progress-container" style={{ height: '16px' }}>
          <div
            className="skeuo-progress-bar"
            style={{
              width: `${riskScore * 100}%`,
              background: `linear-gradient(180deg, ${riskInfo.color} 0%, ${riskInfo.color}dd 100%)`,
              boxShadow: `0 0 10px ${riskInfo.color}44`
            }}
          />
        </div>
      </div>

      {factors && factors.length > 0 && (
        <div style={{ borderTop: '1px solid rgba(0,0,0,0.05)', paddingTop: '1.5rem' }}>
          <h3 style={{ fontSize: '0.8rem', color: 'var(--slate-400)', marginBottom: '1.25rem', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 700 }}>
            Contribution Analysis
          </h3>
          <div className="flex flex-col gap-4">
            {factors.map((f) => (
              <div key={f.name} className="flex flex-col gap-2">
                <div className="flex justify-between items-center" style={{ fontSize: '0.8rem' }}>
                  <span style={{ fontWeight: 600, color: 'var(--slate-600)' }}>{f.name}</span>
                  <span style={{ color: 'var(--slate-500)', fontWeight: 800, fontFamily: 'var(--font-mono)' }}>{(f.contribution * 100).toFixed(1)}%</span>
                </div>
                <div className="skeuo-progress-container">
                  <div
                    className="skeuo-progress-bar"
                    style={{
                      width: `${f.contribution * 100}%`,
                      background: 'linear-gradient(180deg, var(--primary-500) 0%, var(--primary-600) 100%)'
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
