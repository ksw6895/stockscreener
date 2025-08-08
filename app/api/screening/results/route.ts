import { NextRequest, NextResponse } from 'next/server'

// Mock stock data for demo purposes
const generateMockStocks = () => {
  const sectors = ['Technology', 'Healthcare', 'Finance', 'Energy', 'Consumer']
  const stocks = []
  
  for (let i = 0; i < 20; i++) {
    stocks.push({
      symbol: `DEMO${i + 1}`,
      name: `Demo Company ${i + 1}`,
      sector: sectors[Math.floor(Math.random() * sectors.length)],
      price: Math.random() * 500 + 50,
      marketCap: Math.random() * 1000000000000 + 1000000000,
      peRatio: Math.random() * 50 + 10,
      qualityScore: Math.random() * 40 + 60,
      revenueGrowth: Math.random() * 50 - 10,
      roe: Math.random() * 30 + 5,
      beta: Math.random() * 2 + 0.5
    })
  }
  
  return stocks.sort((a, b) => b.qualityScore - a.qualityScore)
}

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const jobId = searchParams.get('jobId')
  
  if (!jobId) {
    return NextResponse.json(
      { error: 'Job ID is required' },
      { status: 400 }
    )
  }
  
  try {
    // In production, this would:
    // 1. Query the database for job results
    // 2. Return actual screening results from your Python backend
    
    // For demo, return mock data
    const mockStocks = generateMockStocks()
    
    return NextResponse.json({
      jobId,
      stocks: mockStocks,
      criteria: {
        minMarketCap: 1000000000,
        maxPE: 50,
        minROE: 10,
        sectors: []
      },
      completedAt: new Date().toISOString()
    })
    
  } catch (error) {
    console.error('Failed to get job results:', error)
    return NextResponse.json(
      { error: 'Failed to get job results' },
      { status: 500 }
    )
  }
}