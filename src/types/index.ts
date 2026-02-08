export interface FileData {
  name: string;
  content: string;
  path: string;
  size: number;
  type: string;
}

export interface AnalysisRequest {
  files: FileData[];
  prompt: string;
}

export interface AnalysisResult {
  fileName: string;
  filePath: string;
  analysis: string;
  metadata: {
    size: number;
    type: string;
  };
}

export interface ApiResponse {
  success: boolean;
  message?: string;
  results?: AnalysisResult[];
  error?: string;
}

// Chat types
export type ChatProvider = 'openai' | 'anthropic';

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface ChatRequest {
  messages: ChatMessage[];
  provider: ChatProvider;
  model?: string;
  developerMode?: boolean;
}

export interface TokenUsage {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
}

export interface CostBreakdown {
  baseCost: number;
  margin: number;
  totalCost: number;
  currency: string;
}

export interface ChatResponse {
  success: boolean;
  content?: string;
  error?: string;
  usage?: TokenUsage;
  cost?: CostBreakdown;
  debug?: {
    provider: string;
    model: string;
    latencyMs: number;
    rawResponse?: unknown;
  };
}
