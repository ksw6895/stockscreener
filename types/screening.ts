export interface ScreeningCriteria {
  minMarketCap?: number | null
  maxMarketCap?: number | null
  minPE?: number | null
  maxPE?: number | null
  minROE?: number | null
  minRevenueGrowth?: number | null
  sectors: string[]
  minQualityScore?: number | null
}

export interface ScreeningJob {
  jobId: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  startedAt: string
  completedAt?: string
  error?: string
}