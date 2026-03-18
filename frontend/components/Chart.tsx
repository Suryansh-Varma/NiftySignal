import React from 'react'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

type Props = { labels: string[]; data: number[] }
export default function Chart({ labels, data }: Props) {
  const chartData = {
    labels,
    datasets: [
      {
        label: 'Close',
        data,
        fill: false,
        borderColor: '#0366d6',
        tension: 0.1,
      },
    ],
  }
  return <Line data={chartData} />
}
