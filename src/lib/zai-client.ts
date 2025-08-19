interface ZAIMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

interface ZAIRequest {
  model: string;
  messages: ZAIMessage[];
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
}

interface ZAIResponse {
  choices: Array<{
    message: {
      role: string;
      content: string;
    };
    finish_reason: string;
  }>;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export class ZAIClient {
  private apiKey: string;
  private baseUrl: string;

  constructor() {
    this.apiKey = process.env.ZAI_API_KEY || '';
    this.baseUrl = process.env.ZAI_API_URL || 'https://open.bigmodel.cn/api/paas/v4/chat/completions';
    
    if (!this.apiKey) {
      throw new Error('ZAI_API_KEY environment variable is required');
    }
  }

  async analyzeFile(fileContent: string, fileName: string, prompt: string): Promise<string> {
    const systemPrompt = `You are an expert file analyzer. You will analyze files and provide detailed reports based on user requests. Always be thorough and specific in your analysis.`;
    
    const userPrompt = `Please analyze the following file and provide a report based on this request: "${prompt}"

File Name: ${fileName}
File Content:
${fileContent}

Please provide a comprehensive analysis addressing the user's specific request.`;

    const request: ZAIRequest = {
      model: 'glm-4-plus',
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPrompt }
      ],
      temperature: 0.7,
      max_tokens: 2000,
      stream: false
    };

    try {
      const response = await fetch(this.baseUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.apiKey}`,
        },
        body: JSON.stringify(request)
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`ZAI API error: ${response.status} - ${errorText}`);
      }

      const data: ZAIResponse = await response.json();
      
      if (!data.choices || data.choices.length === 0) {
        throw new Error('No response from ZAI API');
      }

      return data.choices[0].message.content;
    } catch (error) {
      console.error('ZAI API Error:', error);
      throw new Error(`Failed to analyze file: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }
}
