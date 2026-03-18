import React from 'react'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
} from 'chart.js'
import { Line } from 'react-chartjs-2'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend)

export default function TrendChart({ labels, data, title }: { labels: string[]; data: number[]; title?: string }) {
  const chartData = {
    labels,
    datasets: [
      {
        label: title || 'Trend',
        data,
        borderColor: '#4f46e5',
        backgroundColor: 'rgba(79,70,229,0.08)',
        tension: 0.25,
        pointRadius: 0,
      },
    ],
  }

  const options = {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: { x: { display: false }, y: { display: true } },
  }

  return (
    <div style={{ padding: '0.5rem' }}>
      <h3 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--slate-700)', marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--primary-500)', boxShadow: '0 0 8px var(--primary-500)' }}></span>
        {title || 'Market Trend'}
      </h3>
      <div className="skeuo-recessed" style={{ height: 180, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
        <Line data={chartData} options={options as any} />
      </div>
    </div>
  )
}
