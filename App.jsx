import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Search, 
  Database, 
  Bot, 
  BarChart3, 
  Settings, 
  FileText, 
  Download,
  Zap,
  Shield,
  Globe,
  Brain,
  Activity,
  Users,
  Clock,
  CheckCircle,
  AlertCircle,
  TrendingUp
} from 'lucide-react'

// 組件導入
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'

// 頁面組件導入
import Dashboard from './components/Dashboard.jsx'
import PatentSearch from './components/PatentSearch.jsx'
import DatabaseManagement from './components/DatabaseManagement.jsx'
import RPAManagement from './components/RPAManagement.jsx'
import Analytics from './components/Analytics.jsx'
import SystemSettings from './components/SystemSettings.jsx'
import Navigation from './components/Navigation.jsx'

import './App.css'

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard')
  const [systemStatus, setSystemStatus] = useState({
    rpaStatus: 'active',
    databaseStatus: 'connected',
    aiStatus: 'ready',
    lastUpdate: new Date().toLocaleString('zh-TW')
  })

  // 模擬系統狀態更新
  useEffect(() => {
    const interval = setInterval(() => {
      setSystemStatus(prev => ({
        ...prev,
        lastUpdate: new Date().toLocaleString('zh-TW')
      }))
    }, 30000) // 每30秒更新一次

    return () => clearInterval(interval)
  }, [])

  const renderCurrentPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard systemStatus={systemStatus} />
      case 'search':
        return <PatentSearch />
      case 'database':
        return <DatabaseManagement />
      case 'rpa':
        return <RPAManagement />
      case 'analytics':
        return <Analytics />
      case 'settings':
        return <SystemSettings />
      default:
        return <Dashboard systemStatus={systemStatus} />
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* 頂部導航欄 */}
      <header className="bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo 和標題 */}
            <div className="flex items-center space-x-4">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", stiffness: 260, damping: 20 }}
                className="flex items-center space-x-2"
              >
                <div className="w-10 h-10 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-lg flex items-center justify-center">
                  <Bot className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-slate-900">專利RPA系統</h1>
                  <p className="text-xs text-slate-500">智能專利檢索與分析平台</p>
                </div>
              </motion.div>
            </div>

            {/* 系統狀態指示器 */}
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className="flex items-center space-x-1">
                  <div className={`w-2 h-2 rounded-full ${
                    systemStatus.rpaStatus === 'active' ? 'bg-green-500' : 'bg-red-500'
                  }`} />
                  <span className="text-xs text-slate-600">RPA</span>
                </div>
                <div className="flex items-center space-x-1">
                  <div className={`w-2 h-2 rounded-full ${
                    systemStatus.databaseStatus === 'connected' ? 'bg-green-500' : 'bg-red-500'
                  }`} />
                  <span className="text-xs text-slate-600">資料庫</span>
                </div>
                <div className="flex items-center space-x-1">
                  <div className={`w-2 h-2 rounded-full ${
                    systemStatus.aiStatus === 'ready' ? 'bg-green-500' : 'bg-red-500'
                  }`} />
                  <span className="text-xs text-slate-600">AI</span>
                </div>
              </div>
              <Badge variant="outline" className="text-xs">
                <Clock className="w-3 h-3 mr-1" />
                {systemStatus.lastUpdate}
              </Badge>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* 側邊導航 */}
        <Navigation currentPage={currentPage} setCurrentPage={setCurrentPage} />

        {/* 主要內容區域 */}
        <main className="flex-1 p-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentPage}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              {renderCurrentPage()}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>

      {/* 浮動操作按鈕 */}
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 1, type: "spring", stiffness: 260, damping: 20 }}
        className="fixed bottom-6 right-6 z-40"
      >
        <Button
          size="lg"
          className="rounded-full shadow-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700"
          onClick={() => setCurrentPage('search')}
        >
          <Search className="w-5 h-5 mr-2" />
          快速檢索
        </Button>
      </motion.div>
    </div>
  )
}

export default App
