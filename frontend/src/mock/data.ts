import type {
  GenerationResult,
  TaskRecord,
  WeeklyStats,
  GenerationProgress,
  StrategyData,
  AnalyticsData,
} from '../types'

// ============ Mock 生成结果 ============

export const mockGenerationResult: GenerationResult = {
  taskId: 'task_demo_001',
  videos: [
    {
      id: 'vid_1',
      platform: 'TikTok',
      url: 'https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4',
      thumbnail: '',
      title: '这款便携式蓝牙音箱，让你的户外派对嗨翻天！',
      duration: 30,
    },
    {
      id: 'vid_2',
      platform: 'Instagram',
      url: 'https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4',
      thumbnail: '',
      title: 'The ultimate portable speaker for your next adventure 🎵',
      duration: 15,
    },
    {
      id: 'vid_3',
      platform: 'YouTube Shorts',
      url: 'https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4',
      thumbnail: '',
      title: '拆箱实测：200元蓝牙音箱到底香不香？',
      duration: 45,
    },
  ],
  copies: [
    {
      id: 'copy_1',
      platform: 'TikTok',
      content:
        '🔥 户外党必备！这款音箱防水防尘，续航12小时，带上它去露营简直不要太爽！\n\n低音震撼、颜值在线，200块不到的价格真的香到爆炸 💥\n\n#户外装备 #蓝牙音箱 #露营必备 #好物推荐 #性价比之王',
      hashtags: ['户外装备', '蓝牙音箱', '露营必备', '好物推荐', '性价比之王'],
      characterCount: 128,
    },
    {
      id: 'copy_2',
      platform: 'Instagram',
      content:
        '🎵 Sound that moves with you.\n\nMeet the portable speaker that delivers booming bass in a compact design. Perfect for beach days, hikes, and everything in between. ✨\n\n12h battery | IPX7 waterproof | Under $30\n\n#PortableSpeaker #TechLifestyle #AdventureReady #MusicOnTheGo',
      hashtags: ['PortableSpeaker', 'TechLifestyle', 'AdventureReady', 'MusicOnTheGo'],
      characterCount: 285,
    },
    {
      id: 'copy_3',
      platform: 'Facebook',
      content:
        'Looking for the perfect gift? 🎁\n\nOur new portable Bluetooth speaker combines stunning sound quality with rugged durability — and it costs less than dinner for two!\n\n✅ 12-hour battery life\n✅ IPX7 waterproof rating\n✅ Bluetooth 5.3 for seamless connection\n\nShop now and get 15% off your first order. Link in bio! 👆\n\n#GiftIdeas #TechDeals #PortableAudio',
      hashtags: ['GiftIdeas', 'TechDeals', 'PortableAudio'],
      characterCount: 342,
    },
    {
      id: 'copy_4',
      platform: 'Pinterest',
      content:
        '🎨 The Aesthetic Speaker You Need in Your Life\n\nMinimal design. Powerful sound. This Bluetooth speaker doubles as room décor!\n\nTap to shop the look →',
      hashtags: ['HomeDecor', 'TechAesthetic', 'CozyVibes'],
      characterCount: 158,
    },
  ],
  strategy: {
    recommendedPlatforms: [
      {
        platform: 'TikTok Ads',
        dailyBudget: '$30-50',
        expectedROAS: '2.5x - 3.8x',
        reasoning: '短视频内容在TikTok年轻用户群中互动率最高，建议优先投放测试素材',
      },
      {
        platform: 'Meta Ads (FB+IG)',
        dailyBudget: '$40-60',
        expectedROAS: '2.0x - 3.2x',
        reasoning: 'Facebook用户群体消费力更强，适合搭配Instagram视觉内容联合投放',
      },
      {
        platform: 'Google Ads',
        dailyBudget: '$20-30',
        expectedROAS: '1.8x - 2.5x',
        reasoning: '搜索意图明确，适合长尾关键词+购物广告组合，ROI稳定',
      },
    ],
    budgetAllocation: [
      { platform: 'TikTok Ads', percentage: 30 },
      { platform: 'Meta Ads', percentage: 45 },
      { platform: 'Google Ads', percentage: 25 },
    ],
  },
}

// ============ Mock 进度模拟 ============

export function simulateProgress(
  onUpdate: (progress: GenerationProgress) => void,
  onComplete: () => void
): () => void {
  const taskId = `task_${Date.now()}`
  const steps: GenerationProgress['steps'] = {
    script: 'waiting',
    voiceover: 'waiting',
    videoRender: 'waiting',
    copyOptimize: 'waiting',
  }

  let cancelled = false
  const timeline = [
    { delay: 800, step: 'script' as const, message: '正在分析产品卖点，生成脚本框架...' },
    { delay: 2800, step: 'script' as const, message: '脚本生成完成 ✓' },
    { delay: 1000, step: 'voiceover' as const, message: '正在进行AI配音合成...' },
    { delay: 3200, step: 'voiceover' as const, message: '配音合成完成 ✓' },
    { delay: 1000, step: 'videoRender' as const, message: '正在渲染视频素材...' },
    { delay: 3500, step: 'videoRender' as const, message: '视频渲染完成 ✓' },
    { delay: 800, step: 'copyOptimize' as const, message: '正在优化多平台文案...' },
    { delay: 2200, step: 'copyOptimize' as const, message: '文案优化完成 ✓' },
  ]

  let elapsed = 0
  timeline.forEach(({ delay, step, message }) => {
    elapsed += delay
    setTimeout(() => {
      if (cancelled) return

      if (message.includes('✓')) {
        steps[step] = 'completed'
      } else {
        steps[step] = 'active'
      }

      onUpdate({
        taskId,
        status: 'generating',
        steps: { ...steps },
        message,
      })
    }, elapsed)
  })

  const totalTime = elapsed + 500
  setTimeout(() => {
    if (cancelled) return
    onComplete()
  }, totalTime)

  return () => {
    cancelled = true
  }
}

// ============ Mock 任务历史 ============

export const mockTasks: TaskRecord[] = [
  {
    taskId: 'task_001',
    productName: '便携式蓝牙音箱',
    createdAt: '2026-07-16T10:30:00',
    status: 'completed',
    platforms: ['TikTok', 'Instagram', 'Facebook'],
    contentTypes: ['短视频', '社媒文案'],
  },
  {
    taskId: 'task_002',
    productName: '瑜伽运动水壶',
    createdAt: '2026-07-15T14:20:00',
    status: 'completed',
    platforms: ['TikTok', 'Pinterest'],
    contentTypes: ['社媒文案'],
  },
  {
    taskId: 'task_003',
    productName: '无线充电器',
    createdAt: '2026-07-15T09:15:00',
    status: 'completed',
    platforms: ['Instagram', 'YouTube Shorts'],
    contentTypes: ['短视频'],
  },
  {
    taskId: 'task_004',
    productName: '智能LED台灯',
    createdAt: '2026-07-14T16:45:00',
    status: 'completed',
    platforms: ['TikTok', 'Instagram', 'Facebook', 'Pinterest'],
    contentTypes: ['短视频', '社媒文案'],
  },
]

// ============ Mock 周统计 ============

export const mockWeeklyStats: WeeklyStats = {
  videoCount: 12,
  copyCount: 28,
  strategyCount: 8,
  totalTasks: 10,
  completedTasks: 8,
}

// ============ Mock 投放策略 ============

export const mockStrategyData: StrategyData = {
  recommendedChannels: [
    {
      channel: 'TikTok Ads',
      rating: 5,
      dailyBudget: 50,
      estimatedROAS: '2.8-4.2x',
      reason: '产品视觉冲击力强，TikTok 年轻用户群互动率远超其他平台，短视频形式完美展示产品亮点',
    },
    {
      channel: 'Meta Ads',
      rating: 4,
      dailyBudget: 30,
      estimatedROAS: '2.0-3.5x',
      reason: 'Facebook+Instagram 组合覆盖更广泛年龄段，兴趣定向精准，适合品牌认知+转化双目标',
    },
    {
      channel: 'Google Ads',
      rating: 3,
      dailyBudget: 20,
      estimatedROAS: '1.5-2.8x',
      reason: '搜索意图明确，适合长尾关键词+购物广告组合，作为搜索流量的防守型投放',
    },
  ],
  budgetAllocation: [
    { channel: 'TikTok', value: 50 },
    { channel: 'Meta', value: 30 },
    { channel: 'Google', value: 20 },
  ],
  keySuggestions: [
    '优先在 TikTok 投放 15-30 秒短视频，突出产品核心卖点',
    'A/B 测试不同素材角度（开箱实测 vs 场景展示 vs 对比评测）',
    'Meta Ads 使用"视频+轮播图"组合，提升广告疲劳阈值',
    'Google Ads 以品牌词+品类词防守为主，搜索流量 ROI 最稳定',
    '每周分析各渠道 ROAS 数据，动态调整预算分配比例',
  ],
}

// ============ Mock 数据分析 ============

export const mockAnalyticsData: AnalyticsData = {
  summary: {
    totalContent: 48,
    videoCount: 16,
    copyCount: 32,
    strategyCount: 12,
  },
  platformDistribution: [
    { platform: 'TikTok', count: 18 },
    { platform: 'Instagram', count: 12 },
    { platform: 'YouTube Shorts', count: 8 },
    { platform: 'Facebook', count: 7 },
    { platform: 'Pinterest', count: 3 },
  ],
  recentTasks: [
    {
      id: 'task_001',
      productName: '便携式蓝牙音箱',
      platformCount: 3,
      marketCount: 2,
      createdAt: '2026-07-16T10:30:00',
      status: 'completed',
    },
    {
      id: 'task_002',
      productName: '瑜伽运动水壶',
      platformCount: 2,
      marketCount: 3,
      createdAt: '2026-07-15T14:20:00',
      status: 'completed',
    },
    {
      id: 'task_003',
      productName: '无线充电器',
      platformCount: 2,
      marketCount: 1,
      createdAt: '2026-07-15T09:15:00',
      status: 'completed',
    },
    {
      id: 'task_004',
      productName: '智能LED台灯',
      platformCount: 4,
      marketCount: 2,
      createdAt: '2026-07-14T16:45:00',
      status: 'completed',
    },
    {
      id: 'task_005',
      productName: '户外折叠椅',
      platformCount: 1,
      marketCount: 3,
      createdAt: '2026-07-14T08:00:00',
      status: 'generating',
    },
  ],
}
