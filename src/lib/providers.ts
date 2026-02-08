import { ChatProvider } from '@/types';

export interface ModelConfig {
  id: string;
  name: string;
  provider: ChatProvider;
  /** Cost per 1K input tokens in USD */
  inputCostPer1k: number;
  /** Cost per 1K output tokens in USD */
  outputCostPer1k: number;
  maxTokens: number;
}

/** Margin multiplier applied on top of base API cost */
export const MARGIN_MULTIPLIER = 1.4;

/** Discount for users in Uzbekistan (UZ) */
export const UZ_DISCOUNT = 0.25;

export const MODELS: Record<string, ModelConfig> = {
  'gpt-4o': {
    id: 'gpt-4o',
    name: 'GPT-4o',
    provider: 'openai',
    inputCostPer1k: 0.0025,
    outputCostPer1k: 0.01,
    maxTokens: 4096,
  },
  'gpt-4o-mini': {
    id: 'gpt-4o-mini',
    name: 'GPT-4o Mini',
    provider: 'openai',
    inputCostPer1k: 0.00015,
    outputCostPer1k: 0.0006,
    maxTokens: 4096,
  },
  'claude-sonnet-4-20250514': {
    id: 'claude-sonnet-4-20250514',
    name: 'Claude Sonnet 4',
    provider: 'anthropic',
    inputCostPer1k: 0.003,
    outputCostPer1k: 0.015,
    maxTokens: 4096,
  },
  'claude-3-5-haiku-20241022': {
    id: 'claude-3-5-haiku-20241022',
    name: 'Claude 3.5 Haiku',
    provider: 'anthropic',
    inputCostPer1k: 0.0008,
    outputCostPer1k: 0.004,
    maxTokens: 4096,
  },
};

export const DEFAULT_MODELS: Record<ChatProvider, string> = {
  openai: 'gpt-4o-mini',
  anthropic: 'claude-3-5-haiku-20241022',
};

export function getModelConfig(modelId: string): ModelConfig | undefined {
  return MODELS[modelId];
}

export function getModelsForProvider(provider: ChatProvider): ModelConfig[] {
  return Object.values(MODELS).filter((m) => m.provider === provider);
}

/**
 * Calculate cost with margin. Applies Uzbekistan discount when applicable.
 */
export function calculateCost(
  modelId: string,
  promptTokens: number,
  completionTokens: number,
  isUzbekistan: boolean = false,
): { baseCost: number; margin: number; totalCost: number } {
  const model = MODELS[modelId];
  if (!model) return { baseCost: 0, margin: 0, totalCost: 0 };

  const inputCost = (promptTokens / 1000) * model.inputCostPer1k;
  const outputCost = (completionTokens / 1000) * model.outputCostPer1k;
  const baseCost = inputCost + outputCost;

  let totalCost = baseCost * MARGIN_MULTIPLIER;

  if (isUzbekistan) {
    totalCost = totalCost * (1 - UZ_DISCOUNT);
  }

  const margin = totalCost - baseCost;

  const round = (v: number) => parseFloat(v.toFixed(6));
  return {
    baseCost: round(baseCost),
    margin: round(margin),
    totalCost: round(totalCost),
  };
}
