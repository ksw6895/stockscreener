import { NextRequest, NextResponse } from 'next/server'
import { spawn } from 'child_process'
import path from 'path'

export async function POST(request: NextRequest) {
  try {
    const criteria = await request.json()
    
    // Call Python screening API
    const pythonPath = path.join(process.cwd(), 'api', 'routes', 'screening.py')
    
    const response = await new Promise((resolve, reject) => {
      const python = spawn('python', [
        '-c',
        `
import sys
import json
import asyncio
sys.path.append('${path.join(process.cwd(), 'api', 'routes')}')
from screening import start_screening

async def main():
    result = await start_screening(${JSON.stringify(criteria)})
    print(json.dumps(result))

asyncio.run(main())
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
      { error: 'Failed to start screening' },
      { status: 500 }
    )
  }
}