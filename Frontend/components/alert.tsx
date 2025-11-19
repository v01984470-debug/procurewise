"use client"

import { AlertCircle, X, Loader2 } from "lucide-react"

interface AlertProps {
  type: "error" | "loading"
  message: string
  onClose: () => void
}

export default function Alert({ type, message, onClose }: AlertProps) {
  return (
    <div className="fixed bottom-20 left-1/2 transform -translate-x-1/2 z-50 fade-in">
      <div
        className={`flex items-center p-4 rounded-lg shadow-lg ${
          type === "error" ? "bg-white border-2 border-alert-red border-opacity-80" : "bg-white"
        }`}
        role="alert"
      >
        {type === "error" ? (
          <AlertCircle className="text-alert-red mr-2" size={20} />
        ) : (
          <Loader2 className="text-primary-accent mr-2 animate-spin" size={20} />
        )}

        <span className="text-text-dark">{message}</span>

        {type === "error" && (
          <button
            onClick={onClose}
            className="ml-4 text-text-grey hover:text-primary-grey transition-colors"
            aria-label="Close alert"
          >
            <X size={16} />
          </button>
        )}
      </div>
    </div>
  )
}
