"use client"

import { useState } from "react"
import Header from "@/components/header"
import Sidebar from "@/components/sidebar"

import Alerts from "../alerts"
import ChatWindow from "../../components/chat-window"

export interface AlertContext {
  id: number
  message: string
  priority: string
  type: string
  timestamp: string
}

export default function AlertsPage() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
    const [currentView, setCurrentView] = useState<"alerts" | "chat">("alerts")
  const [replyToAlert, setReplyToAlert] = useState<AlertContext | null>(null)

  const navigateToChat = (alert: AlertContext) => {
    setReplyToAlert(alert)
    setCurrentView("chat")
  }

  const navigateToAlerts = () => {
    setCurrentView("alerts")
    setReplyToAlert(null)
  }

  return (
    <div className="flex h-screen flex-col">
      <Header toggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)} />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar isOpen={isSidebarOpen} />
        <main className="flex-1 p-4 overflow-y-auto" style={{marginTop:"4em"}}>
          {currentView === "alerts" ? (
        <Alerts onTakeOptiBuySuggestion={navigateToChat} />
      ) : (
        <ChatWindow replyToAlert={replyToAlert} onBackToAlerts={navigateToAlerts} />
      )}
        </main>
      </div>
    </div>
  )
}
