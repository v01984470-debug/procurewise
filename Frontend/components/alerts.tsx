"use client"

import { useState } from "react"
import { AlertTriangle, Clock, Package, Filter } from "lucide-react"
import Image from "next/image"

interface AlertContext {
  id: number
  message: string
  priority: string
  type: string
  timestamp: string
}

interface AlertsProps {
  onTakeOptiBuySuggestion: (alert: AlertContext) => void
}

export default function Alerts({ onTakeOptiBuySuggestion }: AlertsProps) {
  const [filter, setFilter] = useState("all")

  const alerts = [
    {
      id: 1,
      message: "PO 104007 supplier ETA date 24/05/2025 is crossed and PO is also not closed.",
      priority: "High",
      type: "Route Disruption",
      timestamp: "2 hours ago",
      actions: ["Take OptiBuy Suggestion", "Ignore"],
    },
  ]

  const filteredAlerts = filter === "all" ? alerts : alerts.filter((alert) => alert.priority.toLowerCase() === filter)

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "High":
        return "border-red-500 bg-red-50"
      case "Medium":
        return "border-amber-500 bg-amber-50"
      case "Low":
        return "border-accent-blue bg-blue-50"
      default:
        return "border-gray-300 bg-gray-50"
    }
  }

  const getIcon = (type: string) => {
    switch (type) {
      case "delay":
        return <Clock className="h-5 w-5 text-red-500" />
      case "inventory":
        return <Package className="h-5 w-5 text-amber-500" />
      case "quality":
        return <AlertTriangle className="h-5 w-5 text-red-500" />
      default:
        return <AlertTriangle className="h-5 w-5 text-primary-grey" />
    }
  }

  const handleTakeOptiBuySuggestion = (alert: (typeof alerts)[0]) => {
    const alertContext: AlertContext = {
      id: alert.id,
      message: alert.message,
      priority: alert.priority,
      type: alert.type,
      timestamp: alert.timestamp,
    }
    onTakeOptiBuySuggestion(alertContext)
  }

  return (
    <div className="relative max-w-4xl mx-auto">
      <div className="absolute inset-0 overflow-hidden rounded-lg">
        <Image
          src="/placeholder.svg?height=600&width=800"
          alt="Warehouse background"
          fill
          className="object-cover opacity-10"
          priority
        />
      </div>

      <div className="relative glass-effect rounded-lg shadow-lg p-6">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-primary-dark mb-2">Alerts & Notifications</h1>
          <p className="text-primary-grey">Stay updated on important procurement events and required actions</p>
        </div>

        {/* Filter Controls */}
        <div className="mb-6 flex items-center space-x-4">
          <div className="flex items-center">
            <Filter className="h-5 w-5 text-primary-grey mr-2" />
            <span className="text-sm font-medium text-primary-dark">Filter by priority:</span>
          </div>
          <div className="flex space-x-2">
            {["all", "high", "medium", "low"].map((priority) => (
              <button
                key={priority}
                onClick={() => setFilter(priority)}
                className={`px-3 py-1 rounded-full text-sm font-medium transition-all ${
                  filter === priority
                    ? "bg-accent-grey text-white"
                    : "bg-white text-primary-grey border border-secondary-grey hover:bg-secondary-light"
                }`}
              >
                {priority.charAt(0).toUpperCase() + priority.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Alerts List */}
        <div className="space-y-4">
          {filteredAlerts.map((alert) => (
            <div
              key={alert.id}
              className={`bg-white p-6 rounded-lg shadow-sm border-l-4 ${getPriorityColor(alert.priority)}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  {getIcon(alert.type)}
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span
                        className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          alert.priority === "High"
                            ? "bg-red-100 text-red-800"
                            : alert.priority === "Medium"
                              ? "bg-amber-100 text-amber-800"
                              : "bg-blue-100 text-blue-800"
                        }`}
                      >
                        {alert.priority} Priority
                      </span>
                      <span className="text-xs text-primary-grey">{alert.timestamp}</span>
                    </div>
                    <p className="text-primary-dark font-medium mb-3">{alert.message}</p>
                    <div className="flex flex-wrap gap-2">
                      {alert.actions.map((action, idx) => (
                        <button
                          key={idx}
                          onClick={() => {
                            if (action === "Take OptiBuy Suggestion") {
                              handleTakeOptiBuySuggestion(alert)
                            }
                          }}
                          className="bg-accent-grey text-white px-3 py-1 rounded text-sm font-medium hover:bg-accent-grey/80 transition-all"
                        >
                          {action}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {filteredAlerts.length === 0 && (
          <div className="text-center py-12 bg-white rounded-lg">
            <AlertTriangle className="h-12 w-12 text-primary-grey mx-auto mb-4" />
            <h3 className="text-lg font-medium text-primary-dark mb-2">No alerts found</h3>
            <p className="text-primary-grey">No alerts match the selected filter criteria.</p>
          </div>
        )}
      </div>
    </div>
  )
}
