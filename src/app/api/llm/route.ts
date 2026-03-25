/**
 * LLM API Route
 * 
 * Proxies requests to the Python LLM mini-service
 */

import { NextRequest, NextResponse } from 'next/server';

const LLM_SERVICE_PORT = 3033;

async function proxyToLLMService(
  endpoint: string,
  method: string,
  body?: unknown
): Promise<NextResponse> {
  const url = `http://localhost:${LLM_SERVICE_PORT}${endpoint}`;
  
  try {
    const options: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    if (body && method !== 'GET') {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(url, options);
    const data = await response.json();

    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('LLM Service error:', error);
    return NextResponse.json(
      { error: 'LLM service unavailable. Make sure the Python LLM service is running on port ' + LLM_SERVICE_PORT },
      { status: 503 }
    );
  }
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const path = searchParams.get('path') || '/status';
  
  return proxyToLLMService(path, 'GET');
}

export async function POST(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const path = searchParams.get('path') || '/chat';
  
  let body;
  try {
    body = await request.json();
  } catch {
    body = {};
  }
  
  return proxyToLLMService(path, 'POST', body);
}
