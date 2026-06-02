import type { NextApiRequest, NextApiResponse } from 'next'
import fs from 'fs'
import path from 'path'
import Papa from 'papaparse'

type RecommendationRow = {
  symbol: string
  last_price: number
  last_date: string
  recommendation: 'BUY' | 'SELL' | 'HOLD'
  confidence: number
  buy_prob: number
  sell_prob: number
  risk_score: number
}

function normalizeSymbol(raw?: string): string {
  if (!raw) return ''
  const upper = String(raw).trim().toUpperCase()
  return upper.endsWith('.NS') ? upper : `${upper}.NS`
}

function toNumber(value: any, fallback = 0): number {
  const n = Number(value)
  return Number.isFinite(n) ? n : fallback
}

function toOptionalNumber(value: any): number {
  const n = Number(value)
  return Number.isFinite(n) ? n : NaN
}

function normalizeConfidence(value: any): number {
  const c = toNumber(value, 0)
  if (c > 1) return Math.min(1, c / 100)
  return Math.max(0, Math.min(1, c))
}

function normalizeRiskScore(value: any, confidence: number): number {
  const raw = toOptionalNumber(value)
  if (Number.isFinite(raw)) {
    if (raw > 1) return Math.max(0, Math.min(1, raw / 100))
    return Math.max(0, Math.min(1, raw))
  }
  return Math.max(0, Math.min(1, 1 - confidence))
}

function normalizeRecommendation(value: any): 'BUY' | 'SELL' | 'HOLD' {
  const rec = String(value || '').toUpperCase()
  if (rec === 'BUY' || rec === 'SELL' || rec === 'HOLD') return rec
  return 'HOLD'
}

function fromSignal(signal: any): 'BUY' | 'SELL' | 'HOLD' {
  const n = toNumber(signal, 0)
  if (n > 0) return 'BUY'
  if (n < 0) return 'SELL'
  return 'HOLD'
}

function normalizeRow(row: any): RecommendationRow | null {
  const symbol = normalizeSymbol(row?.symbol)
  if (!symbol) return null

  const recommendation = normalizeRecommendation(row?.recommendation || fromSignal(row?.signal))
  const confidence = normalizeConfidence(row?.confidence)

  let buyProb = toNumber(row?.buy_prob, NaN)
  let sellProb = toNumber(row?.sell_prob, NaN)
  const riskScore = normalizeRiskScore(
    row?.risk_score ?? row?.adjusted_risk_factor ?? row?.macro_risk_factor ?? row?.risk_factor,
    confidence
  )

  if (!Number.isFinite(buyProb) || !Number.isFinite(sellProb)) {
    if (recommendation === 'BUY') {
      buyProb = Math.max(0.5, confidence)
      sellProb = Math.max(0, 1 - buyProb)
    } else if (recommendation === 'SELL') {
      sellProb = Math.max(0.5, confidence)
      buyProb = Math.max(0, 1 - sellProb)
    } else {
      buyProb = Math.max(0, (1 - confidence) / 2)
      sellProb = Math.max(0, (1 - confidence) / 2)
    }
  }

  return {
    symbol,
    last_price: toNumber(row?.last_price ?? row?.close, 0),
    last_date: String(row?.last_date ?? row?.date ?? ''),
    recommendation,
    confidence,
    buy_prob: Math.max(0, Math.min(1, buyProb)),
    sell_prob: Math.max(0, Math.min(1, sellProb)),
    risk_score: riskScore,
  }
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  try {
    const requestedSymbol = normalizeSymbol(typeof req.query.symbol === 'string' ? req.query.symbol : '')
    const csvPath = path.join(process.cwd(), '..', 'data', 'processed', 'universe_data.csv')
    // Prefer results CSV if exists
    const resultsPath = path.join(process.cwd(), '..', 'results', 'latest_recommendations.csv')

    if (fs.existsSync(resultsPath)) {
      const csv = fs.readFileSync(resultsPath, 'utf8')
      const parsed = Papa.parse(csv, { header: true, dynamicTyping: true })
      const rows = (parsed.data as any[])
        .map(normalizeRow)
        .filter((r): r is RecommendationRow => Boolean(r))

      if (requestedSymbol) {
        const match = rows.find((r) => r.symbol === requestedSymbol)
        return res.status(200).json(match ? [match] : [])
      }

      return res.status(200).json(rows)
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
      const arr = Object.values(grouped)
        .map((r) => normalizeRow({ symbol: r.symbol, last_price: r.close, last_date: r.date, signal: 0, confidence: 0.5, recommendation: 'HOLD' }))
        .filter((r): r is RecommendationRow => Boolean(r))

      if (requestedSymbol) {
        const match = arr.find((r) => r.symbol === requestedSymbol)
        return res.status(200).json(match ? [match] : [])
      }

      return res.status(200).json(arr)
    }

    return res.status(404).json({ error: 'No data files found' })
  } catch (err) {
    console.error(err)
    res.status(500).json({ error: 'Failed to read recommendations' })
  }
}
