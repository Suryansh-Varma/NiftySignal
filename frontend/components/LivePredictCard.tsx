import { useState, useRef, useEffect } from 'react';
import { getCompanyName, NIFTY_50 } from '../lib/supabase';

interface Prediction {
  symbol: string;
  last_price: number;
  last_date: string;
  recommendation: string;
  confidence: number;
  buy_prob: number;
  sell_prob: number;
  macro_risk_applied: number;
  is_live: boolean;
  timestamp: string;
}

export default function LivePredictCard() {
  const [symbol, setSymbol] = useState('');
  const [prediction, setPrediction] = useState<Prediction | null>(null);
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Autocomplete states
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const listboxId = 'live-predict-suggestions';

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleInputChange = (val: string) => {
    const upperVal = val.toUpperCase();
    setSymbol(upperVal);
    
    if (upperVal.length > 0) {
      const filtered = NIFTY_50.filter(s => 
        s.replace('.NS', '').startsWith(upperVal) ||
        getCompanyName(s).toUpperCase().startsWith(upperVal) ||
        s.includes(upperVal) ||
        getCompanyName(s).toUpperCase().includes(upperVal)
      ).slice(0, 5);
      setSuggestions(filtered);
      setShowDropdown(true);
      setActiveIndex(filtered.length > 0 ? 0 : -1);
    } else {
      setSuggestions([]);
      setShowDropdown(false);
      setActiveIndex(-1);
    }
  };

  const selectSymbol = (s: string) => {
    setSymbol(s.replace('.NS', ''));
    setShowDropdown(false);
    setActiveIndex(-1);
    inputRef.current?.focus();
  };

  const handleInputKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (!showDropdown || suggestions.length === 0) {
      if (event.key === 'ArrowDown' && suggestions.length > 0) {
        event.preventDefault();
        setShowDropdown(true);
        setActiveIndex(0);
      }
      return;
    }

    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setActiveIndex((prev) => (prev + 1) % suggestions.length);
      return;
    }

    if (event.key === 'ArrowUp') {
      event.preventDefault();
      setActiveIndex((prev) => (prev <= 0 ? suggestions.length - 1 : prev - 1));
      return;
    }

    if (event.key === 'Enter' && activeIndex >= 0) {
      event.preventDefault();
      selectSymbol(suggestions[activeIndex]);
      return;
    }

    if (event.key === 'Escape' || event.key === 'Tab') {
      setShowDropdown(false);
      setActiveIndex(-1);
    }
  };

  const handlePredict = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!symbol) return;
    setShowDropdown(false);
    setActiveIndex(-1);
    
    setLoading(true);
    setScanning(true);
    setError(null);

    // Artificial "Scanning" delay for user experience
    await new Promise(r => setTimeout(r, 1200));

    try {
      const sym = symbol.toUpperCase().includes('.NS') ? symbol.toUpperCase() : `${symbol.toUpperCase()}.NS`;
      const res = await fetch(`/api/predict/${encodeURIComponent(sym)}`);
      if (!res.ok) throw new Error("Instrument not found in operational universe");
      const json = await res.json();
      setPrediction(json);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
      setScanning(false);
    }
  };

  const statusColor = (rec: string) => {
    if (rec === 'BUY') return 'var(--status-buy)';
    if (rec === 'SELL') return 'var(--status-sell)';
    return 'var(--status-hold)';
  };

  return (
    <div className="flex flex-col gap-6 p-8 rounded-3xl border border-[var(--border-glass)] bg-[var(--bg-card)] shadow-2xl relative transition-all duration-700 hover:shadow-[var(--shadow-glow)]">
      
      <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
        <span className="text-4xl font-mono text-[var(--primary-glow)]">LIVE_SCAN</span>
      </div>

      <div className="space-y-4 relative z-20 overflow-visible">
        <div className="flex items-center gap-2">
           <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--primary-glow)" strokeWidth="3"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
           <h3 className="text-[10px] font-bold tracking-[0.3em] uppercase text-[var(--primary-glow)]">Live Stock Lookup</h3>
        </div>
        
        <form onSubmit={handlePredict} className="relative z-30 overflow-visible">
          <div className="flex gap-2 p-1 rounded-2xl bg-[var(--bg-deep)] border border-[var(--border-glass)] shadow-inner">
            <input 
              ref={inputRef}
              type="text" 
              placeholder="Search stock (e.g., RELIANCE)"
              className="flex-1 bg-transparent border-none py-3 px-5 text-[10px] font-mono focus:ring-0 text-slate-100 placeholder-slate-600 uppercase tracking-widest"
              value={symbol}
              onChange={(e) => handleInputChange(e.target.value)}
              onFocus={() => symbol.length > 0 && suggestions.length > 0 && setShowDropdown(true)}
              onKeyDown={handleInputKeyDown}
              role="combobox"
              aria-autocomplete="list"
              aria-expanded={showDropdown && suggestions.length > 0}
              aria-controls={listboxId}
              aria-activedescendant={activeIndex >= 0 ? `live-predict-option-${activeIndex}` : undefined}
            />
            <button 
              type="submit"
              disabled={loading}
              className="bg-[var(--primary-glow)] text-black px-6 py-3 rounded-xl font-black text-[9px] uppercase tracking-[0.2em] hover:brightness-110 active:scale-95 transition-all disabled:opacity-50"
              aria-label="Get stock signal"
            >
              {loading ? "Loading..." : "Get Signal"}
            </button>
          </div>

          {/* Autocomplete Dropdown - Debug Container */}
          {showDropdown && suggestions.length > 0 ? (
            <div
              ref={dropdownRef}
              id={listboxId}
              role="listbox"
              aria-label="Stock suggestions"
              className="absolute top-full left-0 right-0 mt-2 p-2 rounded-2xl bg-[var(--bg-card)] border-2 border-[var(--primary-glow)] shadow-2xl z-50 backdrop-blur-xl overflow-y-auto max-h-64 min-w-max"
              style={{ pointerEvents: 'auto' }}
            >
              {suggestions.map((s, index) => (
                <button
                  key={s}
                  id={`live-predict-option-${index}`}
                  type="button"
                  role="option"
                  aria-selected={activeIndex === index}
                  onClick={() => selectSymbol(s)}
                  onMouseEnter={() => setActiveIndex(index)}
                  className="w-full flex justify-between items-center p-3 rounded-xl hover:bg-white/5 cursor-pointer transition-colors group"
                  style={{
                    background: activeIndex === index ? 'rgba(255, 255, 255, 0.08)' : 'transparent',
                  }}
                >
                  <span className="text-[10px] font-black text-white uppercase tracking-tighter italic">{getCompanyName(s)}</span>
                  <span className="text-[9px] font-mono text-[var(--text-muted)] group-hover:text-[var(--primary-glow)]">{s.replace('.NS', '')}</span>
                </button>
              ))}
            </div>
          ) : null}
        </form>
      </div>

      {scanning && (
        <div className="flex flex-col gap-4 py-8 animate-in">
          <div className="flex items-center gap-3">
            <div className="h-1.5 w-1.5 rounded-full bg-[var(--primary-glow)] animate-ping"></div>
            <span className="text-[8px] font-mono text-[var(--primary-glow)] tracking-widest uppercase animate-pulse">Running Neural Inference // SYNCING_DATA</span>
          </div>
          <div className="h-1 w-full bg-[var(--bg-deep)] rounded-full overflow-hidden">
            <div className="h-full bg-[var(--primary-glow)] animate-[bar-fill_2s_infinite]"></div>
          </div>
        </div>
      )}

      {prediction && !scanning && (
        <div className="flex flex-col gap-6 py-4 animate-in">
          <div className="flex justify-between items-end border-b border-[var(--border-glass)] pb-4">
            <div>
              <h4 className="text-4xl font-black tracking-tighter italic" style={{ color: statusColor(prediction.recommendation) }}>
                {prediction.recommendation}
              </h4>
              <p className="text-[9px] font-mono text-[var(--text-muted)] mt-1 uppercase tracking-widest">Confidence Level: {(prediction.confidence * 100).toFixed(1)}%</p>
            </div>
            <div className="text-right">
              <span className="text-2xl font-black text-white tracking-tighter italic">₹{prediction.last_price.toLocaleString('en-IN')}</span>
              <p className="text-[8px] font-mono text-[var(--text-muted)] tracking-widest">MARKET_VAL</p>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-6">
            <div className="flex flex-col gap-2">
              <span className="text-[9px] font-bold text-[var(--text-muted)] uppercase tracking-[0.2em]">Alpha_Prob</span>
              <div className="h-20 w-full rounded-2xl bg-[var(--bg-deep)] relative overflow-hidden flex items-end">
                <div 
                  className="w-full bg-[var(--status-buy)] transition-all duration-1000 opacity-80" 
                  style={{ height: `${prediction.buy_prob * 100}%` }}
                ></div>
                <span className="absolute top-2 left-2 text-[8px] font-mono text-white tracking-widest">UPWARDS</span>
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <span className="text-[9px] font-bold text-[var(--text-muted)] uppercase tracking-[0.2em]">Stable_Prob</span>
              <div className="h-20 w-full rounded-2xl bg-[var(--bg-deep)] relative overflow-hidden flex items-end">
                <div 
                  className="w-full bg-[var(--status-hold)] transition-all duration-1000 opacity-80" 
                  style={{ height: `${(1 - prediction.buy_prob - prediction.sell_prob) * 100}%` }}
                ></div>
                <span className="absolute top-2 left-2 text-[8px] font-mono text-white tracking-widest">NEUTRAL</span>
              </div>
            </div>
            <div className="flex flex-col gap-2">
              <span className="text-[9px] font-bold text-[var(--text-muted)] uppercase tracking-[0.2em]">Down_Prob</span>
              <div className="h-20 w-full rounded-2xl bg-[var(--bg-deep)] relative overflow-hidden flex items-end">
                <div 
                  className="w-full bg-[var(--status-sell)] transition-all duration-1000 opacity-80" 
                  style={{ height: `${prediction.sell_prob * 100}%` }}
                ></div>
                <span className="absolute top-2 left-2 text-[8px] font-mono text-white tracking-widest">DOWNSIDE</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-[var(--border-glass)] w-fit border border-[var(--border-glass)]">
             <div className="h-1.5 w-1.5 rounded-full bg-[var(--primary-glow)]"></div>
             <span className="text-[8px] font-mono text-[var(--text-secondary)] uppercase tracking-widest">Risk Adjusted // Factor: {prediction.macro_risk_applied.toFixed(2)} applied</span>
          </div>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-xl bg-red-900/10 border border-red-500/30 text-red-500 text-[10px] font-mono uppercase tracking-widest">
           System_Error: {error}
        </div>
      )}

      <style jsx>{`
        @keyframes bar-fill {
            0% { width: 0%; margin-left: 0; }
            50% { width: 70%; margin-left: 15%; }
            100% { width: 0%; margin-left: 100%; }
        }
      `}</style>
    </div>
  );
}
