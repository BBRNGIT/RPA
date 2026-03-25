'use client';

/**
 * LLM Chat Box Component
 * 
 * Interactive chat interface for the RPA Neural LLM.
 * Users can chat with the locally-trained neural network.
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Slider } from '@/components/ui/slider';
import { Label } from '@/components/ui/label';
import { 
  Send, 
  Bot, 
  User, 
  Loader2, 
  Settings, 
  Brain,
  Sparkles,
  Trash2,
  Zap
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
}

interface LLMStatus {
  model_loaded: boolean;
  vocab_size: number;
  parameters: number;
  config: {
    d_model: number;
    num_heads: number;
    num_layers: number;
  };
}

interface LLMChatProps {
  className?: string;
}

export function LLMChat({ className }: LLMChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<LLMStatus | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [temperature, setTemperature] = useState(0.8);
  const [maxTokens, setMaxTokens] = useState(100);
  const [isTraining, setIsTraining] = useState(false);
  const [trainingText, setTrainingText] = useState('');
  
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Fetch LLM status on mount
  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch('/api/llm/status?XTransformPort=3033');
      if (response.ok) {
        const data = await response.json();
        setStatus(data);
      }
    } catch (error) {
      console.error('Failed to fetch LLM status:', error);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    // Add welcome message
    setMessages([
      {
        id: 'welcome',
        role: 'system',
        content: 'Welcome to RPA Neural LLM! This is a real neural network trained from scratch with backpropagation. It uses character-level tokenization (no word-piece). Ask me anything or type some code to see what I\'ve learned!',
        timestamp: new Date(),
      },
    ]);
  }, [fetchStatus]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/llm/chat?XTransformPort=3033', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage.content,
          max_tokens: maxTokens,
          temperature: temperature,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.response || data.generated || 'No response',
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || 'Failed to get response');
      }
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'system',
        content: `Error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const trainModel = async () => {
    if (!trainingText.trim() || isTraining) return;

    setIsTraining(true);
    try {
      const response = await fetch('/api/llm/train?XTransformPort=3033', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: trainingText.trim(),
          epochs: 5,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        const systemMessage: Message = {
          id: Date.now().toString(),
          role: 'system',
          content: `Training complete! Final loss: ${data.final_loss?.toFixed(4) || 'N/A'}`,
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, systemMessage]);
        setTrainingText('');
      }
    } catch (error) {
      console.error('Training error:', error);
    } finally {
      setIsTraining(false);
    }
  };

  const clearChat = () => {
    setMessages([
      {
        id: 'cleared',
        role: 'system',
        content: 'Chat cleared. Ready for new conversation!',
        timestamp: new Date(),
      },
    ]);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className={cn('flex flex-col h-full', className)}>
      {/* Header */}
      <CardHeader className="border-b px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-primary" />
            <CardTitle className="text-lg">RPA Neural LLM</CardTitle>
            {status?.model_loaded && (
              <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20">
                <Zap className="h-3 w-3 mr-1" />
                Online
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setShowSettings(!showSettings)}
              className="h-8 w-8"
            >
              <Settings className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={clearChat}
              className="h-8 w-8"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
        {status && (
          <CardDescription className="text-xs mt-1">
            {status.parameters?.toLocaleString()} params | {status.vocab_size} vocab | 
            {status.config?.num_layers} layers × {status.config?.num_heads} heads
          </CardDescription>
        )}
      </CardHeader>

      {/* Settings Panel */}
      {showSettings && (
        <div className="border-b p-4 space-y-4 bg-muted/50">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-xs">Temperature: {temperature.toFixed(1)}</Label>
              <Slider
                value={[temperature]}
                onValueChange={([v]) => setTemperature(v)}
                min={0.1}
                max={2}
                step={0.1}
              />
            </div>
            <div className="space-y-2">
              <Label className="text-xs">Max Tokens: {maxTokens}</Label>
              <Slider
                value={[maxTokens]}
                onValueChange={([v]) => setMaxTokens(v)}
                min={20}
                max={200}
                step={10}
              />
            </div>
          </div>
          
          <Separator />
          
          <div className="space-y-2">
            <Label className="text-xs flex items-center gap-2">
              <Sparkles className="h-3 w-3" />
              Train Model on Text
            </Label>
            <div className="flex gap-2">
              <Input
                value={trainingText}
                onChange={(e) => setTrainingText(e.target.value)}
                placeholder="Enter text to train on..."
                className="flex-1"
              />
              <Button 
                size="sm" 
                onClick={trainModel}
                disabled={isTraining || !trainingText.trim()}
              >
                {isTraining ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Train'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Messages */}
      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        <div className="space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                'flex gap-3',
                message.role === 'user' && 'justify-end',
                message.role === 'system' && 'justify-center'
              )}
            >
              {message.role !== 'user' && (
                <div className={cn(
                  'flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center',
                  message.role === 'assistant' ? 'bg-primary/10' : 'bg-muted'
                )}>
                  {message.role === 'assistant' ? (
                    <Bot className="h-4 w-4 text-primary" />
                  ) : (
                    <Sparkles className="h-4 w-4 text-muted-foreground" />
                  )}
                </div>
              )}
              <div
                className={cn(
                  'rounded-lg px-4 py-2 max-w-[80%]',
                  message.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : message.role === 'system'
                    ? 'bg-muted text-muted-foreground text-sm'
                    : 'bg-muted'
                )}
              >
                <p className="whitespace-pre-wrap break-words">{message.content}</p>
                <span className="text-xs opacity-50 mt-1 block">
                  {message.timestamp.toLocaleTimeString()}
                </span>
              </div>
              {message.role === 'user' && (
                <div className="flex-shrink-0 h-8 w-8 rounded-full bg-primary flex items-center justify-center">
                  <User className="h-4 w-4 text-primary-foreground" />
                </div>
              )}
            </div>
          ))}
          {isLoading && (
            <div className="flex gap-3">
              <div className="flex-shrink-0 h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                <Bot className="h-4 w-4 text-primary" />
              </div>
              <div className="bg-muted rounded-lg px-4 py-2">
                <Loader2 className="h-4 w-4 animate-spin" />
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Input */}
      <div className="border-t p-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            sendMessage();
          }}
          className="flex gap-2"
        >
          <Input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message..."
            disabled={isLoading}
            className="flex-1"
          />
          <Button type="submit" disabled={isLoading || !input.trim()}>
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </form>
        <p className="text-xs text-muted-foreground mt-2 text-center">
          RPA Neural LLM - Character-level tokenization, trained with backpropagation
        </p>
      </div>
    </div>
  );
}
