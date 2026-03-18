'use client'
import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/router'
import Link from 'next/link'
import { useAuth } from '../lib/auth'
import { supabase, isValidNiftySymbol, getCompanyName, NIFTY_50 } from '../lib/supabase'

export default function PortfolioPage() {
  const router = useRouter()
  const { user, loading: authLoading, isAuthenticated } = useAuth()
  const [positions, setPositions] = useState<any[]>([])
  const [currentPrices, setCurrentPrices] = useState<Record<string, { price: number; date: string }>>({})
  const [loading, setLoading] = useState(true)
  const [analytics, setAnalytics] = useState<any>({ sharpe_ratio: 0, risk_of_ruin: 0, volatility_ann: 0, status: 'loading' })
  const [showAddForm, setShowAddForm] = useState(false)
  const [formData, setFormData] = useState({ symbol: '', quantity: 1, buy_price: 0, buy_date: new Date().toISOString().split('T')[0] })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

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
    }
  }, [positions])

  const loadPortfolio = async () => {
    try {
      setLoading(true)
      if (!user) return

      const { data, error: sbError } = await supabase
        .from('portfolios')
        .select('*')
        .eq('user_id', user.id)
        .order('symbol', { ascending: true })

      if (sbError) throw sbError
      setPositions(data || [])

      if (data && data.length > 0) {
        const recRes = await fetch(`${apiUrl}/api/recommendations`)
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
      console.error('Loader error:', err)
      setError(err.message || 'Failed to sync with secure database')
    } finally {
      setLoading(false)
    }
  }

  const fetchAnalytics = async () => {
    try {
      const holdings = positions.map(p => ({
        symbol: p.symbol,
        shares: p.quantity,
        avg_buy_price: p.buy_price
      }))
      
      const res = await fetch(`${apiUrl}/api/portfolio/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(holdings)
      })
      const data = await res.json()
      setAnalytics(data)
    } catch (err) {
      console.error('Analytics sync failed:', err)
    }
  }

  const handleAddPosition = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!user || !formData.symbol) return
    const sym = formData.symbol.toUpperCase()
    if (!isValidNiftySymbol(sym)) { setError('Invalid symbol format'); return }

    try {
      const newPos = {
        user_id: user.id,
        symbol: sym,
        company_name: getCompanyName(sym),
        quantity: parseInt(String(formData.quantity)),
        buy_price: parseFloat(String(formData.buy_price)),
        buy_date: formData.buy_date
      }
      const { error: insError } = await supabase.from('portfolios').insert([newPos])
      if (insError) throw insError
      setSuccess(`Position established: ${sym}`)
      loadPortfolio()
      setShowAddForm(false)
    } catch (err: any) {
      setError(err.message)
    }
  }

  const handleRemovePosition = async (id: number) => {
    try {
      const { error: delError } = await supabase.from('portfolios').delete().eq('id', id)
      if (delError) throw delError
      loadPortfolio()
      setSuccess('Position liquidated')
    } catch (err: any) {
      setError(err.message)
    }
  }

  // Icons
  const IconBack = () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
  const IconRisk = () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>

  if (authLoading || loading) return (
     <div className="min-h-screen bg-[var(--bg-deep)] flex flex-col items-center justify-center gap-6">
        <div className="h-2 w-24 bg-[var(--bg-card)] rounded-full overflow-hidden">
           <div className="h-full bg-[var(--primary-glow)] animate-slide"></div>
        </div>
        <span className="text-[10px] font-mono text-[var(--text-muted)] tracking-widest uppercase">Syncing Terminal...</span>
     </div>
  )

  const totalInvestment = positions.reduce((sum, p) => sum + (p.quantity * p.buy_price), 0)
  const totalCurrentValue = positions.reduce((sum, p) => sum + (p.quantity * (currentPrices[p.symbol]?.price || p.buy_price)), 0)
  const totalPnl = totalCurrentValue - totalInvestment

  return (
    <div className="min-h-screen bg-[var(--bg-deep)] py-10 px-6 animate-in">
      <div className="container mx-auto space-y-10">
        
        {/* Navigation & Header */}
        <div className="flex flex-col md:flex-row justify-between items-end gap-6">
          <div className="space-y-4">
             <Link href="/" className="text-[var(--text-muted)] hover:text-white transition-colors flex items-center gap-2 text-[10px] font-mono tracking-widest uppercase">
                <IconBack /> System_Home
             </Link>
             <h1 className="text-5xl font-black tracking-tighter text-white uppercase italic">
                Active <span className="text-[var(--secondary-glow)]">Assets</span>
             </h1>
             <p className="text-[var(--text-secondary)] font-mono text-xs tracking-widest uppercase">
                Operational Ledger // {positions.length} Positions Active
             </p>
          </div>
          
          <div className="flex gap-4">
             <button onClick={() => setShowAddForm(true)} className="px-6 py-3 rounded-2xl bg-[var(--secondary-glow)] text-black font-black uppercase tracking-widest text-[10px] hover:translate-y-[-2px] transition-all">
                Manual_Entry
             </button>
          </div>
        </div>

        {/* Intelligence HUD */}
        {positions.length > 0 && (
           <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="p-6 rounded-3xl border border-[var(--border-glass)] bg-[var(--bg-card)]">
                 <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider block mb-2">Sharpe Efficiency</span>
                 <div className="text-3xl font-black italic text-white">{analytics.sharpe_ratio}</div>
                 <span className="text-[8px] font-mono text-[var(--primary-glow)] uppercase mt-1 block">Institutional Threshold: 1.0+</span>
              </div>
              <div className="p-6 rounded-3xl border border-[var(--border-glass)] bg-[var(--bg-card)]">
                 <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider block mb-2">Risk of Ruin</span>
                 <div className={`text-3xl font-black italic ${analytics.risk_of_ruin > 10 ? 'text-[var(--status-sell)]' : 'text-[var(--primary-glow)]'}`}>
                    {analytics.risk_of_ruin}%
                 </div>
                 <span className="text-[8px] font-mono text-[var(--text-muted)] uppercase mt-1 block">50% Drawdown Prob.</span>
              </div>
              <div className="p-6 rounded-3xl border border-[var(--border-glass)] bg-[var(--bg-card)]">
                 <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider block mb-2">P&L Status</span>
                 <div className={`text-3xl font-black italic ${totalPnl >= 0 ? 'text-[var(--status-buy)]' : 'text-[var(--status-sell)]'}`}>
                    ₹{Math.abs(totalPnl).toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                 </div>
                 <span className="text-[8px] font-mono text-[var(--text-muted)] uppercase mt-1 block">Net Unrealized Value</span>
              </div>
              <div className="p-6 rounded-3xl border border-[var(--border-glass)] bg-[var(--bg-card)]">
                 <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider block mb-2">Asset Volatility</span>
                 <div className="text-3xl font-black italic text-white">{analytics.volatility_ann}%</div>
                 <span className="text-[8px] font-mono text-[var(--text-muted)] uppercase mt-1 block">Annualized Variation</span>
              </div>
           </div>
        )}

        {/* Alerts & Errors */}
        {error && <div className="p-4 rounded-xl border border-red-900/50 bg-red-900/10 text-red-500 font-mono text-[10px] uppercase">{error}</div>}
        {success && <div className="p-4 rounded-xl border border-cyan-900/50 bg-cyan-900/10 text-cyan-500 font-mono text-[10px] uppercase">{success}</div>}

        {/* Allocation Form (Overlay-style) */}
        {showAddForm && (
           <div className="p-8 rounded-3xl border border-[var(--border-glass)] bg-[var(--bg-card)] animate-in">
              <div className="flex justify-between items-center mb-6">
                 <h2 className="text-xl font-black text-white italic uppercase tracking-tighter">New Asset Specification</h2>
                 <button onClick={() => setShowAddForm(false)} className="text-[var(--text-muted)] hover:text-white">CLOSE_X</button>
              </div>
              <form onSubmit={handleAddPosition} className="space-y-8">
                 <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <div className="relative">
                       <label className="text-[8px] font-mono text-[var(--text-muted)] uppercase block mb-2">Ticker Specification</label>
                       <input 
                         type="text" 
                         value={formData.symbol} 
                         onChange={e => {
                           const val = e.target.value.toUpperCase();
                           setFormData({...formData, symbol: val});
                         }} 
                         onFocus={() => setFormData({...formData, symbol: formData.symbol})}
                         placeholder="RELIANCE.NS" 
                         className="w-full bg-[var(--bg-deep)] border border-[var(--border-glass)] p-3 rounded-xl text-white font-bold outline-none uppercase tracking-widest text-[10px]"
                       />
                       
                       {/* Dropdown Suggestions */}
                       {formData.symbol.length > 0 && NIFTY_50.some(s => s.startsWith(formData.symbol) && s !== formData.symbol) && (
                         <div className="absolute top-full left-0 right-0 mt-2 p-1 rounded-xl bg-[var(--bg-card)] border border-[var(--border-glass)] z-50 backdrop-blur-xl max-h-40 overflow-y-auto">
                           {NIFTY_50.filter(s => s.startsWith(formData.symbol)).slice(0, 5).map(s => (
                             <div 
                               key={s} 
                               onClick={() => setFormData({...formData, symbol: s})}
                               className="p-3 hover:bg-white/5 cursor-pointer rounded-lg flex justify-between items-center group"
                             >
                                <span className="text-[9px] font-black text-white italic">{getCompanyName(s)}</span>
                                <span className="text-[8px] font-mono text-[var(--text-muted)] group-hover:text-[var(--primary-glow)]">{s}</span>
                             </div>
                           ))}
                         </div>
                       )}
                    </div>
                    <div>
                       <label className="text-[8px] font-mono text-[var(--text-muted)] uppercase block mb-2">Quantity</label>
                       <input type="number" value={formData.quantity} onChange={e => setFormData({...formData, quantity: parseInt(e.target.value)})} className="w-full bg-[var(--bg-deep)] border border-[var(--border-glass)] p-3 rounded-xl text-white font-bold outline-none text-[10px]"/>
                    </div>
                    <div>
                       <label className="text-[8px] font-mono text-[var(--text-muted)] uppercase block mb-2">Avg_Acquisition_Price</label>
                       <input type="number" value={formData.buy_price} onChange={e => setFormData({...formData, buy_price: parseFloat(e.target.value)})} className="w-full bg-[var(--bg-deep)] border border-[var(--border-glass)] p-3 rounded-xl text-white font-bold outline-none text-[10px]"/>
                    </div>
                    <div className="flex items-end">
                       <button type="submit" className="w-full py-3 rounded-xl bg-[var(--primary-glow)] text-black font-black uppercase text-[10px] tracking-widest hover:brightness-110 active:scale-95 transition-all">Submit_to_Ledger</button>
                    </div>
                 </div>
              </form>
           </div>
        )}

        {/* Main Ledger Table */}
        <div className="p-8 rounded-3xl border border-[var(--border-glass)] bg-[var(--bg-card)]">
           <div className="overflow-x-auto">
              {positions.length === 0 ? (
                 <div className="py-20 text-center space-y-4">
                    <p className="text-[var(--text-muted)] font-mono text-xs uppercase tracking-[0.2em]">Operational_Ledger: Empty</p>
                    <button onClick={() => setShowAddForm(true)} className="text-[var(--secondary-glow)] font-black text-[10px] uppercase border border-[var(--secondary-glow)]/30 px-6 py-2 rounded-full">Initialize_First_Asset</button>
                 </div>
              ) : (
                <table className="w-full text-left border-collapse">
                   <thead>
                      <tr className="border-b border-[var(--border-glass)]">
                         <th className="pb-4 text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider text-transform: uppercase">Asset</th>
                         <th className="pb-4 text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider text-right">Shares</th>
                         <th className="pb-4 text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider text-right">Entry (Avg)</th>
                         <th className="pb-4 text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider text-right">Market (Live)</th>
                         <th className="pb-4 text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider text-right">Performance</th>
                         <th className="pb-4 text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider text-right">Action</th>
                      </tr>
                   </thead>
                   <tbody>
                      {positions.map((pos) => {
                        const marketPrice = currentPrices[pos.symbol]?.price || pos.buy_price
                        const pnl = (marketPrice - pos.buy_price) * pos.quantity
                        const pnlPct = ((marketPrice - pos.buy_price) / pos.buy_price) * 100
                        return (
                           <tr key={pos.id} className="border-b border-[var(--border-glass)] group hover:bg-white/5 transition-colors">
                              <td className="py-6">
                                 <div className="flex flex-col">
                                    <span className="text-white font-black text-sm uppercase tracking-tighter italic">{pos.company_name}</span>
                                    <span className="text-[var(--text-muted)] font-mono text-[9px] uppercase tracking-widest">{pos.symbol}</span>
                                 </div>
                              </td>
                              <td className="py-6 text-right font-mono text-white text-sm">{pos.quantity}</td>
                              <td className="py-6 text-right font-mono text-[var(--text-secondary)] text-sm">₹{pos.buy_price.toFixed(2)}</td>
                              <td className="py-6 text-right font-mono text-[var(--primary-glow)] text-sm">₹{marketPrice.toFixed(2)}</td>
                              <td className="py-6 text-right">
                                 <div className="flex flex-col items-end">
                                    <span className={`text-[10px] font-black ${pnl >= 0 ? 'text-[var(--status-buy)]' : 'text-[var(--status-sell)]'}`}>
                                       {pnl >= 0 ? '+' : ''}{pnl.toFixed(0)}
                                    </span>
                                    <span className="text-[8px] font-mono text-[var(--text-muted)] opacity-50 uppercase">
                                       {pnlPct >= 0 ? '+' : ''}{pnlPct.toFixed(1)}%
                                    </span>
                                 </div>
                              </td>
                              <td className="py-6 text-right">
                                 <button onClick={() => handleRemovePosition(pos.id)} className="text-[10px] font-bold text-red-500/50 hover:text-red-500 transition-colors uppercase">Liquidate</button>
                              </td>
                           </tr>
                        )
                      })}
                   </tbody>
                </table>
              )}
           </div>
        </div>

      </div>
    </div>
  )
}
