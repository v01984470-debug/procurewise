"use client"

import { useState, useEffect, useRef, type KeyboardEvent } from "react"
import {
  Paperclip,
  Mic,
  SendHorizontal,
  Workflow,
  User,
  Bot,
  Wrench,
  Database,
  ArrowLeft,
  AlertTriangle,
  Clock,
  Package,
  Sparkles,
  FlagTriangleRight,
  ZoomIn,
  ZoomOut,
  RotateCcw,
} from "lucide-react"
import { useRouter } from "next/navigation"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import Modal from "@/components/modal"

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
}

interface Session {
  id: number
  messages: Message[]
  isFlagged?: boolean
  alertContext?: AlertContext | null // Add this line
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
  steps?: number[]
}

interface GraphChatMessage {
  content: string
  role: string
  name?: string
  tool_calls?: any[]
  tool_responses?: any[]
}

export default function ChatWindow() {
  const router = useRouter()
  const [replyToAlert, setReplyToAlert] = useState<AlertContext | null>(null)

  // All query‐sessions live here
  const [sessions, setSessions] = useState<Session[]>([])
  const [input, setInput] = useState<string>("")
  const [isTyping, setIsTyping] = useState<boolean>(false)

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
  const [flagSessionId, setFlagSessionId] = useState<number | null>(null)
  const [flagReason, setFlagReason] = useState<string>("")
  const [isSubmittingFlag, setIsSubmittingFlag] = useState<boolean>(false)
  const [shouldReopenConversation, setShouldReopenConversation] = useState<boolean>(false)

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
      // Remove this line: setInput(`Please provide OptiBuy suggestions for: ${alertContext.message}`)
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

  const navigateBackToAlerts = () => {
    // Clear the stored alert context
    sessionStorage.removeItem("replyToAlert")
    router.push("/")
  }

  const clearReplyToAlert = () => {
    setReplyToAlert(null)
    setInput("")
    sessionStorage.removeItem("replyToAlert")
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

  // Send the user's query and create a new session
  const handleSend = async () => {
    const query = input.trim()
    if (!query) return

    // Prepare the message text with alert context if replying to alert
    const messageText = query
    let apiQuery = query

    if (replyToAlert) {
      // For API: include alert context
      apiQuery = `Replying to alert: "${replyToAlert.message}" (Priority: ${replyToAlert.priority}, Type: ${replyToAlert.type})\n\nUser message: ${query}`
    }

    // 1) Create the optimistic user‐message
    const userMsg: Message = {
      id: 1,
      text: messageText,
      sender: "user",
      name: "You",
      timestamp: new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
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
    setInput("")
    setIsTyping(true)

    try {
      // 4) Fire off the backend call with alert context
      const resp = await fetch("http://localhost:8001/supplier-analysis", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: apiQuery, // Send the query with alert context
          chat_summary: chatSummary,
        }),
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
    } catch (error) {
      console.error("Error fetching chat:", error)
      // On error, append a failure notice into that session
      setSessions((prev) =>
        prev.map((sess) =>
          sess.id === newSession.id
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
            : sess,
        ),
      )
    } finally {
      setIsTyping(false)
    }
  }

  const onKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault()
      handleSend()
    }
  }

  // Flag conversation
  const flagConversation = async () => {
    if (!flagSessionId || !flagReason.trim()) return

    setIsSubmittingFlag(true)
    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1000))

      // Update the session to be flagged
      setSessions((prev) =>
        prev.map((session) => (session.id === flagSessionId ? { ...session, isFlagged: true } : session)),
      )

      // Close the dialog and reset state
      setShowFlagDialog(false)
      setFlagReason("")
      setFlagSessionId(null)

      // Reopen conversation if requested
      if (shouldReopenConversation) {
        // Simulate API call to reopen conversation
        await new Promise((resolve) => setTimeout(resolve, 1000))
        setShouldReopenConversation(false)
      }
    } catch (error) {
      console.error("Error flagging conversation:", error)
      // Handle error appropriately
    } finally {
      setIsSubmittingFlag(false)
    }
  }

  // Graph visualization functions
  const openGraphModal = (sessionId?: number) => {
    setGraphSessionId(sessionId)
    generateGraph(sessionId)
    setShowGraphModal(true)
  }

  const generateGraph = (sessionId?: number) => {
    const chatHistory = convertSessionsToGraphData(sessionId)

    // Initialize nodes and edges
    const nodesMap: { [key: string]: GraphNode } = {}
    const edgesMap: { [key: string]: GraphEdge } = {}

    // Iterate through chat history to create nodes and edges
    chatHistory.forEach((message, index) => {
      const sourceId = message.name || message.role
      const targetId =
        index < chatHistory.length - 1 ? chatHistory[index + 1].name || chatHistory[index + 1].role : null

      // Create or update source node
      if (!nodesMap[sourceId]) {
        nodesMap[sourceId] = {
          id: sourceId,
          label: formatName(sourceId),
          role: message.role,
          name: message.name,
          x: Math.random() * SVG_WIDTH,
          y: Math.random() * SVG_HEIGHT,
          messageCount: 1,
          icon: getNodeIcon(message.role, message.name),
          color: getNodeColor(message.role),
          borderColor: getNodeBorderColor(message.role),
        }
      } else {
        nodesMap[sourceId].messageCount++
      }

      // Create edge if target exists
      if (targetId) {
        const edgeId = `${sourceId}-${targetId}`
        if (!edgesMap[edgeId]) {
          edgesMap[edgeId] = {
            id: edgeId,
            source: sourceId,
            target: targetId,
            count: 1,
            steps: [index, index + 1],
          }
        } else {
          edgesMap[edgeId].count++
          edgesMap[edgeId].steps?.push(index, index + 1)
        }
      }
    })

    // Convert maps to arrays
    const newNodes = Object.values(nodesMap)
    const newEdges = Object.values(edgesMap)

    // Update state
    setGraphNodes(newNodes)
    setGraphEdges(newEdges)
  }

  const handleNodeClick = (nodeId: string) => {
    setSelectedNode(nodeId)
  }

  const handleZoomIn = () => {
    setZoom((prevZoom) => prevZoom * 1.1)
  }

  const handleZoomOut = () => {
    setZoom((prevZoom) => prevZoom / 1.1)
  }

  const handleRotate = () => {
    setPan({ x: 0, y: 0 })
  }

  const handleMouseDown = (event: any) => {
    setIsDragging(true)
    setDragStart({ x: event.clientX - pan.x, y: event.clientY - pan.y })
  }

  const handleMouseMove = (event: any) => {
    if (!isDragging) return

    setPan({
      x: event.clientX - dragStart.x,
      y: event.clientY - dragStart.y,
    })
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  const handleMouseLeave = () => {
    setIsDragging(false)
  }

  const handleNodeMouseDown = (event: any, nodeId: string) => {
    setIsDraggingNode(true)
    setDraggedNodeId(nodeId)
    setNodeDragStart({ x: event.clientX, y: event.clientY })

    // Find the node being dragged
    const draggedNode = graphNodes.find((node) => node.id === nodeId)
    if (draggedNode) {
      setNodeDragOffset({ x: draggedNode.x, y: draggedNode.y })
    }
  }

  const handleNodeMouseMove = (event: any) => {
    if (!isDraggingNode || !draggedNodeId) return

    // Calculate the new position based on the initial offset and mouse movement
    const newX = event.clientX - nodeDragStart.x + nodeDragOffset.x
    const newY = event.clientY - nodeDragStart.y + nodeDragOffset.y

    // Update the node's position in the state
    setGraphNodes((prevNodes) =>
      prevNodes.map((node) => (node.id === draggedNodeId ? { ...node, x: newX, y: newY } : node)),
    )
  }

  const handleNodeMouseUp = () => {
    setIsDraggingNode(false)
    setDraggedNodeId(null)
  }

  return (
    <div className="relative mx-auto" style={{ width: "90%" }}>
      <div className="relative glass-effect rounded-lg shadow-lg p-6">
        <header className="mb-4 flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <button
              onClick={navigateBackToAlerts}
              className="flex items-center space-x-2 text-primary-grey hover:text-accent-blue transition-colors"
            >
              <ArrowLeft className="h-5 w-5" />
              <span>Back to Alerts</span>
            </button>
            <div>
              <h1 className="text-2xl font-bold text-primary-dark mb-2">OptiBuy Assistant</h1>
              <p className="text-primary-grey">
                Ask me about suppliers, purchase orders, inventory, or any procurement needs.
              </p>
            </div>
          </div>
          {/* Global graph view button - only show if there are sessions */}
          {sessions.length > 0 && (
            <button
              onClick={() => {
                /* openGraphModal() */
              }}
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
            // Show sessions when they exist - simplified for brevity
            sessions.map((sess) => {
              const total = sess.messages.length
              const visibleMessages = sess.messages.slice(Math.max(total - 2, 0))

              return (
                <div key={sess.id} className="mb-6">
                  {visibleMessages.map((msg) => (
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
                      </button>
                      {sess.isFlagged && (
                        <div className="flex items-center space-x-2 text-primary-grey hover:text-accent-blue">
                          <FlagTriangleRight className="h-5 w-5" />
                          <span className="text-xs opacity-70">Flagged for Review</span>
                        </div>
                      )}
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
              <div className="bg-accent-grey text-white p-4 rounded-lg animate-pulse">
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

        {/* Input Bar */}
        <div className="bg-white rounded-lg border border-secondary-grey">
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
            <button className="mx-2 p-2 text-primary-grey hover:text-accent-blue transition-colors">
              <Paperclip className="h-5 w-5" />
            </button>
            <button className="mx-2 p-2 text-primary-grey hover:text-accent-blue transition-colors">
              <Mic className="h-5 w-5" />
            </button>
            <button
              onClick={handleSend}
              className="bg-accent-grey text-white p-3 rounded-full hover:bg-accent-grey/80 transition-all"
            >
              <SendHorizontal className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Full conversation modal */}
      {openSessionId !== null && (
        <Modal onClose={() => setOpenSessionId(null)}>
          <div className="bg-white rounded-lg shadow-xl overflow-hidden w-full max-w-3xl">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg font-medium leading-6 text-gray-900">Full Conversation History</h3>
              <div className="mt-2 text-sm text-gray-500">
                {sessions
                  .find((session) => session.id === openSessionId)
                  ?.messages.map((msg) => (
                    <div key={msg.id} className="mb-4">
                      <p className="font-bold">{msg.name}:</p>
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
                      <p className="text-xs text-gray-500">{msg.timestamp}</p>
                    </div>
                  ))}
              </div>
            </div>
            <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
              <button
                type="button"
                className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                onClick={() => setOpenSessionId(null)}
              >
                Close
              </button>
              {!sessions.find((session) => session.id === openSessionId)?.isFlagged && (
                <button
                  type="button"
                  className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:ml-3 sm:w-auto sm:text-sm"
                  onClick={() => {
                    setFlagSessionId(openSessionId)
                    setShowFlagDialog(true)
                    setOpenSessionId(null)
                  }}
                >
                  Flag Conversation
                </button>
              )}
            </div>
          </div>
        </Modal>
      )}

      {/* Flag conversation modal */}
      {showFlagDialog && (
        <Modal onClose={() => setShowFlagDialog(false)}>
          <div className="bg-white rounded-lg shadow-xl overflow-hidden w-full max-w-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg font-medium leading-6 text-gray-900">Flag Conversation for Review</h3>
              <div className="mt-2 text-sm text-gray-500">
                <p>
                  Please provide a reason for flagging this conversation. This will help us review the conversation and
                  improve our services.
                </p>
              </div>
              <div className="mt-5">
                <label htmlFor="flagReason" className="block text-sm font-medium text-gray-700">
                  Reason for Flagging
                </label>
                <div className="mt-1">
                  <textarea
                    id="flagReason"
                    rows={3}
                    className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 mt-1 block w-full sm:text-sm border-gray-300 rounded-md"
                    placeholder="Enter your reason here..."
                    value={flagReason}
                    onChange={(e) => setFlagReason(e.target.value)}
                  />
                </div>
                <div className="flex items-center mt-4">
                  <input
                    id="reopenConversation"
                    type="checkbox"
                    className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                    checked={shouldReopenConversation}
                    onChange={() => setShouldReopenConversation(!shouldReopenConversation)}
                  />
                  <label htmlFor="reopenConversation" className="ml-2 block text-sm text-gray-900">
                    Reopen conversation after flagging
                  </label>
                </div>
              </div>
            </div>
            <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
              <button
                type="button"
                className="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
                onClick={flagConversation}
                disabled={isSubmittingFlag}
              >
                {isSubmittingFlag ? "Flagging..." : "Flag Conversation"}
              </button>
              <button
                type="button"
                className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                onClick={() => setShowFlagDialog(false)}
              >
                Cancel
              </button>
            </div>
          </div>
        </Modal>
      )}

      {/* Graph visualization modal */}
      {showGraphModal && (
        <Modal onClose={() => setShowGraphModal(false)}>
          <div className="bg-white rounded-lg shadow-xl overflow-hidden w-full max-w-5xl">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg font-medium leading-6 text-gray-900">Conversation Graph</h3>
              <div className="mt-2 text-sm text-gray-500">
                <p>Visualize the flow of conversation and interactions between different agents.</p>
              </div>

              <div className="flex justify-end space-x-2 mb-2">
                <button
                  onClick={handleZoomIn}
                  className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
                >
                  <ZoomIn className="h-4 w-4" />
                </button>
                <button
                  onClick={handleZoomOut}
                  className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
                >
                  <ZoomOut className="h-4 w-4" />
                </button>
                <button
                  onClick={handleRotate}
                  className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline"
                >
                  <RotateCcw className="h-4 w-4" />
                </button>
              </div>

              <div className="relative" style={{ width: SVG_WIDTH, height: SVG_HEIGHT }}>
                <svg
                  ref={svgRef}
                  width={SVG_WIDTH}
                  height={SVG_HEIGHT}
                  style={{ border: "1px solid #ccc" }}
                  onMouseDown={handleMouseDown}
                  onMouseMove={handleMouseMove}
                  onMouseUp={handleMouseUp}
                  onMouseLeave={handleMouseLeave}
                >
                  <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
                    {graphEdges.map((edge) => (
                      <line
                        key={edge.id}
                        x1={graphNodes.find((node) => node.id === edge.source)?.x || 0}
                        y1={graphNodes.find((node) => node.id === edge.source)?.y || 0}
                        x2={graphNodes.find((node) => node.id === edge.target)?.x || 0}
                        y2={graphNodes.find((node) => node.id === edge.target)?.y || 0}
                        stroke="#aaa"
                        strokeWidth={2}
                      />
                    ))}
                    {graphNodes.map((node) => (
                      <g
                        key={node.id}
                        transform={`translate(${node.x}, ${node.y})`}
                        onClick={() => handleNodeClick(node.id)}
                        onMouseDown={(e) => handleNodeMouseDown(e, node.id)}
                        onMouseMove={handleNodeMouseMove}
                        onMouseUp={handleNodeMouseUp}
                        style={{ cursor: "pointer" }}
                      >
                        <circle
                          r={20 + node.messageCount}
                          fill={node.color}
                          stroke={node.borderColor}
                          strokeWidth={3}
                        />
                        <node.icon
                          className="h-6 w-6 text-white"
                          style={{ position: "relative", left: -12, top: -12 }}
                        />
                        <text
                          x={0}
                          y={40}
                          textAnchor="middle"
                          fontSize={12}
                          fill="black"
                          style={{ pointerEvents: "none" }}
                        >
                          {node.label}
                        </text>
                      </g>
                    ))}
                  </g>
                </svg>
              </div>
            </div>
            <div className="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
              <button
                type="button"
                className="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
                onClick={() => setShowGraphModal(false)}
              >
                Close
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}
