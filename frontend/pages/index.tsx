import React, { useEffect, useState } from 'react'
import axios from 'axios'
import Link from 'next/link'
import { useAuth } from '../lib/auth'
import MarketRiskPulse from '../components/MarketRiskPulse'
import LivePredictCard from '../components/LivePredictCard'

export default function Home() {
  const [recs, setRecs] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const { isAuthenticated } = useAuth()
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  useEffect(() => {
    if (isAuthenticated) {
      setLoading(true)
      axios
        .get(`${apiUrl}/api/recommendations`)
        .then(r => setRecs(r.data.slice(0, 10)))
        .catch(err => console.error('Failed to load:', err))
        .finally(() => setLoading(false))
    }
  }, [isAuthenticated, apiUrl])

  // Icons as functional components
  const IconVault = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line></svg>
  );

  const IconStrategy = () => (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
  );

  if (isAuthenticated) {
    return (
      <div className="min-h-screen bg-[var(--bg-deep)] py-10 px-6 animate-in">
        <div className="container mx-auto space-y-10">
          
          <div className="flex flex-col md:flex-row justify-between items-start gap-6">
            <div className="space-y-2">
              <h1 className="text-5xl font-black tracking-tighter text-white uppercase italic">
                NiftySignal <span className="text-[var(--primary-glow)]">AI</span>
              </h1>
              <p className="text-[var(--text-secondary)] font-mono text-xs tracking-widest uppercase">
                        Smart market signals for NSE stocks
              </p>
            </div>
            
            <div className="w-full md:w-80">
                <MarketRiskPulse />
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2">
               <LivePredictCard />
            </div>

            <div className="flex flex-col gap-6">
               <div className="p-6 rounded-3xl border border-[var(--border-glass)] bg-[var(--bg-card)] space-y-4">
                  <h4 className="text-xs font-bold text-[var(--text-muted)] tracking-widest uppercase">System Control</h4>
                  <div className="flex flex-col gap-3">
                     <Link href="/portfolio" className="group flex items-center justify-between p-4 rounded-2xl bg-[var(--bg-deep)] border border-[var(--border-glass)] hover:border-[var(--primary-glow)] transition-all">
                        <div className="flex items-center gap-3">
                           <IconVault />
                           <span className="text-sm font-bold text-white group-hover:text-[var(--primary-glow)] transition-colors text-transform: uppercase">Vault Terminal</span>
                        </div>
                        <div className="h-1 w-1 rounded-full bg-[var(--primary-glow)]"></div>
                     </Link>
                     <Link href="/goal-optimizer" className="group flex items-center justify-between p-4 rounded-2xl bg-[var(--bg-deep)] border border-[var(--border-glass)] hover:border-[var(--secondary-glow)] transition-all">
                        <div className="flex items-center gap-3">
                           <IconStrategy />
                           <span className="text-sm font-bold text-white group-hover:text-[var(--secondary-glow)] transition-colors text-transform: uppercase">Strategy Matrix</span>
                        </div>
                        <div className="h-1 w-1 rounded-full bg-[var(--secondary-glow)]"></div>
                     </Link>
                  </div>
               </div>

               <div className="p-6 rounded-3xl border border-[var(--border-glass)] bg-gradient-to-br from-[#0c111a] to-[#05070a] shadow-xl">
                  <div className="flex items-center justify-between mb-4">
                     <span className="text-[10px] font-mono text-[var(--secondary-glow)]">SYSTEM HEALTH</span>
                     <div className="h-1 w-1 rounded-full bg-[var(--secondary-glow)] animate-pulse"></div>
                  </div>
                  <p className="text-sm text-[var(--text-secondary)] font-medium">Live scan is running across top NSE names. Signals refresh continuously based on latest model output.</p>
               </div>
            </div>
          </div>

          <div className="p-8 rounded-3xl border border-[var(--border-glass)] bg-[var(--bg-card)]">
             <div className="flex justify-between items-center mb-8">
                <h3 className="text-xl font-black text-white uppercase tracking-tighter italic">Top Recommendations</h3>
                <span className="bg-[var(--bg-deep)] py-2 px-4 rounded-full border border-[var(--border-glass)] text-[10px] font-mono text-[var(--text-muted)]">LIVE DATA</span>
             </div>

             <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                   <thead>
                      <tr className="border-b border-[var(--border-glass)]">
                         <th className="pb-4 text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Symbol</th>
                         <th className="pb-4 text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Price (INR)</th>
                         <th className="pb-4 text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Signal</th>
                         <th className="pb-4 text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Confidence</th>
                         <th className="pb-4 text-right text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">Link</th>
                      </tr>
                   </thead>
                   <tbody>
                      {loading ? (
                         <tr><td colSpan={5} className="py-20 text-center text-xs font-mono animate-pulse">Synchronizing Neural Data Stream...</td></tr>
                      ) : (
                        recs.map((r, i) => (
                           <tr key={r.symbol} className="border-b border-[var(--border-glass)] hover:bg-white/5 transition-colors group">
                              <td className="py-4 font-mono font-bold text-white text-sm">{r.symbol.replace('.NS', '')}</td>
                              <td className="py-4 font-mono text-sm text-[var(--text-secondary)]">{Number(r.last_price).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                              <td className="py-4">
                                 <span className={`text-[10px] font-black px-2 py-0.5 rounded border ${
                                    r.recommendation === 'BUY' ? 'text-[var(--status-buy)] border-[var(--status-buy)]/30' : 
                                    r.recommendation === 'SELL' ? 'text-[var(--status-sell)] border-[var(--status-sell)]/30' : 
                                    'text-[var(--status-hold)] border-[var(--status-hold)]/30'
                                 }`}>
                                    {r.recommendation}
                                 </span>
                              </td>
                              <td className="py-4">
                                 <div className="w-24 h-1 bg-[var(--bg-deep)] rounded-full overflow-hidden">
                                    <div className="h-full bg-[var(--primary-glow)] opacity-80" style={{ width: `${r.confidence * 100}%` }}></div>
                                 </div>
                              </td>
                              <td className="py-4 text-right">
                                 <Link href={`/company/${r.symbol}`} className="text-[10px] font-bold text-[var(--text-muted)] group-hover:text-[var(--primary-glow)] transition-colors">VIEW DETAILS</Link>
                              </td>
                           </tr>
                        ))
                      )}
                   </tbody>
                </table>
             </div>
          </div>

        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[var(--bg-deep)] text-white font-sans selection:bg-[var(--primary-glow)] selection:text-black">
      <section className="relative h-screen flex items-center justify-center overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-[#0c111a] via-transparent to-[#05070a] z-10"></div>
        <div className="absolute inset-0 opacity-20 z-0">
           <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--primary-glow)_0%,_transparent_70%)] blur-[100px]"></div>
        </div>

        <div className="container mx-auto px-6 text-center relative z-20 space-y-8 max-w-4xl">
           <div className="inline-flex items-center gap-3 px-4 py-2 rounded-full border border-[var(--border-glass)] bg-[var(--bg-glass)] text-[10px] font-mono tracking-widest text-[var(--primary-glow)] uppercase">
              <div className="h-1 w-1 rounded-full bg-[var(--primary-glow)] animate-pulse"></div>
              AI signal engine active
           </div>

           <h1 className="text-6xl md:text-8xl font-black tracking-tighter leading-none italic uppercase">
              Precision <span className="text-transparent bg-clip-text bg-gradient-to-r from-white to-[var(--text-muted)]">Alpha</span>
           </h1>

           <p className="text-lg md:text-xl text-[var(--text-secondary)] font-medium max-w-2xl mx-auto leading-relaxed">
              Track AI-driven stock recommendations, portfolio risk, and goal planning in one simple dashboard.
           </p>

           <div className="flex flex-col sm:flex-row items-center justify-center gap-6 pt-6">
              <Link href="/signup" className="w-full sm:w-auto px-10 py-4 rounded-2xl bg-[var(--primary-glow)] text-black font-black uppercase tracking-widest text-sm hover:translate-y-[-2px] active:translate-y-[1px] transition-all shadow-[0_0_30px_rgba(0,255,204,0.2)]">
                 Create Account
              </Link>
              <Link href="/login" className="w-full sm:w-auto px-10 py-4 rounded-2xl border border-[var(--border-glass)] bg-[var(--bg-glass)] text-white font-bold uppercase tracking-widest text-sm hover:bg-white/5 transition-all">
                 Log In
              </Link>
           </div>

           <div className="grid grid-cols-3 gap-10 pt-20">
              <div className="space-y-1">
                 <div className="text-3xl font-black text-white italic">2,200+</div>
                 <div className="text-[10px] font-mono text-[var(--text-muted)] uppercase tracking-wider">Stocks Tracked</div>
              </div>
              <div className="space-y-1">
                 <div className="text-3xl font-black text-[var(--primary-glow)] italic">64.2%</div>
                 <div className="text-[10px] font-mono text-[var(--text-muted)] uppercase tracking-wider">Recent Hit Rate</div>
              </div>
              <div className="space-y-1">
                 <div className="text-3xl font-black text-white italic">0.2ms</div>
                 <div className="text-[10px] font-mono text-[var(--text-muted)] uppercase tracking-wider">Signal Latency</div>
              </div>
           </div>
        </div>
      </section>
    </div>
  )
}
