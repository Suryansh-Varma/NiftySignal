import type { NextApiRequest, NextApiResponse } from 'next'
import fs from 'fs'
import path from 'path'
import Papa from 'papaparse'
import { getServerApiBase, buildApiUrl } from '../../lib/api-base'

const API_URL = getServerApiBase()

function buildTrendFromUniverse(days = 30): { labels: string[]; values: number[] } {
  const csvPath = path.join(process.cwd(), '..', 'data', 'processed', 'universe_data.csv')
  if (!fs.existsSync(csvPath)) {
    return { labels: [], values: [] }
  }

  const csv = fs.readFileSync(csvPath, 'utf8')
  const parsed = Papa.parse(csv, { header: true, dynamicTyping: true })
  const rows = (parsed.data as any[]).filter(Boolean)

  const byDate: Record<string, { total: number; count: number }> = {}

  rows.forEach((row) => {
    const date = String(row?.date || '')
    const close = Number(row?.close)
    if (!date || !Number.isFinite(close)) return

    if (!byDate[date]) byDate[date] = { total: 0, count: 0 }
    byDate[date].total += close
    byDate[date].count += 1
  })

  const points = Object.entries(byDate)
    .map(([date, bucket]) => ({
      date,
      value: bucket.count ? bucket.total / bucket.count : NaN,
    }))
    .filter((p) => Number.isFinite(p.value))
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
    .slice(-days)

  return {
    labels: points.map((p) => p.date),
    values: points.map((p) => Number(p.value.toFixed(2))),
  }
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  try {
    const trendData = buildTrendFromUniverse(30)

    // Fetch risk assessment from backend
    const riskRes = await fetch(buildApiUrl(API_URL, '/api/market_risk'))
    const riskData = riskRes.ok ? await riskRes.json() : { risk_score: 0.5, factors: [] }

    res.status(200).json({
      trend: {
        labels: trendData.labels || [],
        values: trendData.values || []
      },
      riskScore: riskData.risk_score || 0.5,
      riskLevel: riskData.risk_level || 'MODERATE',
      factors: riskData.factors || [],
      updateDate: riskData.update_date || null
    })
  } catch (error) {
    console.error('Failed to fetch market data:', error)
    // Return empty data instead of mock data
    res.status(200).json({
      trend: { labels: [], values: [] },
      riskScore: 0.5,
      riskLevel: 'MODERATE',
      factors: [],
      updateDate: null
    })
  }
}
