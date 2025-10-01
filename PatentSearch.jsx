import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Search, 
  Database, 
  Bot, 
  Filter, 
  Download, 
  FileText, 
  Calendar,
  Globe,
  Zap,
  CheckCircle,
  Clock,
  AlertCircle,
  Play,
  Pause,
  RotateCcw,
  Eye,
  ExternalLink,
  Copy
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Button } from '@/components/ui/button.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Textarea } from '@/components/ui/textarea.jsx'
import { Checkbox } from '@/components/ui/checkbox.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select.jsx'

const PatentSearch = () => {
  const [searchParams, setSearchParams] = useState({
    keywords: '',
    patentNumber: '',
    applicant: '',
    inventor: '',
    ipcClass: '',
    dateRange: {
      start: '',
      end: ''
    },
    databases: {
      twpat: true,
      uspto: true,
      epo: false,
      wipo: false,
      jpat: false
    },
    options: {
      includeFullText: true,
      includeImages: true,
      includeClaims: true,
      maxResults: 100
    }
  })

  const [searchStatus, setSearchStatus] = useState('idle') // idle, searching, completed, error
  const [searchProgress, setSearchProgress] = useState(0)
  const [searchResults, setSearchResults] = useState([])
  const [currentTask, setCurrentTask] = useState(null)

  // 模擬檢索進度
  useEffect(() => {
    if (searchStatus === 'searching') {
      const interval = setInterval(() => {
        setSearchProgress(prev => {
          if (prev >= 100) {
            setSearchStatus('completed')
            return 100
          }
          return prev + Math.random() * 10
        })
      }, 500)

      return () => clearInterval(interval)
    }
  }, [searchStatus])

  const handleSearch = () => {
    setSearchStatus('searching')
    setSearchProgress(0)
    setCurrentTask({
      id: Date.now(),
      startTime: new Date(),
      databases: Object.keys(searchParams.databases).filter(db => searchParams.databases[db])
    })

    // 模擬檢索結果
    setTimeout(() => {
      setSearchResults([
        {
          id: 1,
          patentNumber: 'US10123456',
          title: '人工智慧驅動的專利檢索系統及方法',
          applicant: 'Tech Innovation Corp.',
          inventors: ['張三', '李四'],
          applicationDate: '2023-01-15',
          publicationDate: '2023-07-20',
          ipcClasses: ['G06F16/00', 'G06N20/00'],
          abstract: '本發明提供一種基於人工智慧的專利檢索系統，能夠自動分析專利文件並提供智能比對功能...',
          database: 'USPTO',
          relevanceScore: 95,
          downloadUrl: '#',
          detailUrl: '#'
        },
        {
          id: 2,
          patentNumber: 'TW202301234',
          title: '機器學習專利分析裝置',
          applicant: '台灣科技股份有限公司',
          inventors: ['王五', '趙六'],
          applicationDate: '2023-02-10',
          publicationDate: '2023-08-15',
          ipcClasses: ['G06N3/00'],
          abstract: '一種利用機器學習技術進行專利分析的裝置，包含資料預處理模組、特徵提取模組...',
          database: 'TWPAT',
          relevanceScore: 88,
          downloadUrl: '#',
          detailUrl: '#'
        },
        {
          id: 3,
          patentNumber: 'US10987654',
          title: 'Automated Patent Analysis System Using Natural Language Processing',
          applicant: 'AI Research Labs Inc.',
          inventors: ['John Smith', 'Jane Doe'],
          applicationDate: '2023-03-05',
          publicationDate: '2023-09-10',
          ipcClasses: ['G06F40/00', 'G06N3/08'],
          abstract: 'An automated system for analyzing patent documents using advanced natural language processing techniques...',
          database: 'USPTO',
          relevanceScore: 82,
          downloadUrl: '#',
          detailUrl: '#'
        }
      ])
    }, 3000)
  }

  const handleInputChange = (field, value) => {
    setSearchParams(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleDatabaseChange = (database, checked) => {
    setSearchParams(prev => ({
      ...prev,
      databases: {
        ...prev.databases,
        [database]: checked
      }
    }))
  }

  const handleOptionChange = (option, value) => {
    setSearchParams(prev => ({
      ...prev,
      options: {
        ...prev.options,
        [option]: value
      }
    }))
  }

  const getStatusIcon = () => {
    switch (searchStatus) {
      case 'searching':
        return <Clock className="w-5 h-5 text-blue-600 animate-spin" />
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-600" />
      default:
        return <Search className="w-5 h-5 text-slate-600" />
    }
  }

  const getStatusText = () => {
    switch (searchStatus) {
      case 'searching':
        return '檢索進行中...'
      case 'completed':
        return `檢索完成 - 找到 ${searchResults.length} 筆結果`
      case 'error':
        return '檢索失敗'
      default:
        return '準備開始檢索'
    }
  }

  const selectedDatabases = Object.keys(searchParams.databases).filter(db => searchParams.databases[db])

  return (
    <div className="space-y-6">
      {/* 頁面標題 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">專利檢索</h1>
          <p className="text-slate-600 mt-1">多資料庫智能專利檢索與分析</p>
        </div>
        <div className="flex items-center space-x-2">
          {getStatusIcon()}
          <span className="text-sm font-medium">{getStatusText()}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 檢索參數設定 */}
        <div className="lg:col-span-1 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Filter className="w-5 h-5" />
                <span>檢索條件</span>
              </CardTitle>
              <CardDescription>設定專利檢索的條件和參數</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Tabs defaultValue="basic" className="w-full">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="basic">基本檢索</TabsTrigger>
                  <TabsTrigger value="advanced">進階檢索</TabsTrigger>
                </TabsList>
                
                <TabsContent value="basic" className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="keywords">關鍵字</Label>
                    <Textarea
                      id="keywords"
                      placeholder="輸入檢索關鍵字，多個關鍵字請用空格分隔"
                      value={searchParams.keywords}
                      onChange={(e) => handleInputChange('keywords', e.target.value)}
                      rows={3}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="patentNumber">專利號碼</Label>
                    <Input
                      id="patentNumber"
                      placeholder="例如: US10123456, TW202301234"
                      value={searchParams.patentNumber}
                      onChange={(e) => handleInputChange('patentNumber', e.target.value)}
                    />
                  </div>
                </TabsContent>

                <TabsContent value="advanced" className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="applicant">申請人</Label>
                    <Input
                      id="applicant"
                      placeholder="公司或個人名稱"
                      value={searchParams.applicant}
                      onChange={(e) => handleInputChange('applicant', e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="inventor">發明人</Label>
                    <Input
                      id="inventor"
                      placeholder="發明人姓名"
                      value={searchParams.inventor}
                      onChange={(e) => handleInputChange('inventor', e.target.value)}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="ipcClass">IPC分類</Label>
                    <Input
                      id="ipcClass"
                      placeholder="例如: G06F, H04L"
                      value={searchParams.ipcClass}
                      onChange={(e) => handleInputChange('ipcClass', e.target.value)}
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div className="space-y-2">
                      <Label htmlFor="dateStart">申請日期起</Label>
                      <Input
                        id="dateStart"
                        type="date"
                        value={searchParams.dateRange.start}
                        onChange={(e) => handleInputChange('dateRange', {
                          ...searchParams.dateRange,
                          start: e.target.value
                        })}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="dateEnd">申請日期迄</Label>
                      <Input
                        id="dateEnd"
                        type="date"
                        value={searchParams.dateRange.end}
                        onChange={(e) => handleInputChange('dateRange', {
                          ...searchParams.dateRange,
                          end: e.target.value
                        })}
                      />
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          {/* 資料庫選擇 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Database className="w-5 h-5" />
                <span>資料庫選擇</span>
              </CardTitle>
              <CardDescription>選擇要檢索的專利資料庫</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {[
                { id: 'twpat', name: 'TWPAT', description: '中華民國專利資料庫', flag: '🇹🇼' },
                { id: 'uspto', name: 'USPTO', description: '美國專利商標局', flag: '🇺🇸' },
                { id: 'epo', name: 'EPO', description: '歐洲專利局', flag: '🇪🇺' },
                { id: 'wipo', name: 'WIPO', description: '世界智慧財產權組織', flag: '🌍' },
                { id: 'jpat', name: 'JPAT', description: '日本特許廳', flag: '🇯🇵' }
              ].map((db) => (
                <div key={db.id} className="flex items-center space-x-3 p-2 rounded-lg hover:bg-slate-50">
                  <Checkbox
                    id={db.id}
                    checked={searchParams.databases[db.id]}
                    onCheckedChange={(checked) => handleDatabaseChange(db.id, checked)}
                  />
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <span className="text-lg">{db.flag}</span>
                      <Label htmlFor={db.id} className="font-medium">{db.name}</Label>
                    </div>
                    <p className="text-xs text-slate-500">{db.description}</p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* 檢索選項 */}
          <Card>
            <CardHeader>
              <CardTitle>檢索選項</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="includeFullText"
                  checked={searchParams.options.includeFullText}
                  onCheckedChange={(checked) => handleOptionChange('includeFullText', checked)}
                />
                <Label htmlFor="includeFullText">包含全文內容</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="includeImages"
                  checked={searchParams.options.includeImages}
                  onCheckedChange={(checked) => handleOptionChange('includeImages', checked)}
                />
                <Label htmlFor="includeImages">包含圖片</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="includeClaims"
                  checked={searchParams.options.includeClaims}
                  onCheckedChange={(checked) => handleOptionChange('includeClaims', checked)}
                />
                <Label htmlFor="includeClaims">包含申請專利範圍</Label>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="maxResults">最大結果數</Label>
                <Select
                  value={searchParams.options.maxResults.toString()}
                  onValueChange={(value) => handleOptionChange('maxResults', parseInt(value))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="50">50</SelectItem>
                    <SelectItem value="100">100</SelectItem>
                    <SelectItem value="200">200</SelectItem>
                    <SelectItem value="500">500</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>

          {/* 開始檢索按鈕 */}
          <Button
            onClick={handleSearch}
            disabled={searchStatus === 'searching' || (!searchParams.keywords && !searchParams.patentNumber)}
            className="w-full h-12 text-lg"
            size="lg"
          >
            {searchStatus === 'searching' ? (
              <>
                <Clock className="w-5 h-5 mr-2 animate-spin" />
                檢索中...
              </>
            ) : (
              <>
                <Search className="w-5 h-5 mr-2" />
                開始檢索
              </>
            )}
          </Button>
        </div>

        {/* 檢索結果區域 */}
        <div className="lg:col-span-2 space-y-6">
          {/* 檢索狀態 */}
          {searchStatus !== 'idle' && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Bot className="w-5 h-5" />
                    <span>檢索狀態</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {searchStatus === 'searching' && (
                    <div className="space-y-4">
                      <div className="flex justify-between text-sm">
                        <span>檢索進度</span>
                        <span>{Math.round(searchProgress)}%</span>
                      </div>
                      <Progress value={searchProgress} className="h-2" />
                      
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-slate-600">檢索資料庫:</span>
                          <div className="mt-1 space-x-1">
                            {selectedDatabases.map(db => (
                              <Badge key={db} variant="outline">{db.toUpperCase()}</Badge>
                            ))}
                          </div>
                        </div>
                        <div>
                          <span className="text-slate-600">預估時間:</span>
                          <p className="mt-1 font-medium">約 2-3 分鐘</p>
                        </div>
                      </div>
                    </div>
                  )}

                  {searchStatus === 'completed' && (
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <CheckCircle className="w-5 h-5 text-green-600" />
                        <span className="font-medium">檢索完成</span>
                      </div>
                      <div className="flex space-x-2">
                        <Button variant="outline" size="sm">
                          <Download className="w-4 h-4 mr-2" />
                          匯出結果
                        </Button>
                        <Button variant="outline" size="sm">
                          <RotateCcw className="w-4 h-4 mr-2" />
                          重新檢索
                        </Button>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* 檢索結果 */}
          {searchResults.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <FileText className="w-5 h-5" />
                      <span>檢索結果</span>
                      <Badge variant="secondary">{searchResults.length} 筆</Badge>
                    </div>
                    <div className="flex space-x-2">
                      <Button variant="outline" size="sm">
                        <Filter className="w-4 h-4 mr-2" />
                        篩選
                      </Button>
                      <Button variant="outline" size="sm">
                        <Download className="w-4 h-4 mr-2" />
                        全部下載
                      </Button>
                    </div>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {searchResults.map((result, index) => (
                      <motion.div
                        key={result.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                        className="border rounded-lg p-4 hover:shadow-md transition-shadow"
                      >
                        <div className="flex justify-between items-start mb-3">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-2">
                              <h3 className="font-semibold text-lg text-slate-900">{result.title}</h3>
                              <Badge variant="outline">{result.database}</Badge>
                              <Badge 
                                variant={result.relevanceScore > 90 ? "default" : "secondary"}
                                className="text-xs"
                              >
                                相關度 {result.relevanceScore}%
                              </Badge>
                            </div>
                            <p className="text-sm text-slate-600 mb-2">
                              <strong>專利號:</strong> {result.patentNumber} | 
                              <strong> 申請人:</strong> {result.applicant} | 
                              <strong> 申請日:</strong> {result.applicationDate}
                            </p>
                            <p className="text-sm text-slate-700 line-clamp-2">
                              {result.abstract}
                            </p>
                          </div>
                          <div className="flex flex-col space-y-2 ml-4">
                            <Button variant="outline" size="sm">
                              <Eye className="w-4 h-4 mr-2" />
                              查看
                            </Button>
                            <Button variant="outline" size="sm">
                              <Download className="w-4 h-4 mr-2" />
                              下載
                            </Button>
                          </div>
                        </div>
                        
                        <div className="flex items-center justify-between text-xs text-slate-500">
                          <div className="flex space-x-4">
                            <span><strong>發明人:</strong> {result.inventors.join(', ')}</span>
                            <span><strong>IPC:</strong> {result.ipcClasses.join(', ')}</span>
                          </div>
                          <div className="flex space-x-2">
                            <Button variant="ghost" size="sm" className="h-6 px-2">
                              <ExternalLink className="w-3 h-3 mr-1" />
                              原文
                            </Button>
                            <Button variant="ghost" size="sm" className="h-6 px-2">
                              <Copy className="w-3 h-3 mr-1" />
                              複製
                            </Button>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* 空狀態 */}
          {searchStatus === 'idle' && (
            <Card className="h-96 flex items-center justify-center">
              <div className="text-center space-y-4">
                <Search className="w-16 h-16 text-slate-300 mx-auto" />
                <div>
                  <h3 className="text-lg font-medium text-slate-900">開始您的專利檢索</h3>
                  <p className="text-slate-500 mt-1">設定檢索條件並選擇資料庫，即可開始智能專利檢索</p>
                </div>
                <div className="flex justify-center space-x-4 text-sm text-slate-400">
                  <div className="flex items-center space-x-1">
                    <Globe className="w-4 h-4" />
                    <span>多國專利</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Zap className="w-4 h-4" />
                    <span>AI智能</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Bot className="w-4 h-4" />
                    <span>自動化</span>
                  </div>
                </div>
              </div>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

export default PatentSearch
