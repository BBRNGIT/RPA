/**
 * LLM Status API Route
 */

import { NextResponse } from 'next/server';

const LLM_SERVICE_PORT = 3033;

export async function GET() {
  try {
    const response = await fetch(`http://localhost:${LLM_SERVICE_PORT}/status`);
    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('LLM Status error:', error);
    return NextResponse.json(
      { 
        model_loaded: false, 
        error: 'LLM service not running',
        parameters: 0,
        vocab_size: 0,
        config: { d_model: 0, num_heads: 0, num_layers: 0 }
      },
      { status: 503 }
    );
  }
}
