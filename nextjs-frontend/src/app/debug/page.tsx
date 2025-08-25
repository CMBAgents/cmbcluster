'use client';

import { useEffect, useState } from 'react';

export default function DebugPage() {
  const [config, setConfig] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        console.log('Fetching /api/config...');
        const response = await fetch('/api/config');
        console.log('Response status:', response.status);
        
        if (response.ok) {
          const data = await response.json();
          console.log('Config data:', data);
          setConfig(data);
        } else {
          const errorText = await response.text();
          console.error('Config fetch failed:', response.status, errorText);
          setError(`HTTP ${response.status}: ${errorText}`);
        }
      } catch (err) {
        console.error('Config fetch error:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
      }
    };

    fetchConfig();
  }, []);

  return (
    <div style={{ padding: '20px', fontFamily: 'monospace' }}>
      <h1>Debug Page</h1>
      
      <h2>Environment Variables (Client-side)</h2>
      <pre>{JSON.stringify({
        NODE_ENV: process.env.NODE_ENV,
        // Only NEXT_PUBLIC_ variables are available client-side
        NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
        NEXT_PUBLIC_API_DOMAIN: process.env.NEXT_PUBLIC_API_DOMAIN,
        NEXT_PUBLIC_DOMAIN: process.env.NEXT_PUBLIC_DOMAIN,
      }, null, 2)}</pre>

      <h2>Runtime Config from /api/config</h2>
      {error && <div style={{ color: 'red' }}>Error: {error}</div>}
      {config && <pre>{JSON.stringify(config, null, 2)}</pre>}
      {!config && !error && <div>Loading...</div>}

      <h2>API Client Test</h2>
      <button onClick={async () => {
        try {
          const { envValidator } = await import('@/lib/env-validator');
          const apiUrl = await envValidator.getApiUrlAsync();
          console.log('API URL from envValidator:', apiUrl);
          alert(`API URL: ${apiUrl}`);
        } catch (err) {
          console.error('envValidator error:', err);
          alert(`Error: ${err}`);
        }
      }}>
        Test envValidator.getApiUrlAsync()
      </button>
    </div>
  );
}