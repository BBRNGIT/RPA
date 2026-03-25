/**
 * API Proxy Route
 * 
 * Proxies requests to the RPA Core API backend running on port 8000.
 * This allows the frontend to make requests without CORS issues.
 */

import { NextRequest, NextResponse } from 'next/server';

const API_BASE_URL = 'http://localhost:8000';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  return proxyRequest(request, await params, 'GET');
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  return proxyRequest(request, await params, 'POST');
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  return proxyRequest(request, await params, 'PUT');
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  return proxyRequest(request, await params, 'DELETE');
}

async function proxyRequest(
  request: NextRequest,
  params: { path: string[] },
  method: string
) {
  try {
    // Build target URL
    const pathSegments = params.path || [];
    const searchParams = request.nextUrl.searchParams;
    
    // Remove XTransformPort from params since we're proxying directly
    searchParams.delete('XTransformPort');
    
    const targetUrl = `${API_BASE_URL}/${pathSegments.join('/')}${searchParams.toString() ? '?' + searchParams.toString() : ''}`;
    
    // Get request body if present
    let body: string | undefined;
    if (method !== 'GET' && method !== 'DELETE') {
      body = await request.text();
    }
    
    // Forward headers
    const headers: Record<string, string> = {};
    const authHeader = request.headers.get('authorization');
    if (authHeader) {
      headers['Authorization'] = authHeader;
    }
    if (body) {
      headers['Content-Type'] = 'application/json';
    }
    
    // Make request to backend
    const response = await fetch(targetUrl, {
      method,
      headers,
      body,
    });
    
    // Get response body
    const responseBody = await response.text();
    
    // Return proxied response
    return new NextResponse(responseBody, {
      status: response.status,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  } catch (error) {
    console.error('Proxy error:', error);
    return NextResponse.json(
      { error: 'Failed to connect to backend' },
      { status: 503 }
    );
  }
}
