"use client"

import { useEffect, useRef } from "react"
import Chart from "chart.js/auto"

export default function SupplierPerformanceChart() {
  const chartRef = useRef<HTMLCanvasElement>(null)
  const chartInstance = useRef<Chart | null>(null)

  useEffect(() => {
    if (chartRef.current) {
      const ctx = chartRef.current.getContext("2d")

      if (ctx) {
        // Destroy previous chart instance if it exists
        if (chartInstance.current) {
          chartInstance.current.destroy()
        }

        // Create new chart
        chartInstance.current = new Chart(ctx, {
          type: "bar",
          data: {
            labels: ["Quality", "On-Time Delivery", "Price Competitiveness", "Communication", "Flexibility"],
            datasets: [
              {
                label: "Performance Score (out of 100)",
                data: [92, 88, 85, 90, 78],
                backgroundColor: "#718096",
                borderColor: "#4A5568",
                borderWidth: 1,
              },
            ],
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              y: {
                beginAtZero: true,
                max: 100,
                ticks: {
                  callback: (value) => value + "%",
                },
              },
            },
            plugins: {
              tooltip: {
                callbacks: {
                  label: (context) => context.parsed.y + "%",
                },
              },
            },
          },
        })
      }
    }

    // Cleanup function
    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy()
      }
    }
  }, [])

  return (
    <div className="h-64 w-full">
      <canvas ref={chartRef} aria-label="Supplier performance chart" role="img"></canvas>
    </div>
  )
}
