"use client"

import { useEffect, useRef } from "react"
import Chart from "chart.js/auto"

export default function SupplierChart() {
  const chartRef = useRef<HTMLCanvasElement>(null)
  const chartInstance = useRef<Chart | null>(null)

  useEffect(() => {
    if (chartRef.current) {
      const ctx = chartRef.current.getContext("2d")

      if (ctx) {
        if (chartInstance.current) {
          chartInstance.current.destroy()
        }

        chartInstance.current = new Chart(ctx, {
          type: "bar",
          data: {
            labels: ["ElectroTech (Air)", "ElectroTech (Sea)", "SinoTech (Air)", "SinoTech (Sea)"],
            datasets: [
              {
                label: "Cost per Unit (USD)",
                data: [2.1, 0.21, 2.05, 0.2],
                backgroundColor: "#60A5FA",
                borderColor: "#4B5563",
                borderWidth: 1,
              },
              {
                label: "Lead Time (Days)",
                data: [4, 20, 5, 22],
                backgroundColor: "#9CA3AF",
                borderColor: "#4B5563",
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
              },
            },
            plugins: {
              title: {
                display: true,
                text: "Supplier Cost & Lead Time Comparison",
                color: "#374151",
              },
              legend: {
                labels: {
                  color: "#374151",
                },
              },
            },
          },
        })
      }
    }

    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy()
      }
    }
  }, [])

  return (
    <div className="h-64 w-full">
      <canvas ref={chartRef} aria-label="Supplier comparison chart" role="img"></canvas>
    </div>
  )
}
