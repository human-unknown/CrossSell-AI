import { create } from 'zustand'
import type {
  ProductInfo,
  GenerationProgress,
  GenerationResult,
} from '../types'

interface CreateState {
  // Step tracking
  currentStep: 1 | 2 | 3

  // Step 1: Product info form
  productInfo: ProductInfo
  setProductInfo: (info: Partial<ProductInfo>) => void

  // Step 2: Generation progress
  progress: GenerationProgress | null
  isGenerating: boolean
  setProgress: (progress: GenerationProgress) => void
  setIsGenerating: (value: boolean) => void

  // Step 3: Results
  result: GenerationResult | null
  setResult: (result: GenerationResult) => void

  // Actions
  goToStep: (step: 1 | 2 | 3) => void
  reset: () => void
}

const defaultProductInfo: ProductInfo = {
  productName: '',
  productDescription: '',
  targetMarkets: [],
  targetPlatforms: [],
  contentTypes: [],
}

export const useCreateStore = create<CreateState>((set) => ({
  currentStep: 1,
  productInfo: { ...defaultProductInfo },
  setProductInfo: (info) =>
    set((s) => ({ productInfo: { ...s.productInfo, ...info } })),
  progress: null,
  isGenerating: false,
  setProgress: (progress) => set({ progress }),
  setIsGenerating: (value) => set({ isGenerating: value }),
  result: null,
  setResult: (result) => set({ result }),
  goToStep: (step) => set({ currentStep: step }),
  reset: () =>
    set({
      currentStep: 1,
      productInfo: { ...defaultProductInfo },
      progress: null,
      isGenerating: false,
      result: null,
    }),
}))
