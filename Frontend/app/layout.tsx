import type React from "react"
import "./globals.css"
import { Inter, Roboto_Mono } from "next/font/google"

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
})

const robotoMono = Roboto_Mono({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-roboto-mono",
})

export const metadata = {
  title: "ProcureWise AI",
  description: "AI-powered procurement management - Streamline Your Procurement, Wisely.",
    generator: '',
    icons: {
      icon: '/images/title_icon.svg', // Replace with the path to your favicon file
    }
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${robotoMono.variable} font-inter bg-secondary-light text-primary-dark`}>
        {children}
      </body>
    </html>
  )
}
