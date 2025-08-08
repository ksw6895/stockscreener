'use client'

import { useState } from 'react'
import { ScreeningCriteria } from '@/types/screening'

interface FilterPanelProps {
  onApplyFilters: (criteria: ScreeningCriteria) => void
  loading?: boolean
}

export default function FilterPanel({ onApplyFilters, loading }: FilterPanelProps) {
  const [criteria, setCriteria] = useState<ScreeningCriteria>({
    minMarketCap: 1000000000,
    maxMarketCap: null,
    minPE: null,
    maxPE: 50,
    minROE: 10,
    minRevenueGrowth: 5,
    sectors: [],
    minQualityScore: 60
  })

  const sectors = [
    'Technology',
    'Healthcare',
    'Financial Services',
    'Consumer Cyclical',
    'Communication Services',
    'Industrials',
    'Consumer Defensive',
    'Energy',
    'Utilities',
    'Real Estate',
    'Basic Materials'
  ]

  const handleSectorToggle = (sector: string) => {
    setCriteria(prev => ({
      ...prev,
      sectors: prev.sectors.includes(sector)
        ? prev.sectors.filter(s => s !== sector)
        : [...prev.sectors, sector]
    }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onApplyFilters(criteria)
  }

  return (
    <form onSubmit={handleSubmit} className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-xl font-bold mb-4">Screening Filters</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Min Market Cap (B)
          </label>
          <input
            type="number"
            value={(criteria.minMarketCap || 0) / 1e9}
            onChange={(e) => setCriteria(prev => ({ ...prev, minMarketCap: parseFloat(e.target.value) * 1e9 }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Max P/E Ratio
          </label>
          <input
            type="number"
            value={criteria.maxPE || ''}
            onChange={(e) => setCriteria(prev => ({ ...prev, maxPE: e.target.value ? parseFloat(e.target.value) : null }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Min ROE (%)
          </label>
          <input
            type="number"
            value={criteria.minROE || ''}
            onChange={(e) => setCriteria(prev => ({ ...prev, minROE: e.target.value ? parseFloat(e.target.value) : null }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Min Revenue Growth (%)
          </label>
          <input
            type="number"
            value={criteria.minRevenueGrowth || ''}
            onChange={(e) => setCriteria(prev => ({ ...prev, minRevenueGrowth: e.target.value ? parseFloat(e.target.value) : null }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Min Quality Score
          </label>
          <input
            type="number"
            value={criteria.minQualityScore || ''}
            onChange={(e) => setCriteria(prev => ({ ...prev, minQualityScore: e.target.value ? parseFloat(e.target.value) : null }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
            min="0"
            max="100"
          />
        </div>
      </div>
      
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Sectors
        </label>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {sectors.map(sector => (
            <label key={sector} className="flex items-center">
              <input
                type="checkbox"
                checked={criteria.sectors.includes(sector)}
                onChange={() => handleSectorToggle(sector)}
                className="mr-2"
                disabled={loading}
              />
              <span className="text-sm">{sector}</span>
            </label>
          ))}
        </div>
      </div>
      
      <button
        type="submit"
        disabled={loading}
        className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? 'Screening...' : 'Apply Filters'}
      </button>
    </form>
  )
}