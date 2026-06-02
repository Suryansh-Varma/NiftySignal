import type { NextApiRequest, NextApiResponse } from 'next'
import { getServerApiBase, buildApiUrl } from '../../lib/api-base'

const API_URL = getServerApiBase()

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  try {
    const response = await fetch(buildApiUrl(API_URL, '/api/market_risk'))
    if (!response.ok) {
      return res.status(response.status).json({ error: 'Failed to fetch market risk' })
    }

    const payload = await response.json()
    return res.status(200).json(payload)
  } catch (error) {
    console.error('Market risk proxy failed:', error)
    return res.status(200).json({
      risk_score: 0.5,
      risk_level: 'UNKNOWN',
      update_date: null,
    })
  }
}
