import { NextRequest, NextResponse } from 'next/server'

// Simulated job status for demo purposes
const mockJobs: { [key: string]: any } = {}

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
    // Simulate job progress
    // In production, this would query a database or job queue
    
    // Create a mock job if it doesn't exist
    if (!mockJobs[jobId]) {
      mockJobs[jobId] = {
        status: 'running',
        progress: 0,
        startedAt: new Date().toISOString()
      }
    }
    
    // Simulate progress increment
    if (mockJobs[jobId].status === 'running') {
      mockJobs[jobId].progress = Math.min(100, mockJobs[jobId].progress + 20)
      
      if (mockJobs[jobId].progress >= 100) {
        mockJobs[jobId].status = 'completed'
        mockJobs[jobId].completedAt = new Date().toISOString()
      }
    }
    
    return NextResponse.json({
      jobId,
      status: mockJobs[jobId].status,
      progress: mockJobs[jobId].progress,
      startedAt: mockJobs[jobId].startedAt,
      completedAt: mockJobs[jobId].completedAt
    })
    
  } catch (error) {
    console.error('Failed to get job status:', error)
    return NextResponse.json(
      { error: 'Failed to get job status' },
      { status: 500 }
    )
  }
}