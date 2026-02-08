import { NextRequest, NextResponse } from 'next/server';
import { ChatRequest, ChatResponse } from '@/types';
import { chatCompletion } from '@/lib/chat-client';
import { calculateCost } from '@/lib/providers';

/**
 * Detect Uzbekistan from request headers.
 * Vercel / Cloudflare set x-vercel-ip-country or cf-ipcountry.
 * Falls back to accept-language containing 'uz'.
 */
function isUzbekistanRequest(request: NextRequest): boolean {
  const country =
    request.headers.get('x-vercel-ip-country') ||
    request.headers.get('cf-ipcountry') ||
    '';
  if (country.toUpperCase() === 'UZ') return true;

  const lang = request.headers.get('accept-language') || '';
  return lang.toLowerCase().includes('uz');
}

export async function POST(request: NextRequest) {
  try {
    const body: ChatRequest = await request.json();
    const { messages, provider, model, developerMode } = body;

    if (!messages || messages.length === 0) {
      return NextResponse.json(
        { success: false, error: 'No messages provided' } as ChatResponse,
        { status: 400 },
      );
    }

    if (!provider) {
      return NextResponse.json(
        { success: false, error: 'No provider specified' } as ChatResponse,
        { status: 400 },
      );
    }

    const start = Date.now();
    const result = await chatCompletion(messages, provider, model, developerMode);
    const latencyMs = Date.now() - start;

    const isUZ = isUzbekistanRequest(request);
    const cost = calculateCost(
      result.model,
      result.usage.promptTokens,
      result.usage.completionTokens,
      isUZ,
    );

    const response: ChatResponse = {
      success: true,
      content: result.content,
      usage: result.usage,
      cost: {
        baseCost: cost.baseCost,
        margin: cost.margin,
        totalCost: cost.totalCost,
        currency: 'USD',
      },
    };

    if (developerMode) {
      response.debug = {
        provider,
        model: result.model,
        latencyMs,
        rawResponse: result.rawResponse,
      };
    }

    return NextResponse.json(response);
  } catch (error) {
    console.error('Chat API Error:', error);
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Internal server error',
      } as ChatResponse,
      { status: 500 },
    );
  }
}
