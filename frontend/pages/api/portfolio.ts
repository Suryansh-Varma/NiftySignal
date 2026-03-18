import type { NextApiRequest, NextApiResponse } from 'next'

export default function handler(req: NextApiRequest, res: NextApiResponse) {
  // Portfolio is managed via Supabase in the portfolio page
  // This API returns empty data - users should add stocks via /portfolio
  res.status(200).json({ positions: [], intraday: {} })
}
