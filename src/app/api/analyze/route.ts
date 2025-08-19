import { NextRequest, NextResponse } from 'next/server';
import { ZAIClient } from '@/lib/zai-client';
import { AnalysisRequest, AnalysisResult, ApiResponse } from '@/types';

export async function POST(request: NextRequest) {
  try {
    const body: AnalysisRequest = await request.json();
    const { files, prompt } = body;

    if (!files || files.length === 0) {
      return NextResponse.json({
        success: false,
        error: 'No files provided'
      } as ApiResponse, { status: 400 });
    }

    if (!prompt || prompt.trim().length === 0) {
      return NextResponse.json({
        success: false,
        error: 'No analysis prompt provided'
      } as ApiResponse, { status: 400 });
    }

    const zaiClient = new ZAIClient();
    const results: AnalysisResult[] = [];

    // Process files sequentially to avoid rate limiting
    for (const file of files) {
      try {
        const analysis = await zaiClient.analyzeFile(file.content, file.name, prompt);
        
        results.push({
          fileName: file.name,
          filePath: file.path,
          analysis,
          metadata: {
            size: file.size,
            type: file.type
          }
        });
      } catch (error) {
        console.error(`Error analyzing file ${file.name}:`, error);
        results.push({
          fileName: file.name,
          filePath: file.path,
          analysis: `Error analyzing file: ${error instanceof Error ? error.message : 'Unknown error'}`,
          metadata: {
            size: file.size,
            type: file.type
          }
        });
      }
    }

    return NextResponse.json({
      success: true,
      results,
      message: `Successfully analyzed ${results.length} files`
    } as ApiResponse);

  } catch (error) {
    console.error('API Error:', error);
    return NextResponse.json({
      success: false,
      error: error instanceof Error ? error.message : 'Internal server error'
    } as ApiResponse, { status: 500 });
  }
}
