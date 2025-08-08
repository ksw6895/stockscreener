import { NextRequest, NextResponse } from 'next/server'
import { spawn } from 'child_process'
import path from 'path'

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
    const response = await new Promise((resolve, reject) => {
      const python = spawn('python', [
        '-c',
        `
import sys
import json
sys.path.append('${path.join(process.cwd(), 'api', 'routes')}')
from screening import get_job_status

result = get_job_status('${jobId}')
print(json.dumps(result))
        `
      ])
      
      let output = ''
      let error = ''
      
      python.stdout.on('data', (data) => {
        output += data.toString()
      })
      
      python.stderr.on('data', (data) => {
        error += data.toString()
      })
      
      python.on('close', (code) => {
        if (code !== 0) {
          reject(new Error(error || 'Python process failed'))
        } else {
          try {
            resolve(JSON.parse(output))
          } catch (e) {
            reject(new Error('Failed to parse Python output'))
          }
        }
      })
    })
    
    return NextResponse.json(response)
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to get job status' },
      { status: 500 }
    )
  }
}