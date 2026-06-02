import { useState, useEffect } from 'react';

interface RiskData {
  risk_score: number;
  risk_level: string;
  update_date: string;
}

export default function MarketRiskPulse() {
  const [data, setData] = useState<RiskData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRisk = async () => {
      try {
        const res = await fetch('/api/market-risk');
        if (!res.ok) throw new Error('Failed to load market risk');
        const json = await res.json();
        setData(json);
      } catch (err) {
        console.error("Failed to fetch risk:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchRisk();
    const interval = setInterval(fetchRisk, 60000); // Check every minute
    return () => clearInterval(interval);
  }, []);

  if (loading) return (
    <div className="animate-pulse h-24 w-full bg-slate-800 rounded-lg border border-slate-700"></div>
  );

  const risk = data?.risk_score || 0.5;
  const level = data?.risk_level || "UNKNOWN";
  
  // Color mapping based on status
  const getColor = () => {
    if (risk < 0.3) return "var(--status-buy)";
    if (risk < 0.6) return "var(--accent-blue)";
    if (risk < 0.8) return "var(--status-extreme)";
    return "var(--status-sell)";
  };

  return (
    <div className="relative group overflow-hidden p-6 rounded-2xl border border-[var(--border-glass)] bg-[var(--bg-glass)] backdrop-blur-xl shadow-2xl transition-all duration-500 hover:border-[var(--border-glow)] hover:shadow-[var(--shadow-glow)]">
      {/* Background Glow */}
      <div 
        className="absolute -top-10 -right-10 w-32 h-32 blur-3xl opacity-20 pointer-events-none transition-colors duration-1000"
        style={{ backgroundColor: getColor() }}
      ></div>

      <div className="flex items-center justify-between relative z-10">
        <div className="flex flex-col gap-1">
          <span className="text-xs font-bold uppercase tracking-widest text-[var(--text-muted)]">Market Pulse</span>
          <div className="flex items-baseline gap-2">
            <h2 className="text-3xl font-black tracking-tighter" style={{ color: getColor() }}>
              {(risk * 100).toFixed(0)}%
            </h2>
            <span className="text-sm font-bold text-[var(--text-secondary)]">{level}</span>
          </div>
          <p className="text-[10px] font-mono text-[var(--text-muted)] mt-1">
            Last update: {data?.update_date?.split(' ')[1] || "Live"}
          </p>
        </div>

        {/* Circular Gauge */}
        <div className="relative w-16 h-16 flex items-center justify-center">
            <svg className="w-full h-full -rotate-90">
                <circle
                    cx="32" cy="32" r="28"
                    stroke="rgba(255,255,255,0.05)"
                    strokeWidth="4"
                    fill="transparent"
                />
                <circle
                    cx="32" cy="32" r="28"
                    stroke={getColor()}
                    strokeWidth="4"
                    fill="transparent"
                    strokeDasharray={175}
                    strokeDashoffset={175 - (175 * risk)}
                    strokeLinecap="round"
                    className="transition-all duration-1000 ease-out"
                />
            </svg>
            <div className="absolute w-2 h-2 rounded-full animate-ping" style={{ backgroundColor: getColor() }}></div>
        </div>
      </div>
      
      {/* Decorative dots */}
      <div className="flex gap-1 mt-4">
        {[1,2,3,4,5].map(i => (
            <div key={i} className={`h-1 w-4 rounded-full ${i <= risk*5 ? '' : 'opacity-10'}`} style={{ backgroundColor: getColor() }}></div>
        ))}
      </div>
    </div>
  );
}
