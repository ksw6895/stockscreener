export interface Stock {
  symbol: string
  name: string
  sector: string
  price: number
  marketCap: number
  peRatio: number
  qualityScore: number
  revenueGrowth?: number
  roe?: number
  beta?: number
  eps?: number
  dividend?: number
  volume?: number
  changePercent?: number
}