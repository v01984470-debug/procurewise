"use client"

import { useState } from "react"
import Header from "./header"
import Sidebar from "./sidebar"
import ChatWindow from "./chat-window"
import InputBar from "./input-bar"
import Modal from "./modal"
import Alert from "./alert"
import type { Message, SupplierData } from "@/lib/types"
import { mockMessages, mockSuppliers } from "@/lib/mock-data"

export default function ProcureWiseChat() {
  const [messages, setMessages] = useState<Message[]>(mockMessages)
  const [isTyping, setIsTyping] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [selectedSupplier, setSelectedSupplier] = useState<SupplierData | null>(null)
  const [alert, setAlert] = useState<{
    show: boolean
    type: "error" | "loading"
    message: string
  }>({
    show: false,
    type: "loading",
    message: "",
  })

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen)
  }

  const handleSendMessage = (text: string) => {
    // Add user message
    const newUserMessage: Message = {
      id: `msg-${Date.now()}`,
      text,
      sender: "user",
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, newUserMessage])

    // Show typing indicator
    setIsTyping(true)

    // Simulate API call
    setTimeout(() => {
      setIsTyping(false)

      // Check if query is about ITM-001
      if (text.toLowerCase().includes("itm-001")) {
        const newAgentMessage: Message = {
          id: `msg-${Date.now() + 1}`,
          text: "Here are the top suppliers for ITM-001 in Japan:",
          sender: "agent",
          timestamp: new Date().toISOString(),
          data: {
            type: "suppliers",
            suppliers: mockSuppliers,
          },
        }
        setMessages((prev) => [...prev, newAgentMessage])
      } else if (text.toLowerCase().includes("itm-004")) {
        // Show error for ITM-004
        setAlert({
          show: true,
          type: "error",
          message: "No suppliers found for ITM-004.",
        })

        // Auto-hide alert after 3 seconds
        setTimeout(() => {
          setAlert((prev) => ({ ...prev, show: false }))
        }, 3000)
      } else {
        // Generic response
        const newAgentMessage: Message = {
          id: `msg-${Date.now() + 1}`,
          text: "I understand you're looking for procurement information. Could you please specify an item number? For example, try asking about ITM-001.",
          sender: "agent",
          timestamp: new Date().toISOString(),
        }
        setMessages((prev) => [...prev, newAgentMessage])
      }
    }, 1500)
  }

  const handleViewDetails = (supplier: SupplierData) => {
    setSelectedSupplier(supplier)
    setModalOpen(true)
  }

  const handleCloseModal = () => {
    setModalOpen(false)
    setSelectedSupplier(null)
  }

  const handleAlertClose = () => {
    setAlert((prev) => ({ ...prev, show: false }))
  }

  return (
    <div className="flex flex-col h-screen">
      <Header toggleSidebar={toggleSidebar} />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar isOpen={sidebarOpen} />
        <main className="flex-1 flex flex-col overflow-hidden">
          <ChatWindow messages={messages} isTyping={isTyping} onViewDetails={handleViewDetails} />
          <InputBar onSendMessage={handleSendMessage} />
        </main>
      </div>
      {modalOpen && selectedSupplier && <Modal supplier={selectedSupplier} onClose={handleCloseModal} />}
      {alert.show && <Alert type={alert.type} message={alert.message} onClose={handleAlertClose} />}
    </div>
  )
}
