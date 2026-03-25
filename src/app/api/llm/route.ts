/**
 * RPA LLM API - Backend Inference Endpoint
 * 
 * Uses Python subprocess for real neural inference
 */

import { NextRequest, NextResponse } from 'next/server';
import { exec } from 'child_process';
import { promisify } from 'util';
import path from 'path';

const execAsync = promisify(exec);

// Model config cache
let modelConfig: any = null;

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const action = searchParams.get('action') || 'status';
  
  if (action === 'status') {
    return NextResponse.json({
      status: 'ready',
      model: 'RPA Neural LLM',
      tokenizer: 'character-level',
      features: ['generation', 'training', 'export'],
    });
  }
  
  if (action === 'config') {
    try {
      const configPath = path.join(process.cwd(), 'RPA', 'model_storage', 'trained_model', 'config.json');
      const fs = require('fs');
      if (fs.existsSync(configPath)) {
        const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
        return NextResponse.json(config);
      }
    } catch (e) {
      // Ignore
    }
    return NextResponse.json({ error: 'Config not found' }, { status: 404 });
  }
  
  return NextResponse.json({ error: 'Unknown action' }, { status: 400 });
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { action, prompt, max_tokens, temperature, top_k, epochs } = body;
    
    // Generate using Python backend
    if (action === 'generate' || !action) {
      const maxTokens = max_tokens || 50;
      const temp = temperature || 0.8;
      const topK = top_k || 40;
      
      // Use Python for inference
      const scriptPath = path.join(process.cwd(), 'RPA', 'generate.py');
      const command = `python3 "${scriptPath}" --prompt "${(prompt || '').replace(/"/g, '\\"')}" --max-tokens ${maxTokens} --temperature ${temp} --top-k ${topK}`;
      
      try {
        const { stdout, stderr } = await execAsync(command, {
          timeout: 30000,
          cwd: path.join(process.cwd(), 'RPA'),
        });
        
        if (stdout.trim()) {
          return NextResponse.json({
            success: true,
            prompt: prompt,
            generated: stdout.trim(),
            max_tokens: maxTokens,
            temperature: temp,
            top_k: topK,
          });
        }
      } catch (e: any) {
        console.error('Python inference error:', e.message);
      }
      
      // Fallback to JS inference (load model_weights.json)
      return NextResponse.json({
        success: false,
        error: 'Python inference failed, use JS fallback',
        prompt: prompt,
      });
    }
    
    // Train endpoint
    if (action === 'train') {
      const epochsCount = epochs || 10;
      const scriptPath = path.join(process.cwd(), 'RPA', 'quick_train.py');
      
      // Start training (async)
      const command = `python3 "${scriptPath}" --epochs ${epochsCount}`;
      
      execAsync(command, {
        timeout: 300000, // 5 min timeout
        cwd: path.join(process.cwd(), 'RPA'),
      }).then(({ stdout }) => {
        console.log('Training output:', stdout);
      }).catch(e => {
        console.error('Training error:', e);
      });
      
      return NextResponse.json({
        success: true,
        message: 'Training started',
        epochs: epochsCount,
      });
    }
    
    // Export model
    if (action === 'export') {
      const weightsPath = path.join(process.cwd(), 'docs', 'model_weights.json');
      const fs = require('fs');
      
      if (fs.existsSync(weightsPath)) {
        const weights = JSON.parse(fs.readFileSync(weightsPath, 'utf-8'));
        return NextResponse.json({
          success: true,
          config: weights.config,
          params: weights.training_stats?.params || 'unknown',
        });
      }
      
      return NextResponse.json({
        success: false,
        error: 'No trained model found',
      });
    }
    
    return NextResponse.json({ error: 'Unknown action' }, { status: 400 });
    
  } catch (error: any) {
    console.error('API error:', error);
    return NextResponse.json({
      success: false,
      error: error.message,
    }, { status: 500 });
  }
}
