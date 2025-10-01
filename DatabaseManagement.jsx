import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Database, 
  CheckCircle, 
  AlertCircle, 
  Settings, 
  RefreshCw,
  Globe,
  Activity,
  Clock,
  Users,
  BarChart3
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Progress } from '@/components/ui/progress.jsx'

const DatabaseManagement = () => {
  const [databases] = useState([
    {
      id: 'twpat',
      name: 'TWPAT',
      fullName: '中華民國專利資料庫',
      flag: '🇹🇼',
      status: 'connected',
      lastSync: '2024-01-15 14:30',
      totalRecords: '2,456,789',
      responseTime: '120ms',
      uptime: '99.8%',
      description: '提供台灣地區的專利、新型、設計專利資料'
    },
    {
      id: 'uspto',
      name: 'USPTO',
      fullName: '美國專利商標局',
      flag: '🇺🇸',
      status: 'connected',
      lastSync: '2024-01-15 14:25',
      totalRecords: '12,345,678',
      responseTime: '95ms',
      uptime: '99.9%',
      description: '美國專利和商標的官方資料庫'
    },
    {
      id: 'epo',
      name: 'EPO',
      fullName: '歐洲專利局',
      flag: '🇪🇺',
      status: 'maintenance',
      lastSync: '2024-01-15 12:00',
      totalRecords: '8,765,432',
      responseTime: '180ms',
      uptime: '98.5%',
      description: '歐洲專利局的專利資料庫'
    },
    {
      id: 'wipo',
      name: 'WIPO',
      fullName: '世界智慧財產權組織',
      flag: '🌍',
      status: 'error',
      lastSync: '2024-01-15 10:15',
      totalRecords: '5,432,109',
      responseTime: 'N/A',
      uptime: '95.2%',
      description: 'PCT國際專利申請資料庫'
    },
    {
      id: 'jpat',
      name: 'JPAT',
      fullName: '日本特許廳',
      flag: '🇯🇵',
      status: 'disconnected',
      lastSync: '2024-01-14 18:45',
      totalRecords: '6,789,012',
      responseTime: 'N/A',
      uptime: '97.8%',
      description: '日本特許廳專利資料庫'
    }
  ])

  const getStatusColor = (status) => {
    switch (status) {
      case 'connected': return 'text-green-600 bg-green-100'
      case 'maintenance': return 'text-yellow-600 bg-yellow-100'
      case 'error': return 'text-red-600 bg-red-100'
      case 'disconnected': return 'text-gray-600 bg-gray-100'
      default: return 'text-gray-600 bg-gray-100'
    }
  }

  const getStatusText = (status) => {
    switch (status) {
      case 'connected': return '已連線'
      case 'maintenance': return '維護中'
      case 'error': return '連線錯誤'
      case 'disconnected': return '未連線'
      default: return '未知'
    }
  }

  const connectedCount = databases.filter(db => db.status === 'connected').length
  const totalCount = databases.length

  return (
    <div className="space-y-6">
      {/* 頁面標題 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">資料庫管理</h1>
          <p className="text-slate-600 mt-1">專利資料庫連線狀態與管理</p>
        </div>
        <div className="flex space-x-3">
          <Button variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            重新整理
          </Button>
          <Button size="sm">
            <Settings className="w-4 h-4 mr-2" />
            資料庫設定
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
              <CardTitle className="text-sm font-medium">連線狀態</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{connectedCount}/{totalCount}</div>
              <p className="text-xs text-muted-foreground">
                <span className="text-green-600">{Math.round(connectedCount/totalCount*100)}%</span> 正常運行
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
              <CardTitle className="text-sm font-medium">總專利數</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">35.8M</div>
              <p className="text-xs text-muted-foreground">
                <span className="text-green-600">+2.1%</span> 較上月
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
              <CardTitle className="text-sm font-medium">平均回應時間</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">132ms</div>
              <p className="text-xs text-muted-foreground">
                <span className="text-green-600">-15ms</span> 較昨日
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
              <CardTitle className="text-sm font-medium">系統可用性</CardTitle>
              <CheckCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">98.8%</div>
              <p className="text-xs text-muted-foreground">
                過去30天平均
              </p>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* 資料庫清單 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {databases.map((db, index) => (
          <motion.div
            key={db.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 * index }}
          >
            <Card className="h-full">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">{db.flag}</span>
                    <div>
                      <CardTitle className="text-lg">{db.name}</CardTitle>
                      <CardDescription>{db.fullName}</CardDescription>
                    </div>
                  </div>
                  <Badge className={getStatusColor(db.status)}>
                    {getStatusText(db.status)}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-slate-600">{db.description}</p>
                
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-slate-500">總記錄數:</span>
                    <p className="font-medium">{db.totalRecords}</p>
                  </div>
                  <div>
                    <span className="text-slate-500">回應時間:</span>
                    <p className="font-medium">{db.responseTime}</p>
                  </div>
                  <div>
                    <span className="text-slate-500">可用性:</span>
                    <p className="font-medium">{db.uptime}</p>
                  </div>
                  <div>
                    <span className="text-slate-500">最後同步:</span>
                    <p className="font-medium text-xs">{db.lastSync}</p>
                  </div>
                </div>

                {/* 可用性進度條 */}
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span>可用性</span>
                    <span>{db.uptime}</span>
                  </div>
                  <Progress value={parseFloat(db.uptime)} className="h-2" />
                </div>

                <div className="flex space-x-2">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="flex-1"
                    disabled={db.status === 'maintenance'}
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    測試連線
                  </Button>
                  <Button variant="outline" size="sm" className="flex-1">
                    <Settings className="w-4 h-4 mr-2" />
                    設定
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* 系統健康度監控 */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
      >
        <Card>
          <CardHeader>
            <CardTitle>系統健康度監控</CardTitle>
            <CardDescription>即時監控各資料庫的運行狀態</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="space-y-3">
                <h4 className="font-medium flex items-center space-x-2">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                  <span>正常運行</span>
                </h4>
                <div className="space-y-2">
                  {databases.filter(db => db.status === 'connected').map(db => (
                    <div key={db.id} className="flex items-center space-x-2 text-sm">
                      <span>{db.flag}</span>
                      <span>{db.name}</span>
                      <Badge variant="outline" className="text-xs">
                        {db.responseTime}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                <h4 className="font-medium flex items-center space-x-2">
                  <Clock className="w-4 h-4 text-yellow-600" />
                  <span>維護中</span>
                </h4>
                <div className="space-y-2">
                  {databases.filter(db => db.status === 'maintenance').map(db => (
                    <div key={db.id} className="flex items-center space-x-2 text-sm">
                      <span>{db.flag}</span>
                      <span>{db.name}</span>
                      <Badge variant="outline" className="text-xs text-yellow-600">
                        維護中
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                <h4 className="font-medium flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 text-red-600" />
                  <span>需要注意</span>
                </h4>
                <div className="space-y-2">
                  {databases.filter(db => db.status === 'error' || db.status === 'disconnected').map(db => (
                    <div key={db.id} className="flex items-center space-x-2 text-sm">
                      <span>{db.flag}</span>
                      <span>{db.name}</span>
                      <Badge variant="outline" className="text-xs text-red-600">
                        {getStatusText(db.status)}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}

export default DatabaseManagement
