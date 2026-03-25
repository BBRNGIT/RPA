/**
 * LLM Train API Route
 */

import { NextRequest, NextResponse } from 'next/server';

const LLM_SERVICE_PORT = 3033;

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    const response = await fetch(`http://localhost:${LLM_SERVICE_PORT}/train`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('LLM Train error:', error);
    return NextResponse.json(
      { error: 'LLM service not available' },
      { status: 503 }
    );
  }
}
