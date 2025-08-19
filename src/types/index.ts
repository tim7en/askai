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
