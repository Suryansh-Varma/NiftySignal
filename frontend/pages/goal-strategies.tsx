import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

type StrategyType = 'conservative' | 'moderate' | 'aggressive';

interface Recommendation {
  symbol: string;
  date: string;
  close: number;
  buy_prob: number;
  confidence: number;
  weight: number;
  allocation_inr: number | string;
}

interface Strategy {
  name: string;
  target_return: string;
  horizon: string;
  description: string;
  risk_level: string;
}

const formatINR = (value: number | string): string => {
  if (typeof value === 'string') return value;
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value);
};

const formatPct = (value: number): string => `${value.toFixed(1)}%`;

const getRiskClass = (risk: string) => {
  switch (risk) {
    case 'Low': return 'pill pill-green';
    case 'Medium': return 'pill pill-yellow';
    case 'High': return 'pill pill-red';
    default: return 'pill';
  }
};

const getConfidenceClass = (confidence: number) => {
  if (confidence >= 60) return 'muted';
  if (confidence >= 40) return 'muted';
  return 'muted';
};

export default function GoalStrategiesPage() {
  const [strategies, setStrategies] = useState<Record<string, Strategy>>({});
  const [selectedStrategy, setSelectedStrategy] = useState<StrategyType>('aggressive');
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [capital, setCapital] = useState<number>(1200000);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [best, setBest] = useState<{ recommended?: StrategyType; evaluations?: any; generated_at?: string } | null>(null);
  const [bestLoading, setBestLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchStrategies = async () => {
      try {
        const res = await axios.get(`${API_BASE}/api/goal_strategies`);
        setStrategies(res.data);
      } catch (err) {
        console.error('Failed to fetch strategies:', err);
      }
    };
    fetchStrategies();
  }, []);

  useEffect(() => {
    const fetchBest = async () => {
      setBestLoading(true);
      try {
        const res = await axios.get(`${API_BASE}/api/goal_best`);
        setBest(res.data);
      } catch (err) {
        console.error('Failed to fetch best strategy:', err);
      } finally {
        setBestLoading(false);
      }
    };
    fetchBest();
  }, []);

  useEffect(() => {
    const fetchRecommendations = async () => {
      setLoading(true);
      setError(null);
      try {
        const res = await axios.get(`${API_BASE}/api/goal_recommendations/${selectedStrategy}`);
        setRecommendations(res.data);
      } catch (err) {
        setError(`Failed to load ${selectedStrategy} recommendations. Please train the model first.`);
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchRecommendations();
  }, [selectedStrategy]);

  const computedRecs = recommendations.map((rec) => ({
    ...rec,
    allocationComputed: rec.weight * capital
  }));
  const totalAllocation = computedRecs.reduce((sum, rec) => sum + (rec.allocationComputed || 0), 0);

  return (
    <div className="container">
      <div className="card section" style={{ marginBottom: 16 }}>
        <h2>Recommended Approach</h2>
        {bestLoading ? (
          <p className="muted">Evaluating strategies...</p>
        ) : best?.recommended ? (
          <div className="row space-between">
            <div>
              <p className="muted">Based on expected return and confidence</p>
              <div style={{ fontSize: 18, fontWeight: 700 }}>
                {strategies[best.recommended]?.name} ({best.recommended})
              </div>
            </div>
            <div className="row" style={{ gap: 12 }}>
              <button className="btn btn-primary" onClick={() => setSelectedStrategy(best!.recommended as StrategyType)}>
                View Best Recommendations
              </button>
            </div>
          </div>
        ) : (
          <p className="muted">No recommended strategy available yet. Train models first.</p>
        )}
      </div>
      <div className="section">
        <h1>Goal-Based Investment Strategies</h1>
        <p className="muted">Choose your investment goal and capital; allocations recompute live.</p>
      </div>

      <div className="grid grid-3 section">
        {Object.entries(strategies).map(([key, strategy]) => (
          <button
            key={key}
            onClick={() => setSelectedStrategy(key as StrategyType)}
            className={selectedStrategy === key ? 'strategy-card strategy-card--active' : 'strategy-card'}
          >
            <div>
              <h3>{strategy.name}</h3>
              <div className={getRiskClass(strategy.risk_level)} style={{ marginBottom: 8 }}>{strategy.risk_level} Risk</div>
              <div>
                <p><strong>Target:</strong> {strategy.target_return}</p>
                <p><strong>Horizon:</strong> {strategy.horizon}</p>
                <p className="muted" style={{ fontSize: 13, marginTop: 8 }}>{strategy.description}</p>
              </div>
            </div>
          </button>
        ))}
      </div>

      <div className="card">
        <div className="row space-between" style={{ marginBottom: 16 }}>
          <h2>{strategies[selectedStrategy]?.name} Strategy Recommendations</h2>
          <div className="row" style={{ gap: 16 }}>
            <div className="row">
              <label htmlFor="capital" className="muted">Investment</label>
              <input id="capital" type="number" className="input" min={100000} step={10000} value={capital}
                onChange={(e) => setCapital(Math.max(0, Number(e.target.value) || 0))} />
            </div>
            <div className="text-right">
              <div className="muted" style={{ fontSize: 12 }}>Total Allocation</div>
              <div style={{ fontWeight: 700 }}>{formatINR(totalAllocation)}</div>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="muted">Loading recommendations...</div>
        ) : error ? (
          <div className="card" style={{ border: '1px solid #fee2e2', background: '#fff1f2' }}>
            <p style={{ color: '#7f1d1d' }}>{error}</p>
          </div>
        ) : computedRecs.length === 0 ? (
          <div className="muted">No recommendations available for this strategy.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="table">
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>Symbol</th>
                  <th className="text-right">Price</th>
                  <th className="text-right">Confidence</th>
                  <th className="text-right">Weight</th>
                  <th className="text-right">Allocation</th>
                </tr>
              </thead>
              <tbody>
                {computedRecs.map((rec, idx) => (
                  <tr key={idx}>
                    <td>{idx + 1}</td>
                    <td><strong style={{ color: '#4338ca' }}>{rec.symbol.replace('.NS', '')}</strong></td>
                    <td className="text-right">{formatINR(rec.close)}</td>
                    <td className={`text-right ${getConfidenceClass(rec.confidence)}`}>{formatPct(rec.confidence)}</td>
                    <td className="text-right">{formatPct(rec.weight * 100)}</td>
                    <td className="text-right" style={{ fontWeight: 700 }}>{formatINR(rec.allocationComputed || 0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {!loading && !error && computedRecs.length > 0 && (
        <div className="card section">
          <h3>Investment Timeline</h3>
          <div className="grid grid-3">
            <div className="card">
              <div className="muted">Invest Today</div>
              <div style={{ fontWeight: 700 }}>{new Date().toLocaleDateString('en-IN')}</div>
            </div>
            <div className="card">
              <div className="muted">Expected Horizon</div>
              <div style={{ fontWeight: 700 }}>{strategies[selectedStrategy]?.horizon}</div>
            </div>
            <div className="card">
              <div className="muted">Target Return</div>
              <div style={{ fontWeight: 700 }}>{strategies[selectedStrategy]?.target_return}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
