import type {
  GenerationResult,
  TaskRecord,
  WeeklyStats,
  GenerationProgress,
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
