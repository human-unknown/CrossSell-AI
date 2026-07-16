// ============ 产品 & 市场 ============

export type TargetMarket =
  | '美国'
  | '英国'
  | '德国'
  | '日本'
  | '东南亚'
  | '法国'
  | '巴西'
  | '印度'

export type TargetPlatform =
  | 'TikTok'
  | 'Instagram'
  | 'YouTube Shorts'
  | 'Facebook'
  | 'Pinterest'

export type ContentType = '短视频' | '社媒文案'

export interface ProductInfo {
  productName: string
  productDescription: string
  targetMarkets: TargetMarket[]
  targetPlatforms: TargetPlatform[]
  contentTypes: ContentType[]
}

// ============ 生成任务 ============

export type StepStatus = 'waiting' | 'active' | 'completed' | 'error'

export interface GenerationProgress {
  taskId: string
  status: 'pending' | 'generating' | 'completed' | 'failed'
  steps: {
    script: StepStatus
    voiceover: StepStatus
    videoRender: StepStatus
    copyOptimize: StepStatus
  }
  message: string
}

// ============ 生成结果 ============

export interface VideoResult {
  id: string
  platform: TargetPlatform
  url: string
  thumbnail: string
  title: string
  duration: number
}

export interface CopyResult {
  id: string
  platform: TargetPlatform
  content: string
  hashtags: string[]
  characterCount: number
}

export interface StrategyResult {
  recommendedPlatforms: {
    platform: string
    dailyBudget: string
    expectedROAS: string
    reasoning: string
  }[]
  budgetAllocation: {
    platform: string
    percentage: number
  }[]
}

export interface GenerationResult {
  taskId: string
  videos: VideoResult[]
  copies: CopyResult[]
  strategy: StrategyResult
}

// ============ 任务历史 ============

export interface TaskRecord {
  taskId: string
  productName: string
  createdAt: string
  status: 'generating' | 'completed' | 'failed'
  platforms: TargetPlatform[]
  contentTypes: ContentType[]
}

// ============ 统计 ============

export interface WeeklyStats {
  videoCount: number
  copyCount: number
  strategyCount: number
  totalTasks: number
  completedTasks: number
}
