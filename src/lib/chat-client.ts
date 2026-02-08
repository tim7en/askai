import { ChatMessage, TokenUsage, ChatProvider } from '@/types';
import { getModelConfig, DEFAULT_MODELS } from './providers';

interface CompletionResult {
  content: string;
  usage: TokenUsage;
  model: string;
  rawResponse?: unknown;
}

async function callOpenAI(
  messages: ChatMessage[],
  model: string,
  includeRaw: boolean,
): Promise<CompletionResult> {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) throw new Error('OPENAI_API_KEY is not configured');

  const config = getModelConfig(model);
  const body = {
    model,
    messages,
    max_tokens: config?.maxTokens ?? 4096,
    temperature: 0.7,
  };

  const res = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`OpenAI API error ${res.status}: ${err}`);
  }

  const data = await res.json();
  const choice = data.choices?.[0];
  if (!choice) throw new Error('No response from OpenAI');

  return {
    content: choice.message.content,
    usage: {
      promptTokens: data.usage?.prompt_tokens ?? 0,
      completionTokens: data.usage?.completion_tokens ?? 0,
      totalTokens: data.usage?.total_tokens ?? 0,
    },
    model,
    rawResponse: includeRaw ? data : undefined,
  };
}

async function callAnthropic(
  messages: ChatMessage[],
  model: string,
  includeRaw: boolean,
): Promise<CompletionResult> {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) throw new Error('ANTHROPIC_API_KEY is not configured');

  const config = getModelConfig(model);

  // Anthropic uses a separate system parameter
  const systemMsg = messages.find((m) => m.role === 'system');
  const nonSystemMessages = messages
    .filter((m) => m.role !== 'system')
    .map((m) => ({ role: m.role, content: m.content }));

  const body: Record<string, unknown> = {
    model,
    max_tokens: config?.maxTokens ?? 4096,
    messages: nonSystemMessages,
  };
  if (systemMsg) {
    body.system = systemMsg.content;
  }

  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Anthropic API error ${res.status}: ${err}`);
  }

  const data = await res.json();
  const textBlock = data.content?.find(
    (b: { type: string }) => b.type === 'text',
  );
  if (!textBlock) throw new Error('No text response from Anthropic');

  return {
    content: textBlock.text,
    usage: {
      promptTokens: data.usage?.input_tokens ?? 0,
      completionTokens: data.usage?.output_tokens ?? 0,
      totalTokens:
        (data.usage?.input_tokens ?? 0) + (data.usage?.output_tokens ?? 0),
    },
    model,
    rawResponse: includeRaw ? data : undefined,
  };
}

export async function chatCompletion(
  messages: ChatMessage[],
  provider: ChatProvider,
  model?: string,
  developerMode: boolean = false,
): Promise<CompletionResult> {
  const resolvedModel = model || DEFAULT_MODELS[provider];
  const config = getModelConfig(resolvedModel);

  if (!config) throw new Error(`Unknown model: ${resolvedModel}`);
  if (config.provider !== provider) {
    throw new Error(`Model ${resolvedModel} does not belong to provider ${provider}`);
  }

  switch (provider) {
    case 'openai':
      return callOpenAI(messages, resolvedModel, developerMode);
    case 'anthropic':
      return callAnthropic(messages, resolvedModel, developerMode);
    default:
      throw new Error(`Unsupported provider: ${provider}`);
  }
}
