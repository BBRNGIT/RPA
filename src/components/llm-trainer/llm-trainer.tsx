"use client";

import { useState, useEffect, useCallback } from 'react';

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  time: string;
}

interface ModelConfig {
  vocab_size: number;
  d_model: number;
  num_heads: number;
  num_layers: number;
  max_seq_len: number;
}

interface TrainingStats {
  epochs?: number;
  final_loss?: number;
  best_loss?: number;
  params?: number;
}

export default function LLMTrainer() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [modelLoaded, setModelLoaded] = useState(false);
  const [modelConfig, setModelConfig] = useState<ModelConfig | null>(null);
  const [trainingStats, setTrainingStats] = useState<TrainingStats | null>(null);

  // Generation settings
  const [temperature, setTemperature] = useState(0.8);
  const [topK, setTopK] = useState(40);
  const [maxTokens, setMaxTokens] = useState(50);

  // Training settings
  const [trainingEpochs, setTrainingEpochs] = useState(10);
  const [training, setTraining] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  useEffect(() => {
    loadModelInfo();
  }, []);

  const loadModelInfo = async () => {
    try {
      const weightsResponse = await fetch('/docs/model_weights.json');
      if (weightsResponse.ok) {
        const weights = await weightsResponse.json();
        setTrainingStats(weights.training_stats || {});
        setModelConfig(weights.config);
        setModelLoaded(true);
        addMessage('system', 'Model loaded! Ready for inference.');
      }
    } catch (e) {
      addMessage('system', 'No trained model found. Train locally first.');
    }
  };

  const addMessage = useCallback((role: Message['role'], content: string) => {
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    setMessages(prev => [...prev, { role, content, time }]);
  }, []);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    addMessage('user', userMessage);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('/api/llm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: userMessage,
          max_tokens: maxTokens,
          temperature,
          top_k: topK,
        }),
      });

      const data = await response.json();

      if (data.success && data.generated) {
        addMessage('assistant', data.generated);
      } else {
        addMessage('system', 'Backend not available. Use GitHub Pages for JS inference.');
      }
    } catch (e) {
      addMessage('system', 'Error: Could not connect to backend.');
    }

    setLoading(false);
  };

  const startTraining = async () => {
    setTraining(true);
    addMessage('system', `Starting training for ${trainingEpochs} epochs...`);

    try {
      const response = await fetch('/api/llm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'train',
          epochs: trainingEpochs,
        }),
      });

      const data = await response.json();
      addMessage('system', data.message || 'Training started in background.');
    } catch (e) {
      addMessage('system', 'Training requires local Python environment.');
    }

    setTraining(false);
  };

  const clearChat = () => {
    setMessages([]);
    addMessage('system', 'Chat cleared. Model ready.');
  };

  return (
    <div className="flex flex-col h-full bg-slate-900 text-white rounded-lg overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-slate-700 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🧠</span>
          <div>
            <h1 className="font-semibold">RPA Neural LLM</h1>
            <p className="text-xs text-slate-400">
              {modelLoaded && modelConfig
                ? `${modelConfig.d_model}d, ${modelConfig.num_heads}h, ${modelConfig.num_layers}L`
                : 'Loading...'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${modelLoaded ? 'bg-green-500' : 'bg-yellow-500'}`} />
          <span className="text-xs text-slate-400">
            {modelLoaded ? 'Ready' : 'No Model'}
          </span>
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="ml-2 px-3 py-1 text-xs bg-slate-700 rounded hover:bg-slate-600"
          >
            ⚙️ Settings
          </button>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="p-4 border-b border-slate-700 bg-slate-800 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            {/* Generation Settings */}
            <div className="space-y-3">
              <h3 className="font-medium text-sm">Generation</h3>

              <div>
                <label className="text-xs text-slate-400">Temperature: {temperature}</label>
                <input
                  type="range"
                  min="0.1"
                  max="2"
                  step="0.1"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  className="w-full h-1 bg-slate-600 rounded"
                />
              </div>

              <div>
                <label className="text-xs text-slate-400">Top-K: {topK}</label>
                <input
                  type="range"
                  min="1"
                  max="100"
                  value={topK}
                  onChange={(e) => setTopK(parseInt(e.target.value))}
                  className="w-full h-1 bg-slate-600 rounded"
                />
              </div>

              <div>
                <label className="text-xs text-slate-400">Max Tokens: {maxTokens}</label>
                <input
                  type="range"
                  min="10"
                  max="200"
                  step="10"
                  value={maxTokens}
                  onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                  className="w-full h-1 bg-slate-600 rounded"
                />
              </div>
            </div>

            {/* Training Settings */}
            <div className="space-y-3">
              <h3 className="font-medium text-sm">Training</h3>

              <div>
                <label className="text-xs text-slate-400">Epochs: {trainingEpochs}</label>
                <input
                  type="range"
                  min="5"
                  max="100"
                  step="5"
                  value={trainingEpochs}
                  onChange={(e) => setTrainingEpochs(parseInt(e.target.value))}
                  className="w-full h-1 bg-slate-600 rounded"
                />
              </div>

              <button
                onClick={startTraining}
                disabled={training}
                className={`w-full py-2 rounded text-sm font-medium ${
                  training
                    ? 'bg-slate-600 cursor-not-allowed'
                    : 'bg-purple-600 hover:bg-purple-500'
                }`}
              >
                {training ? 'Training...' : 'Train Model'}
              </button>

              <button
                onClick={clearChat}
                className="w-full py-2 rounded text-sm bg-slate-700 hover:bg-slate-600"
              >
                Clear Chat
              </button>
            </div>
          </div>

          {/* Stats */}
          {trainingStats && (
            <div className="grid grid-cols-4 gap-2 text-center text-xs">
              <div className="bg-slate-700 rounded p-2">
                <div className="font-bold text-cyan-400">
                  {trainingStats.params?.toLocaleString() || '-'}
                </div>
                <div className="text-slate-400">Params</div>
              </div>
              <div className="bg-slate-700 rounded p-2">
                <div className="font-bold text-cyan-400">
                  {trainingStats.epochs || '-'}
                </div>
                <div className="text-slate-400">Epochs</div>
              </div>
              <div className="bg-slate-700 rounded p-2">
                <div className="font-bold text-green-400">
                  {trainingStats.best_loss?.toFixed(4) || '-'}
                </div>
                <div className="text-slate-400">Best Loss</div>
              </div>
              <div className="bg-slate-700 rounded p-2">
                <div className="font-bold text-green-400">
                  {trainingStats.final_loss?.toFixed(4) || '-'}
                </div>
                <div className="text-slate-400">Final Loss</div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex gap-3 ${
              msg.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                msg.role === 'user'
                  ? 'bg-purple-600'
                  : msg.role === 'system'
                  ? 'bg-slate-700 border border-dashed border-slate-500'
                  : 'bg-slate-600'
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
              <p className="text-[10px] text-slate-300 mt-1">{msg.time}</p>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex gap-3">
            <div className="bg-slate-600 rounded-lg p-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce" />
                <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce [animation-delay:0.1s]" />
                <span className="w-2 h-2 bg-purple-400 rounded-full animate-bounce [animation-delay:0.2s]" />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-4 border-t border-slate-700 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
          placeholder="Type a message..."
          disabled={loading}
          className="flex-1 bg-slate-700 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50"
        />
        <button
          onClick={sendMessage}
          disabled={loading || !input.trim()}
          className="px-6 py-2 bg-purple-600 rounded-lg text-sm font-medium hover:bg-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Send
        </button>
      </div>
    </div>
  );
}
