import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { 
  Activity, 
  Database, 
  Bot, 
  Search, 
  TrendingUp, 
  Clock, 
  CheckCircle, 
  AlertTriangle,
  FileText,
  Download,
  Users,
  Globe,
  Zap,
  BarChart3
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { Button } from '@/components/ui/button.jsx'
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell
} from 'recharts'

const Dashboard = ({ systemStatus }) => {
  const [stats, setStats] = useState({
    totalSearches: 1247,
    activeRobots: 8,
    connectedDatabases: 5,
    successRate: 94.2,
    todaySearches: 156,
    processingTime: 2.3,
    downloadedFiles: 3421,
    analysisReports: 89
  })

  const [recentActivity, setRecentActivity] = useState([
    {
      id: 1,
      type: 'search',
      description: 'USPTO專利檢索完成',
      time: '2分鐘前',
      status: 'success',
      details: '找到 23 筆相關專利'
    },
    {
      id: 2,
      type: 'rpa',
      description: 'TWPAT機器人啟動',
      time: '5分鐘前',
      status: 'running',
      details: '正在執行關鍵字檢索'
    },
    {
      id: 3,
      type: 'analysis',
      description: 'AI分析報告生成',
      time: '8分鐘前',
      status: 'success',
      details: '專利風險評估完成'
    },
    {
      id: 4,
      type: 'download',
      description: '文件下載完成',
      time: '12分鐘前',
      status: 'success',
      details: '下載 15 個PDF文件'
    }
  ])

  // 模擬數據更新
  useEffect(() => {
    const interval = setInterval(() => {
      setStats(prev => ({
        ...prev,
        todaySearches: prev.todaySearches + Math.floor(Math.random() * 3),
        processingTime: (Math.random() * 2 + 1.5).toFixed(1)
      }))
    }, 10000)

    return () => clearInterval(interval)
  }, [])

  // 圖表數據
  const searchTrendData = [
    { name: '週一', searches: 120, success: 115 },
    { name: '週二', searches: 145, success: 138 },
    { name: '週三', searches: 167, success: 159 },
    { name: '週四', searches: 134, success: 128 },
    { name: '週五', searches: 189, success: 182 },
    { name: '週六', searches: 98, success: 94 },
    { name: '週日', searches: 87, success: 83 }
  ]

  const databaseUsageData = [
    { name: 'USPTO', value: 35, color: '#3B82F6' },
    { name: 'TWPAT', value: 28, color: '#10B981' },
    { name: 'EPO', value: 20, color: '#F59E0B' },
    { name: 'WIPO', value: 12, color: '#EF4444' },
    { name: '其他', value: 5, color: '#8B5CF6' }
  ]

  const performanceData = [
    { name: '檢索速度', value: 92 },
    { name: '準確率', value: 94 },
    { name: '可用性', value: 99 },
    { name: '用戶滿意度', value: 87 }
  ]

  const getActivityIcon = (type) => {
    switch (type) {
      case 'search': return <Search className="w-4 h-4" />
      case 'rpa': return <Bot className="w-4 h-4" />
      case 'analysis': return <BarChart3 className="w-4 h-4" />
      case 'download': return <Download className="w-4 h-4" />
      default: return <Activity className="w-4 h-4" />
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'success': return 'text-green-600 bg-green-100'
      case 'running': return 'text-blue-600 bg-blue-100'
      case 'warning': return 'text-yellow-600 bg-yellow-100'
      case 'error': return 'text-red-600 bg-red-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  return (
    <div className="space-y-6">
      {/* 頁面標題 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">系統儀表板</h1>
          <p className="text-slate-600 mt-1">專利RPA系統運行狀態與統計資訊</p>
        </div>
        <div className="flex space-x-3">
          <Button variant="outline" size="sm">
            <Download className="w-4 h-4 mr-2" />
            匯出報告
          </Button>
          <Button size="sm">
            <Activity className="w-4 h-4 mr-2" />
            即時監控
          </Button>
        </div>
      </div>

      {/* 統計卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="relative overflow-hidden">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">總檢索次數</CardTitle>
              <Search className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.totalSearches.toLocaleString()}</div>
              <p className="text-xs text-muted-foreground">
                <span className="text-green-600">+{stats.todaySearches}</span> 今日新增
              </p>
            </CardContent>
            <div className="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-blue-500 to-indigo-500" />
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="relative overflow-hidden">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">活躍機器人</CardTitle>
              <Bot className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.activeRobots}</div>
              <p className="text-xs text-muted-foreground">
                <span className="text-green-600">100%</span> 運行正常
              </p>
            </CardContent>
            <div className="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-green-500 to-emerald-500" />
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="relative overflow-hidden">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">連接資料庫</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.connectedDatabases}</div>
              <p className="text-xs text-muted-foreground">
                <span className="text-green-600">全部</span> 連線正常
              </p>
            </CardContent>
            <div className="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-purple-500 to-pink-500" />
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card className="relative overflow-hidden">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">成功率</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.successRate}%</div>
              <p className="text-xs text-muted-foreground">
                <span className="text-green-600">+2.1%</span> 較上週
              </p>
            </CardContent>
            <div className="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-orange-500 to-red-500" />
          </Card>
        </motion.div>
      </div>

      {/* 圖表區域 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 檢索趨勢圖 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <Card>
            <CardHeader>
              <CardTitle>檢索趨勢</CardTitle>
              <CardDescription>過去一週的檢索活動統計</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={searchTrendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Line 
                    type="monotone" 
                    dataKey="searches" 
                    stroke="#3B82F6" 
                    strokeWidth={2}
                    name="總檢索"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="success" 
                    stroke="#10B981" 
                    strokeWidth={2}
                    name="成功檢索"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </motion.div>

        {/* 資料庫使用分布 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
        >
          <Card>
            <CardHeader>
              <CardTitle>資料庫使用分布</CardTitle>
              <CardDescription>各專利資料庫的使用比例</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={databaseUsageData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {databaseUsageData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* 系統效能和最近活動 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 系統效能 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
        >
          <Card>
            <CardHeader>
              <CardTitle>系統效能</CardTitle>
              <CardDescription>關鍵指標監控</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {performanceData.map((item, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>{item.name}</span>
                    <span className="font-medium">{item.value}%</span>
                  </div>
                  <Progress value={item.value} className="h-2" />
                </div>
              ))}
            </CardContent>
          </Card>
        </motion.div>

        {/* 最近活動 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="lg:col-span-2"
        >
          <Card>
            <CardHeader>
              <CardTitle>最近活動</CardTitle>
              <CardDescription>系統最新操作記錄</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentActivity.map((activity) => (
                  <div key={activity.id} className="flex items-start space-x-3 p-3 rounded-lg hover:bg-slate-50 transition-colors">
                    <div className={`p-2 rounded-full ${getStatusColor(activity.status)}`}>
                      {getActivityIcon(activity.type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium text-slate-900 truncate">
                          {activity.description}
                        </p>
                        <Badge variant="outline" className="text-xs">
                          {activity.time}
                        </Badge>
                      </div>
                      <p className="text-xs text-slate-500 mt-1">
                        {activity.details}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-4 pt-4 border-t">
                <Button variant="outline" className="w-full" size="sm">
                  <Clock className="w-4 h-4 mr-2" />
                  查看完整活動記錄
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* 快速操作區域 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.9 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>快速操作</CardTitle>
            <CardDescription>常用功能快速入口</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Button variant="outline" className="h-20 flex-col space-y-2">
                <Search className="w-6 h-6" />
                <span className="text-sm">新增檢索</span>
              </Button>
              <Button variant="outline" className="h-20 flex-col space-y-2">
                <Bot className="w-6 h-6" />
                <span className="text-sm">啟動機器人</span>
              </Button>
              <Button variant="outline" className="h-20 flex-col space-y-2">
                <BarChart3 className="w-6 h-6" />
                <span className="text-sm">分析報告</span>
              </Button>
              <Button variant="outline" className="h-20 flex-col space-y-2">
                <FileText className="w-6 h-6" />
                <span className="text-sm">文件管理</span>
              </Button>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}

export default Dashboard
