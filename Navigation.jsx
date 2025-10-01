import { motion } from 'framer-motion'
import { 
  LayoutDashboard, 
  Search, 
  Database, 
  Bot, 
  BarChart3, 
  Settings,
  ChevronRight
} from 'lucide-react'
import { Button } from '@/components/ui/button.jsx'
import { Badge } from '@/components/ui/badge.jsx'

const Navigation = ({ currentPage, setCurrentPage }) => {
  const navigationItems = [
    {
      id: 'dashboard',
      label: '儀表板',
      icon: LayoutDashboard,
      description: '系統概覽與狀態監控',
      badge: null
    },
    {
      id: 'search',
      label: '專利檢索',
      icon: Search,
      description: '多資料庫智能檢索',
      badge: 'HOT'
    },
    {
      id: 'database',
      label: '資料庫管理',
      icon: Database,
      description: '專利資料庫配置',
      badge: null
    },
    {
      id: 'rpa',
      label: 'RPA管理',
      icon: Bot,
      description: '機器人流程管理',
      badge: 'NEW'
    },
    {
      id: 'analytics',
      label: '分析報告',
      icon: BarChart3,
      description: '智能分析與洞察',
      badge: null
    },
    {
      id: 'settings',
      label: '系統設定',
      icon: Settings,
      description: '系統配置與管理',
      badge: null
    }
  ]

  return (
    <nav className="w-64 bg-white/80 backdrop-blur-md border-r border-slate-200 h-[calc(100vh-4rem)] overflow-y-auto">
      <div className="p-4">
        <div className="space-y-2">
          {navigationItems.map((item, index) => {
            const Icon = item.icon
            const isActive = currentPage === item.id
            
            return (
              <motion.div
                key={item.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
              >
                <Button
                  variant={isActive ? "default" : "ghost"}
                  className={`w-full justify-start h-auto p-3 ${
                    isActive 
                      ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-md' 
                      : 'hover:bg-slate-100 text-slate-700'
                  }`}
                  onClick={() => setCurrentPage(item.id)}
                >
                  <div className="flex items-center justify-between w-full">
                    <div className="flex items-center space-x-3">
                      <Icon className={`w-5 h-5 ${isActive ? 'text-white' : 'text-slate-500'}`} />
                      <div className="text-left">
                        <div className={`font-medium ${isActive ? 'text-white' : 'text-slate-900'}`}>
                          {item.label}
                        </div>
                        <div className={`text-xs ${isActive ? 'text-blue-100' : 'text-slate-500'}`}>
                          {item.description}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {item.badge && (
                        <Badge 
                          variant={isActive ? "secondary" : "outline"} 
                          className={`text-xs ${
                            isActive 
                              ? 'bg-white/20 text-white border-white/30' 
                              : item.badge === 'HOT' 
                                ? 'bg-red-100 text-red-600 border-red-200'
                                : 'bg-green-100 text-green-600 border-green-200'
                          }`}
                        >
                          {item.badge}
                        </Badge>
                      )}
                      {isActive && (
                        <ChevronRight className="w-4 h-4 text-white" />
                      )}
                    </div>
                  </div>
                </Button>
              </motion.div>
            )
          })}
        </div>

        {/* 快速操作區域 */}
        <div className="mt-8 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
          <h3 className="text-sm font-medium text-slate-900 mb-3">快速操作</h3>
          <div className="space-y-2">
            <Button 
              variant="outline" 
              size="sm" 
              className="w-full justify-start text-xs"
              onClick={() => setCurrentPage('search')}
            >
              <Search className="w-4 h-4 mr-2" />
              新增檢索任務
            </Button>
            <Button 
              variant="outline" 
              size="sm" 
              className="w-full justify-start text-xs"
              onClick={() => setCurrentPage('rpa')}
            >
              <Bot className="w-4 h-4 mr-2" />
              啟動RPA機器人
            </Button>
            <Button 
              variant="outline" 
              size="sm" 
              className="w-full justify-start text-xs"
              onClick={() => setCurrentPage('analytics')}
            >
              <BarChart3 className="w-4 h-4 mr-2" />
              查看分析報告
            </Button>
          </div>
        </div>

        {/* 系統資訊 */}
        <div className="mt-6 p-3 bg-slate-50 rounded-lg">
          <div className="text-xs text-slate-600 space-y-1">
            <div className="flex justify-between">
              <span>版本</span>
              <span className="font-mono">v2.1.0</span>
            </div>
            <div className="flex justify-between">
              <span>環境</span>
              <span className="font-mono">Azure</span>
            </div>
            <div className="flex justify-between">
              <span>狀態</span>
              <span className="text-green-600 font-medium">運行中</span>
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navigation
