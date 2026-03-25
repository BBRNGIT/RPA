/**
 * LLM Chat API Route
 */

import { NextRequest, NextResponse } from 'next/server';

const LLM_SERVICE_PORT = 3033;

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    const response = await fetch(`http://localhost:${LLM_SERVICE_PORT}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('LLM Chat error:', error);
    return NextResponse.json(
      { error: 'LLM service not available' },
      { status: 503 }
    );
  }
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const prompt = searchParams.get('prompt');
  const maxTokens = searchParams.get('max_tokens') || '100';
  const temperature = searchParams.get('temperature') || '0.8';
  
  if (!prompt) {
    return NextResponse.json({ error: 'No prompt provided' }, { status: 400 });
  }
  
  try {
    const url = `http://localhost:${LLM_SERVICE_PORT}/generate?prompt=${encodeURIComponent(prompt)}&max_tokens=${maxTokens}&temperature=${temperature}`;
    const response = await fetch(url);
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('LLM Generate error:', error);
    return NextResponse.json(
      { error: 'LLM service not available' },
      { status: 503 }
    );
  }
}
