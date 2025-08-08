import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Stock Screener Pro - Advanced NASDAQ Analysis',
  description: 'Professional stock screening tool with AI-powered analysis, real-time data, and comprehensive financial metrics',
  keywords: 'stock screener, NASDAQ, financial analysis, stock market, investment, trading',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        {children}
      </body>
    </html>
  )
}