import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "Beautiful Animated Knowledge Graph",
  description: "Interactive knowledge graph with stunning animations",
    generator: 'v0.dev'
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className} style={{ background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)" }}>
        {children}
      </body>
    </html>
  )
}
