'use client'

import { useState, useEffect } from 'react'
import StockTable from './StockTable'
import FilterPanel from './FilterPanel'
import StatsCard from './StatsCard'
import { Stock } from '@/types/stock'
import { ScreeningCriteria } from '@/types/screening'

export default function Dashboard() {
  const [stocks, setStocks] = useState<Stock[]>([])
  const [loading, setLoading] = useState(false)
  const [jobId, setJobId] = useState<string | null>(null)
  const [progress, setProgress] = useState(0)
  const [stats, setStats] = useState({
    totalStocks: 0,
    avgQualityScore: 0,
    topSector: '',
    avgPE: 0
  })

  const startScreening = async (criteria: ScreeningCriteria) => {
    setLoading(true)
    setProgress(0)
    
    try {
      const response = await fetch('/api/screening/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(criteria)
      })
      
      const data = await response.json()
      setJobId(data.jobId)
      pollStatus(data.jobId)
    } catch (error) {
      console.error('Failed to start screening:', error)
      setLoading(false)
    }
  }

  const pollStatus = async (id: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`/api/screening/status?jobId=${id}`)
        const data = await response.json()
        
        setProgress(data.progress)
        
        if (data.status === 'completed') {
          clearInterval(interval)
          fetchResults(id)
        } else if (data.status === 'failed') {
          clearInterval(interval)
          setLoading(false)
          console.error('Screening failed')
        }
      } catch (error) {
        clearInterval(interval)
        setLoading(false)
        console.error('Failed to poll status:', error)
      }
    }, 2000)
  }

  const fetchResults = async (id: string) => {
    try {
      const response = await fetch(`/api/screening/results?jobId=${id}`)
      const data = await response.json()
      
      setStocks(data.stocks)
      calculateStats(data.stocks)
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch results:', error)
      setLoading(false)
    }
  }

  const calculateStats = (stockList: Stock[]) => {
    if (stockList.length === 0) return
    
    const avgQuality = stockList.reduce((sum, s) => sum + (s.qualityScore || 0), 0) / stockList.length
    const avgPERatio = stockList.reduce((sum, s) => sum + (s.peRatio || 0), 0) / stockList.length
    
    const sectorCounts = stockList.reduce((acc, s) => {
      acc[s.sector] = (acc[s.sector] || 0) + 1
      return acc
    }, {} as Record<string, number>)
    
    const topSector = Object.entries(sectorCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || ''
    
    setStats({
      totalStocks: stockList.length,
      avgQualityScore: avgQuality,
      topSector,
      avgPE: avgPERatio
    })
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Stock Screener Pro
          </h1>
          <p className="text-gray-600">
            Advanced NASDAQ stock analysis powered by AI
          </p>
        </header>

        {loading && (
          <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-blue-700">
                Screening in progress...
              </span>
              <span className="text-sm text-blue-600">{progress}%</span>
            </div>
            <div className="w-full bg-blue-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <StatsCard
            title="Total Stocks"
            value={stats.totalStocks}
            icon="📊"
            color="blue"
          />
          <StatsCard
            title="Avg Quality Score"
            value={stats.avgQualityScore.toFixed(1)}
            icon="⭐"
            color="green"
          />
          <StatsCard
            title="Top Sector"
            value={stats.topSector}
            icon="🏆"
            color="purple"
          />
          <StatsCard
            title="Avg P/E Ratio"
            value={stats.avgPE.toFixed(1)}
            icon="💰"
            color="yellow"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <FilterPanel onApplyFilters={startScreening} loading={loading} />
          </div>
          
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-bold mb-4">Screening Results</h2>
              <StockTable stocks={stocks} loading={loading} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}