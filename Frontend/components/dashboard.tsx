"use client"

import { useEffect, useRef } from "react"
import Chart from "chart.js/auto"
import { TrendingUp, Package, Clock, AlertTriangle } from "lucide-react"
import Image from "next/image"

export default function Dashboard() {
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
            labels: ["ElectroTech", "SinoTech", "Precision", "GlobalTech", "AsiaComponents"],
            datasets: [
              {
                label: "Delivery Performance (%)",
                data: [92, 91, 85, 88, 89],
                backgroundColor: "#60A5FA",
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
                max: 100,
              },
            },
            plugins: {
              title: {
                display: true,
                text: "Supplier Performance Metrics",
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

  const stats = [
    {
      title: "Active POs",
      value: "24",
      change: "+12%",
      icon: Package,
      color: "text-accent-blue",
    },
    {
      title: "Avg Lead Time",
      value: "5.2 days",
      change: "-8%",
      icon: Clock,
      color: "text-accent-grey",
    },
    {
      title: "Cost Savings",
      value: "$45,200",
      change: "+15%",
      icon: TrendingUp,
      color: "text-green-600",
    },
    {
      title: "Pending Issues",
      value: "3",
      change: "-2",
      icon: AlertTriangle,
      color: "text-red-500",
    },
  ]

  const inventoryData = [
    { item: "ITM-001", qty: 12000, status: "Sufficient", statusColor: "text-green-600" },
    { item: "ITM-002", qty: 7500, status: "Reorder", statusColor: "text-red-500" },
    { item: "ITM-003", qty: 15200, status: "Sufficient", statusColor: "text-green-600" },
    { item: "ITM-004", qty: 3200, status: "Low Stock", statusColor: "text-amber-500" },
    { item: "ITM-005", qty: 8900, status: "Sufficient", statusColor: "text-green-600" },
  ]

  return (
    <div className="relative max-w-6xl mx-auto">
      <div className="absolute inset-0 overflow-hidden rounded-lg">
        <Image
          src="/images/background.png"
          alt="Warehouse background"
          fill
          className="object-cover opacity-10"
          priority
        />
      </div>

      <div className="relative glass-effect rounded-lg shadow-lg p-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-primary-dark mb-2">Procurement Dashboard</h1>
          <p className="text-primary-grey">Overview of your procurement activities and performance metrics</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat, index) => (
            <div key={index} className="bg-white p-6 rounded-lg shadow-sm border border-secondary-grey">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-primary-grey text-sm font-medium">{stat.title}</p>
                  <p className="text-2xl font-bold text-primary-dark mt-1">{stat.value}</p>
                  <p className={`text-sm mt-1 ${stat.change.startsWith("+") ? "text-green-600" : "text-red-500"}`}>
                    {stat.change} from last month
                  </p>
                </div>
                <stat.icon className={`h-8 w-8 ${stat.color}`} />
              </div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Supplier Performance Chart */}
          <div className="bg-white p-6 rounded-lg shadow-sm border border-secondary-grey">
            <h2 className="text-xl font-semibold text-primary-dark mb-4">Supplier Performance</h2>
            <div className="h-64">
              <canvas ref={chartRef}></canvas>
            </div>
          </div>

          {/* Inventory Status */}
          <div className="bg-white p-6 rounded-lg shadow-sm border border-secondary-grey">
            <h2 className="text-xl font-semibold text-primary-dark mb-4">Inventory Status</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left text-primary-dark">
                <thead className="bg-secondary-light">
                  <tr>
                    <th className="p-3 font-semibold">Item</th>
                    <th className="p-3 font-semibold">Quantity</th>
                    <th className="p-3 font-semibold">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {inventoryData.map((item, index) => (
                    <tr key={index} className="border-b border-secondary-grey hover:bg-secondary-light">
                      <td className="p-3 font-medium">{item.item}</td>
                      <td className="p-3">{item.qty.toLocaleString()}</td>
                      <td className="p-3">
                        <span className={`font-medium ${item.statusColor}`}>{item.status}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="mt-6 bg-white p-6 rounded-lg shadow-sm border border-secondary-grey">
          <h2 className="text-xl font-semibold text-primary-dark mb-4">Recent Activity</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-secondary-light rounded-lg">
              <div>
                <p className="font-medium text-primary-dark">PO-78901 shipped from ElectroTech</p>
                <p className="text-sm text-primary-grey">Expected delivery: May 27, 2025</p>
              </div>
              <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">On Track</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-secondary-light rounded-lg">
              <div>
                <p className="font-medium text-primary-dark">New quote received for ITM-003</p>
                <p className="text-sm text-primary-grey">From SinoTech Components - $98,500</p>
              </div>
              <span className="text-xs bg-amber-100 text-amber-800 px-2 py-1 rounded-full">Review</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-secondary-light rounded-lg">
              <div>
                <p className="font-medium text-primary-dark">Inventory alert for ITM-002</p>
                <p className="text-sm text-primary-grey">Stock level below threshold</p>
              </div>
              <span className="text-xs bg-red-100 text-red-800 px-2 py-1 rounded-full">Action Required</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
