import { NextRequest, NextResponse } from 'next/server';

// Force dynamic rendering since we use environment variables
export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  try {
    // Check if the application is healthy
    const health = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      version: process.env.npm_package_version || '1.0.0',
      environment: process.env.NODE_ENV || 'development',
      port: process.env.PORT || '8501',
    };

    return NextResponse.json(health, { status: 200 });
  } catch (error) {
    return NextResponse.json(
      {
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        error: 'Health check failed',
      },
      { status: 500 }
    );
  }
}
