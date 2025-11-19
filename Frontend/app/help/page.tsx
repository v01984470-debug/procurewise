"use client"

import { useState } from "react"
import Header from "@/components/header"
import Sidebar from "@/components/sidebar"
import Help from "@/components/help"

export default function HelpPage() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true)

  return (
    <div className="flex h-screen flex-col">
      <Header toggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)} />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar isOpen={isSidebarOpen} />
        <main className="flex-1 p-4 overflow-y-auto" style={{marginTop:"4em"}}>
          <Help />
        </main>
      </div>
    </div>
  )
}
