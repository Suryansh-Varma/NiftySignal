import type { NextApiRequest, NextApiResponse } from 'next'
import fs from 'fs'
import path from 'path'
import Papa from 'papaparse'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  try {
    const csvPath = path.join(process.cwd(), '..', 'data', 'processed', 'universe_data.csv')
    // Prefer results CSV if exists
    const resultsPath = path.join(process.cwd(), '..', 'results', 'latest_recommendations.csv')

    if (fs.existsSync(resultsPath)) {
      const csv = fs.readFileSync(resultsPath, 'utf8')
      const parsed = Papa.parse(csv, { header: true, dynamicTyping: true })
      return res.status(200).json(parsed.data)
    }

    // Fallback: produce aggregated hold recommendations if no results file
    if (fs.existsSync(csvPath)) {
      const csv = fs.readFileSync(csvPath, 'utf8')
      const parsed = Papa.parse(csv, { header: true, dynamicTyping: true })
      const latest = (parsed.data as any[])
        .filter(Boolean)
        .sort((a,b) => (new Date(a.date).getTime()) - (new Date(b.date).getTime()))
      const grouped: Record<string, any> = {}
      latest.forEach(r => { grouped[r.symbol] = r })
      const arr = Object.values(grouped).map(r => ({ symbol: r.symbol, last_price: r.close, last_date: r.date, signal: 0, confidence: 0.5, recommendation: 'HOLD' }))
      return res.status(200).json(arr)
    }

    return res.status(404).json({ error: 'No data files found' })
  } catch (err) {
    console.error(err)
    res.status(500).json({ error: 'Failed to read recommendations' })
  }
}
