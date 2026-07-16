/**
 * 前后端数据格式转换
 *
 * 后端 snake_case + 中文/英文枚举 ↔ 前端 camelCase + 中文枚举
 */

import type { ProductInfo, TargetPlatform, ContentType } from '../types'

// ---------- 后端请求格式 ----------
export interface BackendGenerateRequest {
  product_name: string
  product_selling_points: string[]
  product_description?: string | null
  target_markets: string[]
  target_platforms: string[]
  content_types: string[]
  product_image_url?: string | null
}

// ---------- 平台 ID 映射 ----------
const PLATFORM_TO_ID: Record<TargetPlatform, string> = {
  TikTok: 'tiktok',
  Instagram: 'instagram',
  'YouTube Shorts': 'youtube_shorts',
  Facebook: 'facebook',
  Pinterest: 'pinterest',
}

const ID_TO_PLATFORM: Record<string, TargetPlatform> = Object.fromEntries(
  Object.entries(PLATFORM_TO_ID).map(([k, v]) => [v, k])
) as Record<string, TargetPlatform>

// ---------- 内容类型映射 ----------
const CONTENT_TYPE_TO_ID: Record<ContentType, string> = {
  '短视频': 'video',
  '社媒文案': 'copy',
}

const ID_TO_CONTENT_TYPE: Record<string, ContentType> = {
  video: '短视频',
  copy: '社媒文案',
}

// ---------- 转换函数 ----------

/** 前端 ProductInfo → 后端 GenerateRequest */
export function toBackendRequest(info: ProductInfo): BackendGenerateRequest {
  return {
    product_name: info.productName,
    product_selling_points: info.productDescription
      ? info.productDescription.split('\n').filter(Boolean)
      : [],
    product_description: info.productDescription || null,
    target_markets: info.targetMarkets,
    target_platforms: info.targetPlatforms.map((p) => PLATFORM_TO_ID[p] || p),
    content_types: info.contentTypes.map((t) => CONTENT_TYPE_TO_ID[t] || t),
    product_image_url: null,
  }
}

/** 后端平台 ID → 前端显示名 */
export function fromPlatformId(id: string): TargetPlatform {
  return ID_TO_PLATFORM[id] || (id as TargetPlatform)
}

/** 后端内容类型 ID → 前端显示名 */
export function fromContentTypeId(id: string): ContentType {
  return ID_TO_CONTENT_TYPE[id] || (id as ContentType)
}
