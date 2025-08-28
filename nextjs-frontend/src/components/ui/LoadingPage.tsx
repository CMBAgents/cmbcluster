'use client';

import { Spin } from 'antd';

export default function LoadingPage() {
  return (
    <div className="loading-page">
      <div className="loading-container">
        <div className="loading-logo">
          <img 
            src="/logos/cambridge-logo.png" 
            alt="Cambridge Logo" 
            className="w-16 h-16 mb-4"
          />
        </div>
        <Spin size="large" />
        <p className="loading-text">Loading...</p>
      </div>
    </div>
  );
}
