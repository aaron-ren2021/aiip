import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Bot, 
  Play, 
  Pause, 
  Square, 
  Settings, 
  Activity,
  Clock,
  CheckCircle,
  AlertCircle,
  RotateCcw,
  Eye,
  Download,
  Calendar,
  BarChart3
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'

const RPAManagement = () => {
  const [robots] = useState([
    {
      id: 'twpat-searcher',
      name: 'TWPAT檢索機器人',
      description: '專門檢索中華民國專利資料庫',
      status: 'running',
      currentTask: '關鍵字檢索: 人工智慧',
      progress: 75,
      startTime: '2024-01-15 14:30:00',
      estimatedCompletion: '2024-01-15 14:45:00',
      totalTasks: 156,
      successRate: 94.2,
      lastRun: '2024-01-15 14:30:00',
      capabilities: ['關鍵字檢索', '專利號檢索', 'PDF下載', '圖片擷取']
    },
    {
      id: 'uspto-searcher',
      name: 'USPTO檢索機器人',
      description: '專門檢索美國專利商標局資料庫',
      status: 'idle',
      currentTask: null,
      progress: 0,
      startTime: null,
      estimatedCompletion: null,
      totalTasks: 89,
      successRate: 96.8,
      lastRun: '2024-01-15 13:15:00',
      capabilities: ['關鍵字檢索', '專利號檢索', 'PDF下載', '圖式檢索']
    },
    {
      id: 'epo-searcher',
      name: 'EPO檢索機器人',
      description: '專門檢索歐洲專利局資料庫',
      status: 'error',
      currentTask: '連線失敗',
      progress: 0,
      startTime: '2024-01-15 14:00:00',
      estimatedCompletion: null,
      totalTasks: 45,
      successRate: 88.9,
      lastRun: '2024-01-15 12:30:00',
      capabilities: ['關鍵字檢索', '多語言檢索', 'PDF下載']
    },
    {
      id: 'multi-db-coordinator',
      name: '多資料庫協調機器人',
      description: '協調多個資料庫的並行檢索',
      status: 'scheduled',
      currentTask: '等待排程執行',
      progress: 0,
      startTime: null,
      estimatedCompletion: '2024-01-15 15:00:00',
      totalTasks: 23,
      successRate: 92.1,
      lastRun: '2024-01-15 11:45:00',
      capabilities: ['並行檢索', '結果合併', '去重處理']
    }
  ])

  const [taskHistory] = useState([
    {
      id: 1,
      robotId: 'twpat-searcher',
      robotName: 'TWPAT檢索機器人',
      taskType: '關鍵字檢索',
      keywords: ['機器學習', '深度學習'],
      status: 'completed',
      startTime: '2024-01-15 13:30:00',
      endTime: '2024-01-15 13:42:00',
      duration: '12分鐘',
      resultsFound: 23,
      filesDownloaded: 15,
      successRate: 100
    },
    {
      id: 2,
      robotId: 'uspto-searcher',
      robotName: 'USPTO檢索機器人',
      taskType: '專利號檢索',
      keywords: ['US10123456'],
      status: 'completed',
      startTime: '2024-01-15 13:15:00',
      endTime: '2024-01-15 13:18:00',
      duration: '3分鐘',
      resultsFound: 1,
      filesDownloaded: 3,
      successRate: 100
    },
    {
      id: 3,
      robotId: 'epo-searcher',
      robotName: 'EPO檢索機器人',
      taskType: '關鍵字檢索',
      keywords: ['artificial intelligence'],
      status: 'failed',
      startTime: '2024-01-15 12:30:00',
      endTime: '2024-01-15 12:35:00',
      duration: '5分鐘',
      resultsFound: 0,
      filesDownloaded: 0,
      successRate: 0,
      errorMessage: '資料庫連線超時'
    }
  ])

  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return 'text-blue-600 bg-blue-100'
      case 'idle': return 'text-green-600 bg-green-100'
      case 'error': return 'text-red-600 bg-red-100'
      case 'scheduled': return 'text-yellow-600 bg-yellow-100'
      case 'paused': return 'text-gray-600 bg-gray-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const getStatusText = (status) => {
    switch (status) {
      case 'running': return '執行中'
      case 'idle': return '待命中'
      case 'error': return '錯誤'
      case 'scheduled': return '已排程'
      case 'paused': return '已暫停'
      default: return '未知'
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'running': return <Activity className="w-4 h-4 animate-pulse" />
      case 'idle': return <CheckCircle className="w-4 h-4" />
      case 'error': return <AlertCircle className="w-4 h-4" />
      case 'scheduled': return <Clock className="w-4 h-4" />
      case 'paused': return <Pause className="w-4 h-4" />
      default: return <Bot className="w-4 h-4" />
    }
  }

  const runningRobots = robots.filter(robot => robot.status === 'running').length
  const totalRobots = robots.length
  const averageSuccessRate = robots.reduce((sum, robot) => sum + robot.successRate, 0) / robots.length

  return (
    <div className="space-y-6">
      {/* 頁面標題 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">RPA機器人管理</h1>
          <p className="text-slate-600 mt-1">自動化機器人流程監控與管理</p>
        </div>
        <div className="flex space-x-3">
          <Button variant="outline" size="sm">
            <RotateCcw className="w-4 h-4 mr-2" />
            重新整理
          </Button>
          <Button size="sm">
            <Settings className="w-4 h-4 mr-2" />
            機器人設定
          </Button>
        </div>
      </div>

      {/* 概覽統計 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">活躍機器人</CardTitle>
              <Bot className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{runningRobots}/{totalRobots}</div>
              <p className="text-xs text-muted-foreground">
                <span className="text-blue-600">{Math.round(runningRobots/totalRobots*100)}%</span> 執行中
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">總任務數</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">313</div>
              <p className="text-xs text-muted-foreground">
                <span className="text-green-600">+12</span> 今日新增
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">平均成功率</CardTitle>
              <CheckCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{averageSuccessRate.toFixed(1)}%</div>
              <p className="text-xs text-muted-foreground">
                <span className="text-green-600">+1.2%</span> 較上週
              </p>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">平均執行時間</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">8.5分</div>
              <p className="text-xs text-muted-foreground">
                <span className="text-green-600">-2.1分</span> 較昨日
              </p>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* 主要內容區域 */}
      <Tabs defaultValue="robots" className="space-y-6">
        <TabsList>
          <TabsTrigger value="robots">機器人狀態</TabsTrigger>
          <TabsTrigger value="tasks">任務歷史</TabsTrigger>
          <TabsTrigger value="schedule">排程管理</TabsTrigger>
        </TabsList>

        <TabsContent value="robots" className="space-y-6">
          {/* 機器人清單 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {robots.map((robot, index) => (
              <motion.div
                key={robot.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 * index }}
              >
                <Card className="h-full">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className={`p-2 rounded-full ${getStatusColor(robot.status)}`}>
                          {getStatusIcon(robot.status)}
                        </div>
                        <div>
                          <CardTitle className="text-lg">{robot.name}</CardTitle>
                          <CardDescription>{robot.description}</CardDescription>
                        </div>
                      </div>
                      <Badge className={getStatusColor(robot.status)}>
                        {getStatusText(robot.status)}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* 當前任務 */}
                    {robot.currentTask && (
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-600">當前任務:</span>
                          <span className="font-medium">{robot.currentTask}</span>
                        </div>
                        {robot.status === 'running' && (
                          <>
                            <div className="flex justify-between text-sm">
                              <span>進度</span>
                              <span>{robot.progress}%</span>
                            </div>
                            <Progress value={robot.progress} className="h-2" />
                          </>
                        )}
                      </div>
                    )}

                    {/* 統計資訊 */}
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-slate-500">總任務數:</span>
                        <p className="font-medium">{robot.totalTasks}</p>
                      </div>
                      <div>
                        <span className="text-slate-500">成功率:</span>
                        <p className="font-medium">{robot.successRate}%</p>
                      </div>
                      <div>
                        <span className="text-slate-500">最後執行:</span>
                        <p className="font-medium text-xs">{robot.lastRun}</p>
                      </div>
                      <div>
                        <span className="text-slate-500">預計完成:</span>
                        <p className="font-medium text-xs">
                          {robot.estimatedCompletion || 'N/A'}
                        </p>
                      </div>
                    </div>

                    {/* 功能列表 */}
                    <div className="space-y-2">
                      <span className="text-sm text-slate-500">支援功能:</span>
                      <div className="flex flex-wrap gap-1">
                        {robot.capabilities.map((capability, idx) => (
                          <Badge key={idx} variant="outline" className="text-xs">
                            {capability}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    {/* 操作按鈕 */}
                    <div className="flex space-x-2">
                      {robot.status === 'idle' && (
                        <Button size="sm" className="flex-1">
                          <Play className="w-4 h-4 mr-2" />
                          啟動
                        </Button>
                      )}
                      {robot.status === 'running' && (
                        <Button variant="outline" size="sm" className="flex-1">
                          <Pause className="w-4 h-4 mr-2" />
                          暫停
                        </Button>
                      )}
                      {robot.status === 'error' && (
                        <Button variant="outline" size="sm" className="flex-1">
                          <RotateCcw className="w-4 h-4 mr-2" />
                          重啟
                        </Button>
                      )}
                      <Button variant="outline" size="sm">
                        <Eye className="w-4 h-4 mr-2" />
                        詳情
                      </Button>
                      <Button variant="outline" size="sm">
                        <Settings className="w-4 h-4 mr-2" />
                        設定
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="tasks" className="space-y-6">
          {/* 任務歷史 */}
          <Card>
            <CardHeader>
              <CardTitle>任務執行歷史</CardTitle>
              <CardDescription>最近的機器人任務執行記錄</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {taskHistory.map((task, index) => (
                  <motion.div
                    key={task.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="border rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex justify-between items-start mb-3">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <h3 className="font-semibold text-slate-900">{task.robotName}</h3>
                          <Badge variant="outline">{task.taskType}</Badge>
                          <Badge 
                            className={
                              task.status === 'completed' 
                                ? 'bg-green-100 text-green-600' 
                                : 'bg-red-100 text-red-600'
                            }
                          >
                            {task.status === 'completed' ? '已完成' : '失敗'}
                          </Badge>
                        </div>
                        <p className="text-sm text-slate-600 mb-2">
                          <strong>檢索條件:</strong> {task.keywords.join(', ')} | 
                          <strong> 執行時間:</strong> {task.duration} | 
                          <strong> 成功率:</strong> {task.successRate}%
                        </p>
                        {task.errorMessage && (
                          <p className="text-sm text-red-600">
                            <strong>錯誤訊息:</strong> {task.errorMessage}
                          </p>
                        )}
                      </div>
                      <div className="flex flex-col space-y-2 ml-4">
                        <Button variant="outline" size="sm">
                          <Eye className="w-4 h-4 mr-2" />
                          查看詳情
                        </Button>
                        {task.status === 'completed' && (
                          <Button variant="outline" size="sm">
                            <Download className="w-4 h-4 mr-2" />
                            下載結果
                          </Button>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between text-xs text-slate-500">
                      <div className="flex space-x-4">
                        <span><strong>開始時間:</strong> {task.startTime}</span>
                        <span><strong>結束時間:</strong> {task.endTime}</span>
                      </div>
                      <div className="flex space-x-4">
                        <span><strong>找到結果:</strong> {task.resultsFound} 筆</span>
                        <span><strong>下載檔案:</strong> {task.filesDownloaded} 個</span>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="schedule" className="space-y-6">
          {/* 排程管理 */}
          <Card>
            <CardHeader>
              <CardTitle>排程管理</CardTitle>
              <CardDescription>設定和管理機器人的自動執行排程</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12">
                <Calendar className="w-16 h-16 text-slate-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-slate-900 mb-2">排程功能開發中</h3>
                <p className="text-slate-500">即將推出自動排程功能，敬請期待</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default RPAManagement
