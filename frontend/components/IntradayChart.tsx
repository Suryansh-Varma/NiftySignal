import React from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Filler,
} from 'chart.js'
import { Line } from 'react-chartjs-2'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Filler)

export default function IntradayChart({ labels, data }: { labels: string[]; data: number[] }) {
  const chartData = {
    labels,
    datasets: [
      {
        label: 'Intraday Velocity',
        data,
        borderColor: 'var(--slate-800)',
        backgroundColor: 'rgba(0, 0, 0, 0.03)',
        fill: true,
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 4,
        borderWidth: 2,
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        mode: 'index',
        intersect: false,
        backgroundColor: 'rgba(0, 0, 0, 0.9)',
        titleFont: { weight: 'bold' },
        padding: 12,
        cornerRadius: 8,
      }
    },
    scales: {
      x: { display: false },
      y: {
        display: true,
        grid: { color: 'rgba(0,0,0,0.03)' },
        ticks: { font: { size: 10, weight: 'bold' }, color: 'var(--slate-400)' }
      }
    }
  }

  return (
    <div style={{ padding: '0.5rem' }}>
      <div className="flex justify-between items-center" style={{ marginBottom: '1rem' }}>
        <h4 style={{ margin: 0, fontSize: '0.75rem', fontWeight: 900, color: 'var(--slate-500)', textTransform: 'uppercase', letterSpacing: '0.1em', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span className="skeuo-knob" style={{ width: '8px', height: '8px', background: 'var(--accent-500)' }}></span>
          Intraday Pulse
        </h4>
        <span style={{ fontSize: '0.7rem', fontWeight: 800, color: 'var(--accent-600)', fontFamily: 'var(--font-mono)' }}>LIVE FEED</span>
      </div>
      <div className="skeuo-recessed" style={{ height: 180, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
        <Line data={chartData} options={options as any} />
      </div>
    </div>
  )
}
