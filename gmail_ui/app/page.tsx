"use client"

import { useEffect, useState } from "react"
import { RefreshCcw, Mail, Briefcase, XCircle, Award, Clock, AlertCircle } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

interface Email {
  id: string
  sender_name: string
  subject: string
  category: string
}

export default function EmailClassification() {
  const [emails, setEmails] = useState<Email[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeCategory, setActiveCategory] = useState("all")
  const [isLoggedIn, setIsLoggedIn] = useState(false)

  const fetchEmails = async () => {
    setIsLoading(true)
    setError(null)

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
  const categories = ["all", ...Array.from(new Set(emails.map((email) => email.category.toLowerCase())))]

  // Filter emails based on active category
  const filteredEmails =
    activeCategory === "all" ? emails : emails.filter((email) => email.category.toLowerCase() === activeCategory)

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
                  window.location.href = "/" // or reload to clear component state
                }}
              >
                Logout
              </Button>

            </div>
          </div>
          <div className="h-0.5 w-full bg-gradient-to-r from-purple-500 via-cyan-500 to-purple-500 rounded-full" />
        </header>

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
                      ? "bg-gray-800 text-white"
                      : "text-gray-400 hover:bg-gray-800/50 hover:text-gray-200"
                  }`}
                style={{ marginLeft: index === 0 ? "0" : "-1px" }} // Negative margin to eliminate gaps
              >
                {category.charAt(0).toUpperCase() + category.slice(1)}
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
                  <Card className="overflow-hidden bg-gray-900/50 border-gray-800 hover:bg-gray-900 transition-all duration-300">
                    <CardContent className="p-0">
                    <div className="p-4 flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2">
                      <div className="text-center sm:text-left">
                        <h2 className="font-medium text-white">{email.subject}</h2>
                        <p className="text-sm text-gray-400">{email.sender_name}</p>
                      </div>

                      <Badge className={`${getCategoryColor(email.category)} transition-colors duration-300`}>
                        <span className="flex items-center gap-1.5">
                          {getCategoryIcon(email.category)}
                          {email.category}
                        </span>
                      </Badge>
                    </div>

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
