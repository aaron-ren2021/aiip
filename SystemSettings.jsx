import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Settings, 
  Save, 
  RotateCcw,
  Database,
  Bot,
  Shield,
  Bell,
  Globe,
  Palette
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'

const SystemSettings = () => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">系統設定</h1>
          <p className="text-slate-600 mt-1">系統配置與管理設定</p>
        </div>
        <div className="flex space-x-3">
          <Button variant="outline" size="sm">
            <RotateCcw className="w-4 h-4 mr-2" />
            重設為預設值
          </Button>
          <Button size="sm">
            <Save className="w-4 h-4 mr-2" />
            儲存設定
          </Button>
        </div>
      </div>

      <Tabs defaultValue="general" className="space-y-6">
        <TabsList>
          <TabsTrigger value="general">一般設定</TabsTrigger>
          <TabsTrigger value="database">資料庫設定</TabsTrigger>
          <TabsTrigger value="rpa">RPA設定</TabsTrigger>
          <TabsTrigger value="security">安全性設定</TabsTrigger>
        </TabsList>

        <TabsContent value="general">
          <div className="text-center py-12">
            <Settings className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">設定功能開發中</h3>
            <p className="text-slate-500">即將推出完整的系統設定功能</p>
          </div>
        </TabsContent>

        <TabsContent value="database">
          <div className="text-center py-12">
            <Database className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">資料庫設定開發中</h3>
            <p className="text-slate-500">即將推出資料庫連線設定功能</p>
          </div>
        </TabsContent>

        <TabsContent value="rpa">
          <div className="text-center py-12">
            <Bot className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">RPA設定開發中</h3>
            <p className="text-slate-500">即將推出機器人配置設定功能</p>
          </div>
        </TabsContent>

        <TabsContent value="security">
          <div className="text-center py-12">
            <Shield className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">安全性設定開發中</h3>
            <p className="text-slate-500">即將推出安全性配置功能</p>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default SystemSettings
