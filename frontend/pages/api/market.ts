import type { NextApiRequest, NextApiResponse } from 'next'

const API_URL = process.env.BACKEND_API_URL || 'http://localhost:8000'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  try {
    // Fetch market trend from backend
    const trendRes = await fetch(`${API_URL}/api/market_trend`)
    const trendData = trendRes.ok ? await trendRes.json() : { labels: [], values: [] }

    // Fetch risk assessment from backend
    const riskRes = await fetch(`${API_URL}/api/market_risk`)
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
