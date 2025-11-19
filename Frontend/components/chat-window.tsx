"use client"

import type React from "react"

import { useState, useEffect, useRef, type KeyboardEvent } from "react"
import {
  Paperclip,
  Mic,
  SendHorizontal,
  Sparkles,
  Workflow,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  User,
  Bot,
  Wrench,
  Database,
  Flag,
  FlagTriangleRight,
  X,
  AlertTriangle,
  Clock,
  Package,
} from "lucide-react"
import Modal from "./modal"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

interface AlertContext {
  id: number
  message: string
  priority: string
  type: string
  timestamp: string
}

interface Message {
  id: number
  text: string
  sender: "user" | "agent"
  name?: string
  timestamp: string
  table?: Array<{
    supplier: string
    location: string
    capacity: number
    cost: number
    leadTime: number
    performance: number
  }>
  actions?: string[]
  showChart?: boolean
  attachedPdfs?: Array<{
    filename: string
    data: string // base64 data
  }>
}

interface Session {
  id: number
  messages: Message[]
  isFlagged?: boolean
  alertContext?: AlertContext | null // Add alert context to session
}

// Graph visualization interfaces
interface GraphNode {
  id: string
  label: string
  role: string
  name?: string
  x: number
  y: number
  messageCount: number
  icon: any
  color: string
  borderColor: string
}

interface GraphEdge {
  id: string
  source: string
  target: string
  count: number
  steps?: number[] // Add step numbers
}

interface GraphChatMessage {
  content: string
  role: string
  name?: string
  tool_calls?: any[]
  tool_responses?: any[]
}

export default function ChatWindow() {
  // All query‐sessions live here
  const [sessions, setSessions] = useState<Session[]>([])
  const [input, setInput] = useState<string>("")
  const [isTyping, setIsTyping] = useState<boolean>(false)
  const [replyToAlert, setReplyToAlert] = useState<AlertContext | null>(null)

  // *** NEW: Hold the rolling summary returned from the last backend call
  const [chatSummary, setChatSummary] = useState<string | null>("")

  // Which session (by id) is currently open in the full-history modal?
  const [openSessionId, setOpenSessionId] = useState<number | null>(null)

  // Graph visualization state
  const [showGraphModal, setShowGraphModal] = useState<boolean>(false)
  const [graphSessionId, setGraphSessionId] = useState<number | null>(null)
  const [graphNodes, setGraphNodes] = useState<GraphNode[]>([])
  const [graphEdges, setGraphEdges] = useState<GraphEdge[]>([])
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [zoom, setZoom] = useState(1)
  const [pan, setPan] = useState({ x: 0, y: 0 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })

  // *** NEW: Node dragging state
  const [isDraggingNode, setIsDraggingNode] = useState(false)
  const [draggedNodeId, setDraggedNodeId] = useState<string | null>(null)
  const [nodeDragStart, setNodeDragStart] = useState({ x: 0, y: 0 })
  const [nodeDragOffset, setNodeDragOffset] = useState({ x: 0, y: 0 })

  // *** UPDATED: Flag conversation state - now separate from conversation modal
  const [showFlagDialog, setShowFlagDialog] = useState<boolean>(false)
  const [flagSessionId, setFlagSessionId] = useState<number | null>(null) // Store which session to flag
  const [flagReason, setFlagReason] = useState<string>("")
  const [isSubmittingFlag, setIsSubmittingFlag] = useState<boolean>(false)
  const [shouldReopenConversation, setShouldReopenConversation] = useState<boolean>(false) // Whether to reopen conversation after flagging

  // PDF upload state
  const [selectedPdfs, setSelectedPdfs] = useState<File[]>([])
  const [isUploadingPdfs, setIsUploadingPdfs] = useState<boolean>(false)

  const svgRef = useRef<SVGSVGElement>(null)

  const chatRef = useRef<HTMLDivElement>(null)

  const SVG_WIDTH = 1400
  const SVG_HEIGHT = 1000

  // Load alert context from sessionStorage on component mount
  useEffect(() => {
    const storedAlert = sessionStorage.getItem("replyToAlert")
    if (storedAlert) {
      const alertContext = JSON.parse(storedAlert)
      setReplyToAlert(alertContext)
    }
  }, [])

  // Always scroll to bottom when sessions update
  useEffect(() => {
    chatRef.current?.scrollTo({
      top: chatRef.current.scrollHeight,
      behavior: "smooth",
    })
  }, [sessions])

  // Helper to capitalize and split snake_case names
  function formatName(raw: string, allCaps = false): string {
    const formatted = raw
      .split("_")
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
      .join(" ")

    return allCaps ? formatted.toUpperCase() : formatted
  }

  // Get alert icon based on type
  const getAlertIcon = (type: string) => {
    switch (type) {
      case "delay":
        return <Clock className="h-4 w-4 text-red-500" />
      case "inventory":
        return <Package className="h-4 w-4 text-amber-500" />
      case "quality":
        return <AlertTriangle className="h-4 w-4 text-red-500" />
      default:
        return <AlertTriangle className="h-4 w-4 text-gray-500" />
    }
  }

  // Get priority color for alert
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "High":
        return "border-red-500 bg-red-50 text-red-800"
      case "Medium":
        return "border-amber-500 bg-amber-50 text-amber-800"
      case "Low":
        return "border-blue-500 bg-blue-50 text-blue-800"
      default:
        return "border-gray-300 bg-gray-50 text-gray-800"
    }
  }

  // Helper function to convert file to base64 byte string
  const fileToByteString = (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => {
        if (reader.result) {
          // Convert to base64 and remove the data URL prefix
          const base64 = (reader.result as string).split(",")[1]
          resolve(base64)
        } else {
          reject(new Error("Failed to read file"))
        }
      }
      reader.onerror = () => reject(reader.error)
      reader.readAsDataURL(file)
    })
  }

  // Handle PDF file selection
  const handlePdfUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (files) {
      const pdfFiles = Array.from(files).filter((file) => file.type === "application/pdf")
      setSelectedPdfs((prev) => [...prev, ...pdfFiles])
    }
    // Reset the input value to allow selecting the same file again
    event.target.value = ""
  }

  // Remove selected PDF
  const removePdf = (index: number) => {
    setSelectedPdfs((prev) => prev.filter((_, i) => i !== index))
  }

  // Graph visualization helper functions
  const getNodeIcon = (role: string, name?: string) => {
    if (role === "user") return User
    if (role === "assistant") return Bot
    if (role === "tool") return Wrench
    if (name?.includes("sql")) return Database
    return Bot
  }

  const getNodeColor = (role: string) => {
    if (role === "user") return "#3b82f6"
    if (role === "assistant") return "#10b981"
    if (role === "tool") return "#8b5cf6"
    return "#6b7280"
  }

  const getNodeBorderColor = (role: string) => {
    if (role === "user") return "#93c5fd"
    if (role === "assistant") return "#6ee7b7"
    if (role === "tool") return "#c4b5fd"
    return "#d1d5db"
  }

  // Convert sessions to chat history format for graph visualization
  const convertSessionsToGraphData = (sessionId?: number): GraphChatMessage[] => {
    let messagesToConvert: Message[] = []

    if (sessionId) {
      // Single session
      const session = sessions.find((s) => s.id === sessionId)
      messagesToConvert = session?.messages || []
    } else {
      // All sessions combined
      messagesToConvert = sessions.flatMap((session) => session.messages)
    }

    return messagesToConvert.map((msg) => ({
      content: msg.text,
      role: msg.sender === "user" ? "user" : "assistant",
      name: msg.name?.toLowerCase().replace(/\s+/g, "_") || (msg.sender === "user" ? "you" : "assistant"),
    }))
  }

  // *** NEW: Get messages for a specific participant in the current session
  const getParticipantMessages = (participantId: string): Message[] => {
    if (!graphSessionId) return []

    const session = sessions.find((s) => s.id === graphSessionId)
    if (!session) return []

    // Parse participant ID to get role and name
    const [role, ...nameParts] = participantId.split("-")
    const participantName = nameParts.join("_")

    // Filter messages for this participant
    return session.messages.filter((msg) => {
      const msgRole = msg.sender === "user" ? "user" : "assistant"
      const msgName = msg.name?.toLowerCase().replace(/\s+/g, "_") || (msg.sender === "user" ? "you" : "assistant")

      return msgRole === role && msgName === participantName
    })
  }

  // *** UPDATED: Initiate flag conversation flow
  const initiateFlagConversation = (sessionId: number, shouldReopen = false) => {
    // Store which session to flag
    setFlagSessionId(sessionId)
    setShouldReopenConversation(shouldReopen)

    // Close conversation modal if open
    setOpenSessionId(null)

    // Open flag dialog as separate modal
    setShowFlagDialog(true)
  }

  // *** UPDATED: Flag conversation functionality
  const handleFlagConversation = async () => {
    if (!flagSessionId || !flagReason.trim()) return

    setIsSubmittingFlag(true)

    try {
      const session = sessions.find((s) => s.id === flagSessionId)
      if (!session) return

      const response = await fetch("http://localhost:8001/flag-runs", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          reason: flagReason.trim(),
          messages: session.messages,
        }),
      })

      if (response.ok) {
        // Mark session as flagged
        setSessions((prev) => prev.map((sess) => (sess.id === flagSessionId ? { ...sess, isFlagged: true } : sess)))

        // Close flag dialog and reset
        setShowFlagDialog(false)
        setFlagReason("")

        // Optionally reopen conversation modal
        if (shouldReopenConversation) {
          setOpenSessionId(flagSessionId)
        }

        setFlagSessionId(null)
        setShouldReopenConversation(false)

        // Show success message (you could add a toast notification here)
        console.log("Conversation flagged successfully")
      } else {
        console.error("Failed to flag conversation")
      }
    } catch (error) {
      console.error("Error flagging conversation:", error)
    } finally {
      setIsSubmittingFlag(false)
    }
  }

  // *** UPDATED: Cancel flag dialog
  const cancelFlagDialog = () => {
    setShowFlagDialog(false)
    setFlagReason("")

    // Optionally reopen conversation modal
    if (shouldReopenConversation) {
      setOpenSessionId(flagSessionId)
    }

    setFlagSessionId(null)
    setShouldReopenConversation(false)
  }

  // Open graph modal for specific session or all sessions
  const openGraphModal = (sessionId?: number) => {
    setGraphSessionId(sessionId || null)

    // Convert data and generate graph
    const chatData = convertSessionsToGraphData(sessionId)
    generateGraph(chatData)

    setShowGraphModal(true)
  }

  // Enhanced hierarchical graph generation with increased spacing
  const generateGraph = (chatData: GraphChatMessage[]) => {
    if (!chatData || chatData.length === 0) return

    // Create unique participants (ONE node per participant, not per message)
    const participantMap = new Map()
    const messageSequence: { participantKey: string; step: number }[] = []

    chatData.forEach((message, index) => {
      const participantKey = `${message.role}-${message.name || "default"}`
      const displayName = message.name
        ? formatName(message.name, true) // Convert to ALL CAPS and replace underscores with spaces
        : `${message.role.charAt(0).toUpperCase() + message.role.slice(1)}`

      messageSequence.push({ participantKey, step: index + 1 })

      if (!participantMap.has(participantKey)) {
        participantMap.set(participantKey, {
          id: participantKey,
          role: message.role,
          name: message.name,
          displayName: displayName,
          messageCount: 1,
          firstIndex: index,
          lastIndex: index,
        })
      } else {
        // Just increment the message count for existing participant
        const participant = participantMap.get(participantKey)
        participant.messageCount++
        participant.lastIndex = index
      }
    })

    // Enhanced hierarchical layout with proper role-based positioning
    const participants = Array.from(participantMap.values())
    participants.sort((a, b) => a.firstIndex - b.firstIndex)

    const newNodes: GraphNode[] = []

    // Increased spacing between nodes
    const nodeSpacing = 180
    const columnSpacing = 300
    const startY = 100
    const startX = 200

    // Group participants by role for better hierarchy
    const roleGroups = {
      user: participants.filter((p) => p.role === "user"),
      assistant: participants.filter((p) => p.role === "assistant"),
      tool: participants.filter((p) => p.role === "tool"),
    }

    // Enhanced hierarchical positioning logic
    const userColumn = startX
    const assistantColumn = startX + columnSpacing * 2
    const toolColumn = startX + columnSpacing * 4

    // Position user nodes (left column)
    roleGroups.user.forEach((participant, index) => {
      newNodes.push({
        id: participant.id,
        label: participant.displayName,
        role: participant.role,
        name: participant.name,
        x: userColumn,
        y: startY + index * nodeSpacing,
        messageCount: participant.messageCount,
        icon: getNodeIcon(participant.role, participant.name),
        color: getNodeColor(participant.role),
        borderColor: getNodeBorderColor(participant.role),
      })
    })

    // Position assistant nodes (middle column) - hierarchical by appearance order
    let assistantY = startY
    roleGroups.assistant.forEach((participant, index) => {
      // Create sub-hierarchy for different assistant types
      let xOffset = 0
      if (participant.name?.includes("sql")) {
        xOffset = -50 // SQL assistants slightly to the left
      } else if (participant.name?.includes("planner")) {
        xOffset = 50 // Planners slightly to the right
      }

      newNodes.push({
        id: participant.id,
        label: participant.displayName,
        role: participant.role,
        name: participant.name,
        x: assistantColumn + xOffset,
        y: assistantY,
        messageCount: participant.messageCount,
        icon: getNodeIcon(participant.role, participant.name),
        color: getNodeColor(participant.role),
        borderColor: getNodeBorderColor(participant.role),
      })

      assistantY += nodeSpacing
    })

    // Position tool nodes (right column)
    let toolY = startY
    roleGroups.tool.forEach((participant, index) => {
      newNodes.push({
        id: participant.id,
        label: participant.displayName,
        role: participant.role,
        name: participant.name,
        x: toolColumn,
        y: toolY,
        messageCount: participant.messageCount,
        icon: getNodeIcon(participant.role, participant.name),
        color: getNodeColor(participant.role),
        borderColor: getNodeBorderColor(participant.role),
      })

      toolY += nodeSpacing
    })

    // Create workflow edges based on actual message sequence with step numbers
    const newEdges: GraphEdge[] = []
    const edgeStepsMap = new Map()

    for (let i = 0; i < messageSequence.length - 1; i++) {
      const sourceKey = messageSequence[i].participantKey
      const targetKey = messageSequence[i + 1].participantKey
      const stepNumber = messageSequence[i + 1].step

      if (sourceKey !== targetKey) {
        const edgeKey = `${sourceKey}→${targetKey}`

        if (!edgeStepsMap.has(edgeKey)) {
          edgeStepsMap.set(edgeKey, [])
        }
        edgeStepsMap.get(edgeKey).push(stepNumber)
      }
    }

    // Create edges with step numbers
    edgeStepsMap.forEach((steps, edgeKey) => {
      const [sourceKey, targetKey] = edgeKey.split("→")
      const sourceNode = newNodes.find((n) => n.id === sourceKey)
      const targetNode = newNodes.find((n) => n.id === targetKey)

      if (sourceNode && targetNode) {
        newEdges.push({
          id: edgeKey,
          source: sourceKey,
          target: targetKey,
          count: steps.length, // Keep count for edge thickness
          steps: steps, // Add step numbers
        })
      }
    })

    setGraphNodes(newNodes)
    setGraphEdges(newEdges)
  }

  // *** NEW: Node dragging handlers
  const handleNodeMouseDown = (e: React.MouseEvent, nodeId: string) => {
    e.stopPropagation() // Prevent canvas panning

    const node = graphNodes.find((n) => n.id === nodeId)
    if (!node) return

    setIsDraggingNode(true)
    setDraggedNodeId(nodeId)

    // Get mouse position relative to SVG
    const svgRect = svgRef.current?.getBoundingClientRect()
    if (svgRect) {
      const mouseX = (e.clientX - svgRect.left - pan.x) / zoom
      const mouseY = (e.clientY - svgRect.top - pan.y) / zoom

      setNodeDragStart({ x: mouseX, y: mouseY })
      setNodeDragOffset({
        x: mouseX - node.x,
        y: mouseY - node.y,
      })
    }
  }

  // Graph interaction handlers (modified to handle node dragging)
  const handleMouseDown = (e: React.MouseEvent) => {
    if (isDraggingNode) return // Don't start canvas drag if dragging a node

    setIsDragging(true)
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - dragStart.y })
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDraggingNode && draggedNodeId) {
      // Handle node dragging
      const svgRect = svgRef.current?.getBoundingClientRect()
      if (svgRect) {
        const mouseX = (e.clientX - svgRect.left - pan.x) / zoom
        const mouseY = (e.clientY - svgRect.top - pan.y) / zoom

        const newX = mouseX - nodeDragOffset.x
        const newY = mouseY - nodeDragOffset.y

        // Update the node position
        setGraphNodes((prevNodes) =>
          prevNodes.map((node) => (node.id === draggedNodeId ? { ...node, x: newX, y: newY } : node)),
        )
      }
    } else if (isDragging) {
      // Handle canvas panning
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      })
    }
  }

  const handleMouseUp = () => {
    setIsDragging(false)
    setIsDraggingNode(false)
    setDraggedNodeId(null)
  }

  const handleZoomIn = () => {
    setZoom((prev) => Math.min(prev * 1.2, 3))
  }

  const handleZoomOut = () => {
    setZoom((prev) => Math.max(prev / 1.2, 0.3))
  }

  const handleReset = () => {
    setZoom(1)
    setPan({ x: 0, y: 0 })
    setSelectedNode(null)
    // Regenerate graph to reset node positions
    const chatData = convertSessionsToGraphData(graphSessionId)
    generateGraph(chatData)
  }

  // Helper function to create blob URL from base64 and open PDF
  const openPdfInNewTab = (filename: string, base64Data: string) => {
    try {
      // Convert base64 to blob
      const byteCharacters = atob(base64Data)
      const byteNumbers = new Array(byteCharacters.length)
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i)
      }
      const byteArray = new Uint8Array(byteNumbers)
      const blob = new Blob([byteArray], { type: "application/pdf" })

      // Create blob URL and open in new tab
      const blobUrl = URL.createObjectURL(blob)
      window.open(blobUrl, "_blank")

      // Clean up blob URL after a delay
      setTimeout(() => URL.revokeObjectURL(blobUrl), 1000)
    } catch (error) {
      console.error("Failed to open PDF:", error)
    }
  }

  // Send the user's query and create a new session
  const handleSend = async () => {
    const query = input.trim()
    if (!query && selectedPdfs.length === 0) return

    // Prepare the message text with alert context if replying to alert
    const messageText = query
    let apiQuery = query

    if (replyToAlert) {
      // For API: include alert context
      apiQuery = `Replying to alert: "${replyToAlert.message}" (Priority: ${replyToAlert.priority}, Type: ${replyToAlert.type})\n\nUser message: ${query}`
    }

    setInput("")
    setIsTyping(true)
    setIsUploadingPdfs(true)

    try {
      // Process PDFs to byte strings FIRST
      const pdfByteStrings: { filename: string; data: string }[] = []

      if (selectedPdfs.length > 0) {
        for (const pdf of selectedPdfs) {
          try {
            const byteString = await fileToByteString(pdf)
            pdfByteStrings.push({
              filename: pdf.name,
              data: byteString,
            })
          } catch (error) {
            console.error(`Failed to process PDF ${pdf.name}:`, error)
          }
        }
      }

      // 1) Create the user message WITH PDF data
      const userMsg: Message = {
        id: 1,
        text: messageText,
        sender: "user",
        name: "You",
        timestamp: new Date().toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        }),
        attachedPdfs: pdfByteStrings.length > 0 ? pdfByteStrings : undefined,
      }

      // 2) New session container
      const newSession: Session = {
        id: sessions.length + 1,
        messages: [userMsg],
        isFlagged: false,
        alertContext: replyToAlert, // Store alert context in session
      }

      // 3) Append it
      setSessions((prev) => [...prev, newSession])

      // 4) Fire off the backend call
      const requestBody: any = {
        query: apiQuery, // Send the query with alert context
        chat_summary: chatSummary,
      }

      // Add PDFs to payload if any were uploaded
      if (pdfByteStrings.length > 0) {
        requestBody.pdfs = pdfByteStrings
      }

      console.log(requestBody)

      const resp = await fetch("http://localhost:8001/supplier-analysis", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      })
      const data = await resp.json()

      // *** NEW: update our summary state for next time
      if (data.chat_summary) {
        setChatSummary(data.chat_summary)
      }

      // 5) Transform returned chat_history into Message[]
      const agentMsgs: Message[] = data.chat_history
        .filter((e: any) => e.content != null && e.content !== "None")
        .map((entry: any, idx: number) => ({
          id: idx + 2, // user was 1
          text: entry.content,
          sender: entry.name === "you" ? "user" : "agent",
          name: formatName(entry.name),
          timestamp: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
        }))

      // 6) Append agent messages only into our new session
      setSessions((prev) =>
        prev.map((sess) =>
          sess.id === newSession.id ? { ...sess, messages: [...sess.messages, ...agentMsgs] } : sess,
        ),
      )

      // Clear selected PDFs after successful send
      setSelectedPdfs([])
    } catch (error) {
      console.error("Error fetching chat:", error)
      // On error, append a failure notice into that session
      setSessions((prev) =>
        prev.map((sess) => {
          return sess.id === newSession.id
            ? {
                ...sess,
                messages: [
                  ...sess.messages,
                  {
                    id: sess.messages.length + 1,
                    text: "⚠️ Failed to load response. Please try again.",
                    sender: "agent",
                    timestamp: new Date().toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    }),
                  },
                ],
              }
            : sess
        }),
      )
    } finally {
      setIsTyping(false)
      setIsUploadingPdfs(false)
      // Clear the alert context after sending
      if (replyToAlert) {
        sessionStorage.removeItem("replyToAlert")
        setReplyToAlert(null)
      }
    }
  }

  const onKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="relative mx-auto" style={{ width: "90%" }}>
      <div className="relative glass-effect rounded-lg shadow-lg p-6">
        <header className="mb-4 flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-primary-dark mb-2">OptiBuy Assistant</h1>
            <p className="text-primary-grey">
              Ask me about suppliers, purchase orders, inventory, or any procurement needs.
            </p>
          </div>
          {/* Global graph view button - only show if there are sessions */}
          {sessions.length > 0 && (
            <button
              onClick={() => openGraphModal()}
              className="flex items-center space-x-2 bg-accent-blue text-white px-4 py-2 rounded-lg hover:bg-accent-blue/80 transition-colors"
            >
              <Workflow className="h-5 w-5" />
              <span>View Conversation Graph</span>
            </button>
          )}
        </header>

        {/* Chat scroll area */}
        <div
          ref={chatRef}
          className="h-[calc(100vh-300px)] overflow-y-auto mb-4 border border-secondary-grey rounded-lg p-4 bg-white bg-opacity-80"
        >
          {sessions.length === 0 ? (
            // Empty state when no sessions
            <div className="flex items-center justify-center h-full text-center">
              <div className="space-y-4">
                <div className="w-16 h-16 mx-auto bg-slate-100 rounded-full flex items-center justify-center">
                  <Bot className="w-8 h-8 text-slate-400" />
                </div>
                <div>
                  <h3 className="text-lg font-medium text-primary-dark mb-2">
                    {replyToAlert ? "Ready to help with your alert" : "Welcome to OptiBuy Assistant"}
                  </h3>
                  <p className="text-primary-grey text-sm max-w-md">
                    {replyToAlert
                      ? "I'll analyze the alert and provide OptiBuy suggestions to help resolve the issue."
                      : "Start a conversation by asking about suppliers, purchase orders, inventory, or any procurement needs. I'll help you analyze data and make informed decisions."}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            // Show sessions when they exist
            sessions.map((sess) => {
              const total = sess.messages.length
              // first + last only
              const preview = total <= 2 ? sess.messages : [sess.messages[0], sess.messages[total - 1]]

              return (
                <div key={sess.id} className="mb-6">
                  {preview.map((msg) => (
                    <div
                      key={msg.id}
                      className={`flex mb-4 ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
                    >
                      <div
                        className={`max-w-[70%] p-4 rounded-lg ${
                          msg.sender === "user"
                            ? "bg-accent-blue text-white rounded-tr-sm"
                            : "bg-accent-grey text-white rounded-tl-sm"
                        }`}
                        style={
                          msg.sender === "user"
                            ? { borderRadius: "3px" } /* no extra styling for user messages */
                            : {
                                // background: 'linear-gradient(to right,rgb(169, 138, 248),rgb(142, 97, 255))',
                                // color: '#000',
                                padding: "1rem",
                                borderRadius: "3px",
                              }
                        }
                      >
                        {/* Show reply-to alert for the first user message in sessions that have alert context */}
                        {msg.sender === "user" && sess.alertContext && msg.id === 1 && (
                          <div className="mb-3 p-2 bg-white/20 rounded-lg border-l-2 border-white/40">
                            <div className="flex items-center space-x-2 mb-1">
                              {getAlertIcon(sess.alertContext.type)}
                              <span className="text-xs font-medium opacity-80">Replying to Alert</span>
                              <span className="text-xs opacity-60">{sess.alertContext.priority} Priority</span>
                            </div>
                            <p className="text-xs opacity-80 line-clamp-2">{sess.alertContext.message}</p>
                          </div>
                        )}
                        <h3
                          className="mt-4 mb-4"
                          style={{
                            color: msg.sender === "user" ? "white" : "#88D1F1",
                          }}
                        >
                          {msg.name}
                        </h3>
                        <div>
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                              table: ({ node, ...props }) => (
                                <div className="overflow-x-auto mb-4 mt-4">
                                  <table
                                    className="border-collapse border border-gray-300 min-w-full"
                                    style={{ color: "black" }}
                                    {...props}
                                  />
                                </div>
                              ),
                              thead: ({ node, ...props }) => <thead className="bg-gray-100" {...props} />,
                              th: ({ node, ...props }) => (
                                <th className="border border-gray-300 px-3 py-1 text-left" {...props} />
                              ),
                              td: ({ node, ...props }) => (
                                <td className="border border-gray-300 px-3 py-1 hover:bg-gray-50" {...props} />
                              ),
                              tr: ({ node, ...props }) => <tr className="odd:bg-white even:bg-gray-50" {...props} />,
                              hr: ({ node, ...props }) => <hr style={{ marginBottom: "1em", marginTop: "1em" }} />,
                              li: ({ node, ...props }) => <li className="mb-1 ml-4 list-disc" {...props} />,
                              ul: ({ node, ...props }) => <ul {...props} style={{ marginBottom: "2em" }} />,
                            }}
                          >
                            {msg.text}
                          </ReactMarkdown>

                          {/* Render attached PDFs as clickable links */}
                          {msg.attachedPdfs && msg.attachedPdfs.length > 0 && (
                            <div className="mt-3 pt-3 border-t border-white/20">
                              <div className="text-xs opacity-80 mb-2" style={{display:"flex",alignItems:"center"}}><Paperclip size={16} className="mr-2"/> Attached Documents:</div>
                              <div className="space-y-1">
                                {msg.attachedPdfs.map((pdf, index) => (
                                  <button
                                    key={index}
                                    onClick={() => openPdfInNewTab(pdf.filename, pdf.data)}
                                    className="block text-left text-sm underline hover:no-underline opacity-90 hover:opacity-100 transition-opacity"
                                    style={{ color: msg.sender === "user" ? "#E0F2FE" : "#BFDBFE" }}
                                  >
                                    {pdf.filename}
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                        <p className="text-xs opacity-70 mt-2">{msg.timestamp}</p>
                      </div>
                    </div>
                  ))}

                  {/* If there are hidden messages, show action buttons */}
                  {total > 2 && (
                    <div className="flex justify-center mb-4 space-x-4">
                      <button
                        onClick={() => setOpenSessionId(sess.id)}
                        className="flex items-center space-x-2 text-primary-grey hover:text-accent-blue"
                      >
                        <Sparkles className="h-5 w-5" />
                        <span className="text-xs opacity-70">See Entire Agentic Conversation</span>
                        {/* Show flagged icon if conversation is flagged */}
                      </button>
                      {sess.isFlagged && (
                        <div className="flex items-center space-x-2 text-primary-grey hover:text-accent-blue">
                          <FlagTriangleRight className="h-5 w-5" />{" "}
                          <span className="text-xs opacity-70">Flagged for Review</span>{" "}
                        </div>
                      )}
                      {/* Session-specific graph button */}
                      <button
                        onClick={() => openGraphModal(sess.id)}
                        className="flex items-center space-x-2 text-primary-grey hover:text-accent-blue"
                      >
                        <Workflow className="h-4 w-4" />
                        <span className="text-xs opacity-70">View Sub-Sectional Graph</span>
                      </button>
                    </div>
                  )}
                </div>
              )
            })
          )}

          {isTyping && (
            <div className="flex justify-start mb-4">
              <div
                className="bg-accent-grey text-white p-4 rounded-lg rounded-tl-sm animate-pulse"
                style={{ borderRadius: "3px" }}
              >
                <div className="flex space-x-2">
                  {[0, 1, 2].map((i) => (
                    <div
                      key={i}
                      className="typing-dot w-2 h-2 rounded-full bg-white"
                      style={{ "--dot-index": i } as any}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Hidden file input for PDF upload */}
        <input
          type="file"
          ref={(input) => {
            if (input) {
              input.onclick = () => {
                input.value = ""
              }
            }
          }}
          onChange={handlePdfUpload}
          accept=".pdf"
          multiple
          style={{ display: "none" }}
          id="pdf-upload-input"
        />

        {/* Input Bar */}
        <div className="bg-white rounded-lg border border-secondary-grey">
          {/* Replying to alert preview - shows above input when replying */}
          {replyToAlert && (
            <div className="p-3 border-b border-gray-200 bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex items-start space-x-3 flex-1">
                  <div className="flex items-center space-x-2">
                    {getAlertIcon(replyToAlert.type)}
                    <span className="text-sm font-medium text-gray-700">Replying to Alert</span>
                    <span className={`text-xs px-2 py-1 rounded-full ${getPriorityColor(replyToAlert.priority)}`}>
                      {replyToAlert.priority} Priority
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => {
                    setReplyToAlert(null)
                    sessionStorage.removeItem("replyToAlert")
                  }}
                  className="p-1 hover:bg-gray-200 rounded-full transition-colors"
                >
                  <X className="w-4 h-4 text-gray-500" />
                </button>
              </div>
              <p className="text-sm text-gray-600 mt-2 line-clamp-2 ml-6">{replyToAlert.message}</p>
            </div>
          )}

          {/* PDF upload preview - shows selected PDFs */}
          {selectedPdfs.length > 0 && (
            <div className="p-3 border-b border-gray-200 bg-blue-50">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-blue-700">📎 {selectedPdfs.length} PDF(s) selected</span>
                <button onClick={() => setSelectedPdfs([])} className="text-blue-600 hover:text-blue-800 text-sm">
                  Clear all
                </button>
              </div>
              <div className="space-y-2">
                {selectedPdfs.map((pdf, index) => (
                  <div key={index} className="flex items-center justify-between bg-white rounded p-2 border">
                    <div className="flex items-center space-x-2">
                      <div className="w-8 h-8 bg-red-100 rounded flex items-center justify-center">
                        <span className="text-red-600 text-xs font-bold">PDF</span>
                      </div>
                      <div>
                        <div className="text-sm font-medium text-gray-700">{pdf.name}</div>
                        <div className="text-xs text-gray-500">{(pdf.size / 1024 / 1024).toFixed(2)} MB</div>
                      </div>
                    </div>
                    <button
                      onClick={() => removePdf(index)}
                      className="p-1 hover:bg-gray-200 rounded-full transition-colors"
                    >
                      <X className="w-4 h-4 text-gray-500" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Input field container */}
          <div className="flex items-center p-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={onKeyPress}
              placeholder={
                replyToAlert ? "Ask for OptiBuy suggestions..." : "Ask OptiBuy about suppliers, POs, inventory..."
              }
              className="flex-1 p-3 rounded-lg border border-secondary-grey focus:border-accent-blue focus:outline-none bg-transparent"
            />
            <button
              onClick={() => document.getElementById("pdf-upload-input")?.click()}
              className="mx-2 p-2 text-primary-grey hover:text-accent-blue transition-colors"
              disabled={isUploadingPdfs}
              title="Upload PDF documents"
            >
              <Paperclip className={`h-5 w-5 ${isUploadingPdfs ? "animate-pulse" : ""}`} />
            </button>
            <button className="mx-2 p-2 text-primary-grey hover:text-accent-blue transition-colors">
              <Mic className="h-5 w-5" />
            </button>
            <button
              onClick={handleSend}
              disabled={isUploadingPdfs}
              className="bg-accent-grey text-white p-3 rounded-full hover:bg-accent-grey/80 transition-all disabled:opacity-50"
            >
              {isUploadingPdfs ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <SendHorizontal className="h-5 w-5" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Full‐history modal for whichever session is open */}
      {openSessionId != null && (
        <Modal onClose={() => setOpenSessionId(null)}>
          <div className="fixed inset-0 flex bg-white items-center justify-center p-4" style={{ borderRadius: "3px" }}>
            <div
              className="rounded-lg p-6 overflow-y-auto"
              style={{ borderRadius: "3px", maxHeight: "90vh", width: "100%" }}
            >
              <div className="flex justify-between items-center mb-4">
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-semibold text-primary-dark">Full Conversation</h2>
                  {/* Show flagged icon if conversation is flagged */}
                  {sessions.find((s) => s.id === openSessionId)?.isFlagged && (
                    <FlagTriangleRight className="h-5 w-5 text-red-500" />
                  )}
                </div>
                <div className="flex gap-2">
                  {/* *** UPDATED: Flag conversation button - now uses new flow */}
                  {!sessions.find((s) => s.id === openSessionId)?.isFlagged && (
                    <button
                      onClick={() => initiateFlagConversation(openSessionId, true)} // true = reopen conversation after flagging
                      className="flex items-center space-x-2 bg-red-500 text-white px-3 py-2 rounded-lg hover:bg-red-600 transition-colors"
                    >
                      <Flag className="h-4 w-4" />
                      <span className="text-sm">Flag Conversation</span>
                    </button>
                  )}
                  {/* Graph button in full conversation modal */}
                  <button
                    onClick={() => {
                      setOpenSessionId(null)
                      openGraphModal(openSessionId)
                    }}
                    className="flex items-center space-x-2 bg-accent-blue text-white px-3 py-2 rounded-lg hover:bg-accent-blue/80 transition-colors"
                  >
                    <Workflow className="h-4 w-4" />
                    <span className="text-sm">View Graph</span>
                  </button>
                </div>
              </div>
              <div className="space-y-4">
                {sessions
                  .find((s) => s.id === openSessionId)!
                  .messages.map((msg) => (
                    <div key={msg.id} className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}>
                      <div
                        className={`max-w-[80%] p-3 rounded-lg ${
                          msg.sender === "user"
                            ? "bg-accent-blue text-white rounded-tr-sm"
                            : "bg-accent-grey text-white rounded-tl-sm"
                        }`}
                        style={
                          msg.sender === "user"
                            ? { borderRadius: "3px" } /* no extra styling for user messages */
                            : {
                                // background: 'linear-gradient(to right,rgb(196, 172, 255),rgb(220, 206, 255))',
                                // color: '#000',
                                padding: "1rem",
                                borderRadius: "3px",
                              }
                        }
                      >
                        {/* Show reply-to alert for the first user message in sessions that have alert context */}
                        {msg.sender === "user" &&
                          sessions.find((s) => s.id === openSessionId)?.alertContext &&
                          msg.id === 1 && (
                            <div className="mb-3 p-2 bg-white/20 rounded-lg border-l-2 border-white/40">
                              <div className="flex items-center space-x-2 mb-1">
                                {getAlertIcon(sessions.find((s) => s.id === openSessionId)!.alertContext!.type)}
                                <span className="text-xs font-medium opacity-80">Replying to Alert</span>
                                <span className="text-xs opacity-60">
                                  {sessions.find((s) => s.id === openSessionId)!.alertContext!.priority}
                                </span>
                              </div>
                              <p className="text-xs opacity-80 line-clamp-2">
                                {sessions.find((s) => s.id === openSessionId)!.alertContext!.message}
                              </p>
                            </div>
                          )}
                        <h3
                          className="mt-4 mb-4"
                          style={{
                            color: msg.sender === "user" ? "white" : "#88D1F1",
                          }}
                        >
                          {msg.name}
                        </h3>
                        <div>
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                              table: ({ node, ...props }) => (
                                <div className="overflow-x-auto mb-4 mt-4">
                                  <table
                                    className="border-collapse border border-gray-300 min-w-full"
                                    style={{ color: "black" }}
                                    {...props}
                                  />
                                </div>
                              ),
                              thead: ({ node, ...props }) => <thead className="bg-gray-100" {...props} />,
                              th: ({ node, ...props }) => (
                                <th className="border border-gray-300 px-3 py-1 text-left" {...props} />
                              ),
                              td: ({ node, ...props }) => (
                                <td className="border border-gray-300 px-3 py-1 hover:bg-gray-50" {...props} />
                              ),
                              tr: ({ node, ...props }) => <tr className="odd:bg-white even:bg-gray-50" {...props} />,
                              hr: ({ node, ...props }) => <hr style={{ marginBottom: "1em", marginTop: "1em" }} />,
                              li: ({ node, ...props }) => <li className="mb-1 ml-4 list-disc" {...props} />,
                              ul: ({ node, ...props }) => <ul {...props} style={{ marginBottom: "2em" }} />,
                            }}
                          >
                            {msg.text}
                          </ReactMarkdown>

                          {/* Render attached PDFs as clickable links */}
                          {msg.attachedPdfs && msg.attachedPdfs.length > 0 && (
                            <div className="mt-3 pt-3 border-t border-white/20">
                              <div className="text-xs opacity-80 mb-2">📎 Attached Documents:</div>
                              <div className="space-y-1">
                                {msg.attachedPdfs.map((pdf, index) => (
                                  <button
                                    key={index}
                                    onClick={() => openPdfInNewTab(pdf.filename, pdf.data)}
                                    className="block text-left text-sm underline hover:no-underline opacity-90 hover:opacity-100 transition-opacity"
                                    style={{ color: msg.sender === "user" ? "#E0F2FE" : "#BFDBFE" }}
                                  >
                                    {pdf.filename}
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                        <p className="text-xs opacity-70 mt-1">{msg.timestamp}</p>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          </div>
        </Modal>
      )}

      {/* Flag conversation dialog - separate modal */}
      {showFlagDialog && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
            <div className="flex justify-between items-center p-6 border-b">
              <h3 className="text-lg font-semibold text-gray-800">Flag Conversation</h3>
              <button onClick={cancelFlagDialog} className="p-1 hover:bg-gray-100 rounded-full transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Reason for flagging this conversation:
              </label>
              <textarea
                value={flagReason}
                onChange={(e) => setFlagReason(e.target.value)}
                placeholder="Please provide a reason for flagging this conversation..."
                className="w-full h-32 p-3 border border-gray-300 rounded-lg focus:border-red-500 focus:ring-1 focus:ring-red-500 focus:outline-none resize-none"
              />
            </div>

            <div className="flex justify-end gap-3 p-6 border-t bg-gray-50">
              <button
                onClick={cancelFlagDialog}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                disabled={isSubmittingFlag}
              >
                Cancel
              </button>
              <button
                onClick={handleFlagConversation}
                disabled={!flagReason.trim() || isSubmittingFlag}
                className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
              >
                {isSubmittingFlag ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Submitting...
                  </>
                ) : (
                  <>
                    <Flag className="w-4 h-4" />
                    Submit Flag
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Graph visualization modal */}
      {showGraphModal && (
        <Modal onClose={() => setShowGraphModal(false)} fullScreen>
          <div className="w-full h-full flex flex-col p-4">
            {/* Header */}
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold text-gray-800">
                {graphSessionId ? `Sub-Section Flow: ${graphSessionId} ` : "Complete Conversation Flow"}
              </h2>
              <div className="flex gap-2">
                <button
                  onClick={handleZoomIn}
                  className="bg-white/80 backdrop-blur p-2 rounded border border-gray-200 hover:bg-white"
                >
                  <ZoomIn className="w-4 h-4" />
                </button>
                <button
                  onClick={handleZoomOut}
                  className="bg-white/80 backdrop-blur p-2 rounded border border-gray-200 hover:bg-white"
                >
                  <ZoomOut className="w-4 h-4" />
                </button>
                <button
                  onClick={handleReset}
                  className="bg-white/80 backdrop-blur p-2 rounded border border-gray-200 hover:bg-white"
                  title="Reset view and node positions"
                >
                  <RotateCcw className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Graph Container */}
            <div className="flex-1 relative bg-gradient-to-br from-slate-50 to-blue-50 overflow-hidden rounded-lg">
              {/* Instructions */}
              <div className="absolute top-4 left-4 z-10 bg-white/90 backdrop-blur rounded-lg p-3 shadow-sm text-sm text-gray-600">
                <div className="font-medium mb-1">💡 Graph Controls:</div>
                <div>• Drag nodes to rearrange</div>
                <div>• Click & drag background to pan</div>
                <div>• Use zoom controls to scale</div>
                <div>• Click nodes to see details</div>
              </div>

              {/* Graph SVG */}
              <svg
                ref={svgRef}
                width="100%"
                height="100%"
                viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
                className={isDraggingNode ? "cursor-grabbing" : "cursor-grab"}
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseUp}
              >
                <defs>
                  <linearGradient id="edgeGradientModal" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.6" />
                    <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.8" />
                  </linearGradient>
                  <marker
                    id="arrowheadModal"
                    markerWidth="10"
                    markerHeight="8"
                    refX="9"
                    refY="4"
                    orient="auto"
                    markerUnits="strokeWidth"
                  >
                    <polygon points="0 0, 10 4, 0 8" fill="#3b82f6" stroke="#3b82f6" strokeWidth="0.5" />
                  </marker>
                  <pattern id="dotsModal" x="0" y="0" width="40" height="40" patternUnits="userSpaceOnUse">
                    <circle cx="4" cy="4" r="2" fill="#e2e8f0" />
                  </pattern>
                </defs>

                <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
                  <rect width={SVG_WIDTH} height={SVG_HEIGHT} fill="url(#dotsModal)" />

                  {/* Edges */}
                  {graphEdges.map((edge) => {
                    const sourceNode = graphNodes.find((n) => n.id === edge.source)
                    const targetNode = graphNodes.find((n) => n.id === edge.target)

                    if (!sourceNode || !targetNode) return null

                    const dx = targetNode.x - sourceNode.x
                    const dy = targetNode.y - sourceNode.y
                    const distance = Math.sqrt(dx * dx + dy * dy)

                    const nodeRadius = 50
                    const startX = sourceNode.x + (dx / distance) * nodeRadius
                    const startY = sourceNode.y + (dy / distance) * nodeRadius
                    const endX = targetNode.x - (dx / distance) * nodeRadius
                    const endY = targetNode.y - (dy / distance) * nodeRadius

                    const midX = (startX + endX) / 2
                    const midY = (startY + endY) / 2
                    const offset = distance * 0.15

                    const controlX = midX + (dy / distance) * offset
                    const controlY = midY - (dx / distance) * offset

                    const pathData = `M ${startX} ${startY} Q ${controlX} ${controlY} ${endX} ${endY}`

                    return (
                      <g key={edge.id}>
                        <path
                          d={pathData}
                          stroke="url(#edgeGradientModal)"
                          strokeWidth={Math.min(3 + edge.count * 1.5, 10)}
                          fill="none"
                          markerEnd="url(#arrowheadModal)"
                          className="transition-all duration-300"
                          opacity="0.8"
                        />
                      </g>
                    )
                  })}

                  {/* Nodes */}
                  {graphNodes.map((node) => {
                    const Icon = node.icon
                    const isNodeSelected = selectedNode === node.id
                    const isBeingDragged = draggedNodeId === node.id

                    return (
                      <g
                        key={node.id}
                        className={`transition-all duration-200 hover:opacity-80 ${
                          isBeingDragged ? "cursor-grabbing" : "cursor-grab"
                        }`}
                        onMouseDown={(e) => handleNodeMouseDown(e, node.id)}
                        onClick={() => setSelectedNode(isNodeSelected ? null : node.id)}
                      >
                        <circle
                          cx={node.x + 3}
                          cy={node.y + 3}
                          r="50"
                          fill="rgba(0,0,0,0.1)"
                          className="transition-all duration-200"
                        />
                        <circle
                          cx={node.x}
                          cy={node.y}
                          r="50"
                          fill="white"
                          stroke={isBeingDragged ? "#f59e0b" : node.borderColor}
                          strokeWidth={isNodeSelected ? "5" : isBeingDragged ? "4" : "3"}
                          className="transition-all duration-200"
                        />
                        <circle
                          cx={node.x}
                          cy={node.y}
                          r="30"
                          fill={node.color}
                          className="transition-all duration-200"
                        />
                        <foreignObject
                          x={node.x - 12}
                          y={node.y - 12}
                          width="24"
                          height="24"
                          className="pointer-events-none"
                        >
                          <div className="w-6 h-6 text-white">
                            <Icon className="w-6 h-6" />
                          </div>
                        </foreignObject>
                        <text
                          x={node.x}
                          y={node.y + 75}
                          textAnchor="middle"
                          className="text-sm font-semibold fill-gray-700 pointer-events-none"
                          style={{ fontSize: "16px" }}
                        >
                          {node.label}
                        </text>
                        {node.messageCount > 1 && (
                          <>
                            <circle
                              cx={node.x + 35}
                              cy={node.y - 35}
                              r="18"
                              fill={node.color}
                              stroke="white"
                              strokeWidth="3"
                              className="pointer-events-none"
                            />
                            <text
                              x={node.x + 35}
                              y={node.y - 28}
                              textAnchor="middle"
                              className="text-sm font-bold fill-white pointer-events-none"
                              style={{ fontSize: "14px" }}
                            >
                              {node.messageCount}
                            </text>
                          </>
                        )}
                      </g>
                    )
                  })}
                </g>
              </svg>

              {/* Selected node info - simplified without messages */}
              {selectedNode && (
                <div className="absolute bottom-4 left-4 bg-white/95 backdrop-blur rounded-lg p-4 shadow-lg max-w-md">
                  {(() => {
                    const node = graphNodes.find((n) => n.id === selectedNode)
                    if (!node) return null

                    return (
                      <div className="space-y-3">
                        <div className="flex items-center gap-2">
                          <div
                            className="w-10 h-10 rounded-full flex items-center justify-center"
                            style={{ backgroundColor: node.color }}
                          >
                            <node.icon className="w-5 h-5 text-white" />
                          </div>
                          <div>
                            <div className="font-semibold text-base">{node.label}</div>
                            <div className="text-sm text-gray-500 capitalize">{node.role}</div>
                          </div>
                        </div>
                        <div className="text-sm text-gray-600">
                          <div>Messages: {node.messageCount}</div>
                          {node.name && <div>Name: {node.name}</div>}
                        </div>
                      </div>
                    )
                  })()}
                </div>
              )}
            </div>

            {/* Stats Footer */}
            <div className="mt-4 p-3 mb-4 border-t bg-gray-50 rounded-lg">
              <div className="grid grid-cols-4 gap-4 text-center">
                <div>
                  <div className="text-xl font-bold text-blue-600">
                    {convertSessionsToGraphData(graphSessionId).length}
                  </div>
                  <div className="text-sm text-gray-600">Total Messages</div>
                </div>
                <div>
                  <div className="text-xl font-bold text-green-600">{graphNodes.length}</div>
                  <div className="text-sm text-gray-600">Participants</div>
                </div>
                <div>
                  <div className="text-xl font-bold text-purple-600">{graphEdges.length}</div>
                  <div className="text-sm text-gray-600">Connections</div>
                </div>
                <div>
                  <div className="text-xl font-bold text-orange-600">
                    {new Set(convertSessionsToGraphData(graphSessionId).map((msg) => msg.role)).size}
                  </div>
                  <div className="text-sm text-gray-600">Role Types</div>
                </div>
              </div>
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}
