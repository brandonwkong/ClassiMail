"use client"

import { useEffect, useState, useRef, useCallback } from "react"
import { RefreshCcw, Mail, Briefcase, XCircle, Award, Clock, AlertCircle, TrendingUp, BarChart3, ExternalLink, Sparkles } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

interface Email {
  id: string
  sender_name: string
  subject: string
  body?: string
  category: string
  rank_score?: number
  position?: number
  features?: Record<string, any>
}

interface InteractionStats {
  click?: number
  open?: number
  skip?: number
  [key: string]: number | undefined
}

// Track emails that have been seen (in viewport) but not clicked
interface SeenEmail {
  id: string
  position: number
  seenAt: number
  clicked: boolean
}

export default function EmailClassification() {
  const [emails, setEmails] = useState<Email[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeCategory, setActiveCategory] = useState("all")
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [expandedEmail, setExpandedEmail] = useState<string | null>(null)
  const [stats, setStats] = useState<InteractionStats>({})
  const [showStats, setShowStats] = useState(false)
  const clickTimeRef = useRef<number>(0)
  const seenEmailsRef = useRef<Map<string, SeenEmail>>(new Map())
  const clickedEmailsRef = useRef<Set<string>>(new Set())

  // Log interaction to backend
  const logInteraction = useCallback(async (
    emailId: string,
    action: "click" | "open" | "skip",
    position?: number,
    timeSpentMs?: number
  ) => {
    try {
      await fetch("http://localhost:5000/interact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email_id: emailId,
          action,
          position,
          time_spent_ms: timeSpentMs,
        }),
      })
    } catch (err) {
      console.error("Failed to log interaction:", err)
    }
  }, [])

  // Log skips for emails that were seen but not clicked
  const logSkips = useCallback(() => {
    const now = Date.now()
    const SKIP_THRESHOLD_MS = 2000 // Must be visible for 2s to count as "seen"

    seenEmailsRef.current.forEach((seen, emailId) => {
      const wasVisible = now - seen.seenAt >= SKIP_THRESHOLD_MS
      const wasClicked = clickedEmailsRef.current.has(emailId)

      if (wasVisible && !wasClicked) {
        logInteraction(emailId, "skip", seen.position)
      }
    })

    // Clear after logging
    seenEmailsRef.current.clear()
  }, [logInteraction])

  // Track email visibility with Intersection Observer
  const observeEmail = useCallback((element: HTMLElement | null, email: Email) => {
    if (!element) return

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            // Email became visible
            if (!seenEmailsRef.current.has(email.id)) {
              seenEmailsRef.current.set(email.id, {
                id: email.id,
                position: email.position || 0,
                seenAt: Date.now(),
                clicked: false,
              })
            }
          }
        })
      },
      { threshold: 0.5 } // 50% visible counts as "seen"
    )

    observer.observe(element)
    return () => observer.disconnect()
  }, [])

  // Log skips when user leaves the page
  useEffect(() => {
    const handleBeforeUnload = () => {
      logSkips()
    }

    window.addEventListener("beforeunload", handleBeforeUnload)
    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload)
      logSkips() // Also log when component unmounts
    }
  }, [logSkips])

  // Fetch interaction stats
  const fetchStats = async () => {
    try {
      const res = await fetch("http://localhost:5000/stats")
      if (res.ok) {
        const data = await res.json()
        setStats(data)
      }
    } catch (err) {
      console.error("Failed to fetch stats:", err)
    }
  }

  // Handle email click
  const handleEmailClick = (email: Email) => {
    // Mark as clicked so it won't be logged as skipped
    clickedEmailsRef.current.add(email.id)

    if (expandedEmail === email.id) {
      // Closing - log time spent
      const timeSpent = Date.now() - clickTimeRef.current
      logInteraction(email.id, "open", email.position, timeSpent)
      setExpandedEmail(null)
    } else {
      // Opening - start timer
      clickTimeRef.current = Date.now()
      logInteraction(email.id, "click", email.position)
      setExpandedEmail(email.id)
    }
  }

  const fetchEmails = async () => {
    // Log skips for previous emails before fetching new ones
    logSkips()

    setIsLoading(true)
    setError(null)

    // Reset tracking for new email set
    seenEmailsRef.current.clear()
    clickedEmailsRef.current.clear()

    try {
      const res = await fetch("http://localhost:5000/emails")
      if (!res.ok) throw new Error("Failed to fetch emails")
      const data = await res.json()
      setEmails(data)
    } catch (err) {
      setError("Could not load emails. Please try again.")
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchEmails()
  }, [])

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const loggedIn = params.get("logged_in") === "true"
    if (loggedIn) {
      setIsLoggedIn(true)
      localStorage.setItem("logged_in", "true")
      window.history.replaceState(null, "", window.location.pathname) // remove ?logged_in from URL
    } else {
      const stored = localStorage.getItem("logged_in") === "true"
      setIsLoggedIn(stored)
    }
  }, [])
  

  // Extract unique categories from emails
  const categories = ["all", "recommended", ...Array.from(new Set(emails.map((email) => email.category.toLowerCase())))]

  // Filter and sort emails based on active category
  const filteredEmails = (() => {
    let result;
    if (activeCategory === "all") {
      result = emails
    } else if (activeCategory === "recommended") {
      // Sort by rank_score descending
      result = [...emails].sort((a, b) => (b.rank_score || 0) - (a.rank_score || 0))
      console.log("Recommended emails sorted:", result.map(e => ({
        subject: e.subject.slice(0, 30),
        rank: e.rank_score,
        category: e.category
      })))
    } else {
      result = emails.filter((email) => email.category.toLowerCase() === activeCategory)
    }
    
    // Update positions for the filtered/sorted list
    result.forEach((email, index) => {
      email.position = index + 1
    })
    
    return result
  })()

  // Debug: Log active category changes
  useEffect(() => {
    console.log("Active category changed to:", activeCategory)
  }, [activeCategory])

  const getCategoryIcon = (category: string) => {
    switch (category.toLowerCase()) {
      case "job offer":
        return <Briefcase className="h-4 w-4" />
      case "rejection":
        return <XCircle className="h-4 w-4" />
      case "interview":
        return <Award className="h-4 w-4" />
      case "follow-up":
        return <Clock className="h-4 w-4" />
      default:
        return <Mail className="h-4 w-4" />
    }
  }

  const getCategoryColor = (category: string) => {
    switch (category.toLowerCase()) {
      case "job offer":
        return "bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20"
      case "rejection":
        return "bg-rose-500/10 text-rose-500 hover:bg-rose-500/20"
      case "interview":
        return "bg-violet-500/10 text-violet-500 hover:bg-violet-500/20"
      case "follow-up":
        return "bg-amber-500/10 text-amber-500 hover:bg-amber-500/20"
      default:
        return "bg-sky-500/10 text-sky-500 hover:bg-sky-500/20"
    }
  }
  if (!isLoggedIn) {
    return (
      <div className="flex flex-col justify-center items-center min-h-screen bg-black text-white gap-6">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
          ClassiMail
        </h1>
        <button
          className="px-4 py-2 bg-gradient-to-r from-purple-500 to-cyan-500 rounded-md font-semibold"
          onClick={() => {
            window.location.href = 'http://localhost:5000/auth'
          }}
        >
          Login with Google
        </button>
      </div>
    )
  }  

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="container mx-auto px-4 py-8">
        <header className="mb-8">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent">
              ClassiMail
            </h1>
            <div className="flex gap-2">
              <Button
                onClick={() => {
                  setShowStats(!showStats)
                  if (!showStats) fetchStats()
                }}
                variant="outline"
                className="border-gray-700 bg-gray-800 text-gray-100 hover:bg-gray-700 hover:border-gray-500"
              >
                <BarChart3 className="h-4 w-4 mr-2" />
                Stats
              </Button>

              <Button
                onClick={fetchEmails}
                variant="outline"
                className="group border-gray-700 bg-gray-800 text-gray-100 hover:bg-gray-700 hover:border-gray-500"
                disabled={isLoading}
              >
                <RefreshCcw className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : "group-hover:animate-spin"}`} />
                Refresh
              </Button>

              <Button
                onClick={() => {
                  localStorage.removeItem("logged_in")
                  setIsLoggedIn(false)
                  window.location.href = "/"
                }}
              >
                Logout
              </Button>

            </div>
          </div>
          <div className="h-0.5 w-full bg-gradient-to-r from-purple-500 via-cyan-500 to-purple-500 rounded-full" />
        </header>

        {/* Stats Panel */}
        {showStats && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="mb-6 p-4 rounded-lg bg-gray-900/50 border border-gray-800"
          >
            <h3 className="text-sm font-semibold text-gray-300 mb-3 flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Interaction Stats (for CTR training)
            </h3>
            <div className="flex gap-4 flex-wrap">
              {Object.entries(stats).length > 0 ? (
                Object.entries(stats).map(([action, count]) => (
                  <div key={action} className="bg-gray-800 px-3 py-2 rounded-md">
                    <span className="text-gray-400 text-sm">{action}:</span>
                    <span className="text-white font-mono ml-2">{count}</span>
                  </div>
                ))
              ) : (
                <p className="text-gray-500 text-sm">No interactions logged yet. Click on emails to start collecting data.</p>
              )}
            </div>
          </motion.div>
        )}

        {error && (
          <div className="flex items-center gap-2 p-4 mb-6 rounded-lg bg-red-500/10 text-red-400 border border-red-500/20">
            <AlertCircle className="h-5 w-5" />
            <p>{error}</p>
          </div>
        )}

        {/* Custom Filter Tabs - Fixed with no gaps */}
        <div className="mb-6 overflow-x-auto">
          <div className="flex bg-gray-900/50 border border-gray-800 rounded-md w-fit">
            {categories.map((category, index) => (
              <button
                key={category}
                onClick={() => setActiveCategory(category)}
                className={`px-4 py-2 text-sm font-medium transition-all duration-200 border-r border-gray-800 last:border-r-0
                  ${
                    activeCategory === category
                      ? category === "recommended"
                        ? "bg-gradient-to-r from-purple-600 to-cyan-600 text-white"
                        : "bg-gray-800 text-white"
                      : category === "recommended"
                        ? "text-purple-400 hover:bg-gray-800/50 hover:text-purple-300"
                        : "text-gray-400 hover:bg-gray-800/50 hover:text-gray-200"
                  }`}
                style={{ marginLeft: index === 0 ? "0" : "-1px" }}
              >
                <span className="flex items-center gap-1.5">
                  {category === "recommended" && <Sparkles className="h-3.5 w-3.5" />}
                  {category.charAt(0).toUpperCase() + category.slice(1)}
                </span>
              </button>
            ))}
          </div>
        </div>

        <div className="grid gap-4">
          {isLoading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <Card key={i} className="bg-gray-900/50 border-gray-800">
                <CardContent className="p-0">
                  <div className="p-4" />
                </CardContent>
              </Card>
            ))
          ) : (
            <AnimatePresence mode="popLayout">
              {filteredEmails.map((email, index) => (
                <motion.div
                  key={email.id || index}
                  layout
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.3, ease: "easeInOut" }}
                >
                  <Card
                    ref={(el) => observeEmail(el, email)}
                    className={`overflow-hidden bg-gray-900/50 border-gray-800 hover:bg-gray-900 transition-all duration-300 cursor-pointer ${
                      expandedEmail === email.id ? "ring-1 ring-purple-500/50" : ""
                    }`}
                    onClick={() => handleEmailClick(email)}
                  >
                    <CardContent className="p-0">
                      <div className="p-4 flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2">
                        <div className="text-center sm:text-left flex-1">
                          <div className="flex items-center gap-2 justify-center sm:justify-start">
                            {/* Rank position badge */}
                            <span className="text-xs font-mono text-gray-500">#{email.position || index + 1}</span>
                            <h2 className="font-medium text-white">{email.subject}</h2>
                          </div>
                          <p className="text-sm text-gray-400">{email.sender_name}</p>
                        </div>

                        <div className="flex items-center gap-2 justify-center sm:justify-end">
                          {/* Rank score indicator */}
                          {email.rank_score !== undefined && (
                            <div className="flex items-center gap-1 text-xs text-gray-500" title="Rank Score">
                              <TrendingUp className="h-3 w-3" />
                              <span className="font-mono">{(email.rank_score * 100).toFixed(0)}%</span>
                            </div>
                          )}

                          <Badge className={`${getCategoryColor(email.category)} transition-colors duration-300`}>
                            <span className="flex items-center gap-1.5">
                              {getCategoryIcon(email.category)}
                              {email.category}
                            </span>
                          </Badge>
                        </div>
                      </div>

                      {/* Expanded details */}
                      <AnimatePresence>
                        {expandedEmail === email.id && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: "auto", opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            className="border-t border-gray-800 bg-gray-900/30"
                          >
                            <div className="p-4 text-sm">
                              {/* Action buttons */}
                              <div className="flex items-center gap-3 mb-4">
                                <a
                                  href={`https://mail.google.com/mail/u/0/#inbox/${email.id}`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium rounded transition-colors"
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  <ExternalLink className="h-3 w-3" />
                                  Open in Gmail
                                </a>
                                <span className="text-gray-500 text-xs">Click card again to close</span>
                              </div>

                              {/* Email body */}
                              {email.body && (
                                <div>
                                  <div className="bg-gray-800/50 p-3 rounded max-h-64 overflow-y-auto">
                                    <pre className="text-gray-300 text-xs whitespace-pre-wrap font-sans leading-relaxed">
                                      {email.body.slice(0, 2000)}
                                      {email.body.length > 2000 && (
                                        <span className="text-gray-500">... (truncated)</span>
                                      )}
                                    </pre>
                                  </div>
                                </div>
                              )}
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </AnimatePresence>

          )}

          {!isLoading && emails.length > 0 && filteredEmails.length === 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center justify-center p-12 text-center"
            >
              <Mail className="h-12 w-12 text-gray-600 mb-4" />
              <h3 className="text-xl font-medium text-gray-400">No emails found</h3>
              <p className="text-gray-500 mt-2">No emails in the "{activeCategory}" category</p>
            </motion.div>
          )}

          {!isLoading && emails.length === 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center justify-center p-12 text-center"
            >
              <Mail className="h-12 w-12 text-gray-600 mb-4" />
              <h3 className="text-xl font-medium text-gray-400">No emails found</h3>
              <p className="text-gray-500 mt-2">Check your connection or try refreshing</p>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  )
}
