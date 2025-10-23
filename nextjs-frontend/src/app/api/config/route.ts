import { NextResponse } from 'next/server';

// Force dynamic rendering to ensure environment variables are read at runtime
export const dynamic = 'force-dynamic';
export const revalidate = 0;

export async function GET() {
  // Read environment variables at runtime using process.env directly
  const timestamp = new Date().toISOString();
  
  // Force fresh environment variable reading with explicit property access
  // Use server-side env vars first, then NEXT_PUBLIC_ vars, then defaults
  const apiUrl = process.env['API_URL'] || process.env['NEXT_PUBLIC_API_URL'] || 'http://localhost:8000';
  const apiDomain = process.env['NEXT_PUBLIC_API_DOMAIN'] || 'api.localhost';
  const domain = process.env['NEXT_PUBLIC_DOMAIN'] || 'localhost';
  const nextAuthUrl = process.env['NEXTAUTH_URL'] || 'http://localhost:3001';
  const nodeEnv = process.env['NODE_ENV'] || 'development';
  
  // Create debug object
  const envVars = {
    API_URL: process.env['API_URL'],
    NEXT_PUBLIC_API_URL: process.env['NEXT_PUBLIC_API_URL'],
    NEXT_PUBLIC_API_DOMAIN: process.env['NEXT_PUBLIC_API_DOMAIN'],
    NEXT_PUBLIC_DOMAIN: process.env['NEXT_PUBLIC_DOMAIN'],
    NEXTAUTH_URL: process.env['NEXTAUTH_URL'],
    NODE_ENV: nodeEnv
  };
  
  
  const config = {
    apiUrl,
    apiDomain,
    domain, 
    nextAuthUrl,
    nodeEnv,
    timestamp,
    debug: 'v2-runtime-env-vars'  // Version marker
  };
  
  
  return NextResponse.json(config);
}