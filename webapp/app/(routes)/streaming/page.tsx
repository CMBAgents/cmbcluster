'use client';

import { useState, useEffect } from 'react';

export default function StreamingPage() {
  const [data, setData] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);

  const startStreaming = async () => {
    setData('');
    setError(null);
    setIsStreaming(true);

    try {
      const response = await fetch('/api/stream');

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      if (!response.body) {
        throw new Error('Response body is null');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }

        const chunk = decoder.decode(value, { stream: true });
        // SSE format is "data: content\n\n"
        const lines = chunk.split('\n\n').filter(line => line.startsWith('data: '));
        for (const line of lines) {
            const content = line.substring(6);
            setData((prev) => prev + content + ' ');
        }
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsStreaming(false);
    }
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">LLM Token Streaming</h1>
      <div className="mb-4">
        <button
          onClick={startStreaming}
          disabled={isStreaming}
          className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded disabled:bg-gray-400"
        >
          {isStreaming ? 'Streaming...' : 'Start Streaming'}
        </button>
      </div>
      <div className="p-4 border rounded-lg bg-gray-50 min-h-[100px]">
        <p className="whitespace-pre-wrap">{data}</p>
        {error && <p className="text-red-500 mt-2">Error: {error}</p>}
      </div>
    </div>
  );
}
