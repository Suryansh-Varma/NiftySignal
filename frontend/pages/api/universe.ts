import type { NextApiRequest, NextApiResponse } from 'next'
import fs from 'fs'
import path from 'path'
import Papa from 'papaparse'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  try {
    const { symbol } = req.query
    const csvPath = path.join(process.cwd(), '..', 'data', 'processed', 'universe_data.csv')
    if (!fs.existsSync(csvPath)) return res.status(404).json({ error: 'universe CSV not found' })
    const csv = fs.readFileSync(csvPath, 'utf8')
    const parsed = Papa.parse(csv, { header: true, dynamicTyping: true })
    const rows = (parsed.data as any[]).filter(Boolean)
    if (symbol) {
      const sym = String(symbol)
      const filtered = rows.filter(r => r.symbol === sym)
      return res.status(200).json(filtered)
    }
    return res.status(200).json(rows)
  } catch (err) {
    console.error(err)
    res.status(500).json({ error: 'Failed to read universe CSV' })
  }
}
