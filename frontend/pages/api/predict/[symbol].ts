import type { NextApiRequest, NextApiResponse } from 'next'
import { getServerApiBase, buildApiUrl } from '../../../lib/api-base'

const API_URL = getServerApiBase()

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  try {
    const rawSymbol = req.query.symbol
    const symbol = Array.isArray(rawSymbol) ? rawSymbol[0] : rawSymbol

    if (!symbol) {
      return res.status(400).json({ error: 'Missing symbol' })
    }

    const response = await fetch(buildApiUrl(API_URL, `/api/predict/${encodeURIComponent(symbol)}`))
    const text = await response.text()

    if (!response.ok) {
      return res.status(response.status).json({ error: text || 'Prediction failed' })
    }

    try {
      const payload = JSON.parse(text)
      return res.status(200).json(payload)
    } catch {
      return res.status(500).json({ error: 'Invalid backend response' })
    }
  } catch (error) {
    console.error('Prediction proxy failed:', error)
    return res.status(500).json({ error: 'Prediction request failed' })
  }
}
