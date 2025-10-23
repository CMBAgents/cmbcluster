#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Read environment variables from root .env file
function readRootEnv() {
  const rootEnvPath = path.join(__dirname, '../../../.env');
  const env = {};
  
  if (fs.existsSync(rootEnvPath)) {
    const content = fs.readFileSync(rootEnvPath, 'utf8');
    content.split('\n').forEach(line => {
      const trimmed = line.trim();
      if (trimmed && !trimmed.startsWith('#')) {
        const [key, ...valueParts] = trimmed.split('=');
        if (key && valueParts.length > 0) {
          env[key.trim()] = valueParts.join('=').trim().replace(/^['"]|['"]$/g, '');
        }
      }
    });
  }
  
  return env;
}

// Generate NextJS environment file
function generateNextJSEnv() {
  const rootEnv = readRootEnv();
  const isDev = process.env.NODE_ENV === 'development' || process.argv.includes('--dev');
  
  // Determine URLs based on environment
  const apiUrl = isDev ? 'http://localhost:8000' : rootEnv.API_URL || 'https://api.35.188.79.156.nip.io';
  const frontendUrl = isDev ? 'http://localhost:3001' : rootEnv.FRONTEND_URL || 'https://35.188.79.156.nip.io';
  
  const envContent = `# Environment Configuration${isDev ? ' for Local Development' : ' for Production'}
PORT=${isDev ? '3001' : '8501'}
NEXT_PUBLIC_PORT=${isDev ? '3001' : '8501'}

# API Configuration${isDev ? ' - using local backend' : ' - using production backend from root .env'}
NEXT_PUBLIC_API_URL=${apiUrl}
API_URL=${apiUrl}

# NextAuth Configuration
NEXTAUTH_URL=${frontendUrl}
NEXTAUTH_SECRET=${rootEnv.SECRET_KEY || 'development-secret-key-change-in-production'}

# Google OAuth Configuration (from root .env)
GOOGLE_CLIENT_ID=${rootEnv.GOOGLE_CLIENT_ID || ''}
GOOGLE_CLIENT_SECRET=${rootEnv.GOOGLE_CLIENT_SECRET || ''}

# Theme Colors (matching Streamlit dark theme)
NEXT_PUBLIC_PRIMARY_COLOR=#4A9EFF
NEXT_PUBLIC_BACKGROUND_COLOR=#0E1117
NEXT_PUBLIC_SECONDARY_COLOR=#1A1F2E
NEXT_PUBLIC_TERTIARY_COLOR=#252B3A
NEXT_PUBLIC_TEXT_PRIMARY=#FFFFFF
NEXT_PUBLIC_TEXT_SECONDARY=#E2E8F0

# App Configuration
NEXT_PUBLIC_APP_TITLE=CMBAgent Cloud
NEXT_PUBLIC_APP_TAGLINE=Your gateway to autonomous research

# Development/Production mode
DEV_MODE=${isDev ? 'true' : rootEnv.DEV_MODE || 'false'}
DEBUG=${isDev ? 'true' : rootEnv.DEBUG || 'false'}

# Domain configuration
NEXT_PUBLIC_DOMAIN=${rootEnv.DOMAIN || '35.188.79.156.nip.io'}
NEXT_PUBLIC_API_DOMAIN=${rootEnv.API_URL ? new URL(rootEnv.API_URL).host : 'api.35.188.79.156.nip.io'}
`;

  // Write to .env.local
  const envPath = path.join(__dirname, '../.env.local');
  fs.writeFileSync(envPath, envContent);
  

}

// Run the script
if (require.main === module) {
  try {
    generateNextJSEnv();
  } catch (error) {
    console.error('❌ Error generating environment configuration:', error.message);
    process.exit(1);
  }
}

module.exports = { generateNextJSEnv, readRootEnv };