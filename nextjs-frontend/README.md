# CMBAgent Cloud - Next.js Frontend

This is the Next.js frontend for CMBAgent Cloud, migrated from Streamlit while maintaining all functionality and APIs.

## 🚀 Quick Start

### Prerequisites

- Node.js 18.x or later
- npm or yarn
- Backend API running on port 8000

### Installation

1. **Install dependencies:**
   ```bash
   cd nextjs-frontend
   npm install
   ```

2. **Set up environment variables:**
   ```bash
   # Copy the example environment file
   copy env.example .env.local
   
   # Edit .env.local with your actual values:
   # - Google OAuth credentials
   # - API URL
   # - NextAuth secret
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

4. **Access the application:**
   Open [http://localhost:8501](http://localhost:8501) in your browser.

## 📋 Features

### ✅ Implemented in Task 1

- [x] **Next.js 14** with TypeScript and App Router
- [x] **Port 8501** configuration (same as Streamlit)
- [x] **Ant Design UI** library with dark theme
- [x] **Project Structure:**
  - `components/` - Reusable UI components
    - `auth/` - Authentication components
    - `environments/` - Environment management
    - `storage/` - Storage management
    - `monitoring/` - Environment monitoring
    - `settings/` - Settings pages
  - `lib/` - Utilities and API client
  - `hooks/` - Custom React hooks
  - `types/` - TypeScript type definitions
  - `utils/` - Helper functions

- [x] **Dependencies Installed:**
  - Core: Next.js 14, React 18, TypeScript
  - UI: Ant Design, Ant Design Icons, Ant Design Charts
  - Auth: NextAuth.js (Google OAuth ready)
  - API: Axios, TanStack React Query
  - Forms: React Hook Form, Zod validation
  - Utils: date-fns, clsx, tailwind-merge

- [x] **Configuration Files:**
  - `next.config.js` - Next.js config with port 8501
  - `tailwind.config.js` - Tailwind CSS with custom theme
  - `tsconfig.json` - TypeScript configuration
  - `.env.example` - Environment variables template

- [x] **TypeScript Types:**
  - User, Environment, StorageItem interfaces
  - API response types
  - Form data types
  - Component prop types

- [x] **Core Setup:**
  - Root layout with Ant Design ConfigProvider
  - Dark theme matching Streamlit colors exactly
  - Health check API route at `/api/health`
  - Global CSS with custom scrollbar
  - Logo files copied to `public/logos/`

- [x] **Authentication Setup:**
  - NextAuth.js configuration
  - Google OAuth provider
  - Sign-in page with professional design
  - Session management

- [x] **API Client:**
  - Axios-based client with interceptors
  - All API endpoints from original `api_client.py`
  - Error handling and timeout configuration
  - Auth token management

- [x] **Component Structure:**
  - Main page with tabs (Environments, Storage, Monitoring)
  - User info sidebar
  - Environment management with table view
  - Storage and monitoring placeholder components

## 🔧 Configuration

### Environment Variables

Create a `.env.local` file with the following variables:

```bash
# Port Configuration
PORT=8501
NEXT_PUBLIC_PORT=8501

# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
API_URL=http://localhost:8000

# NextAuth Configuration
NEXTAUTH_URL=http://localhost:8501
NEXTAUTH_SECRET=your-secret-key-here

# Google OAuth (get from Google Cloud Console)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Theme Colors (matching Streamlit)
NEXT_PUBLIC_PRIMARY_COLOR=#4A9EFF
NEXT_PUBLIC_BACKGROUND_COLOR=#0E1117
NEXT_PUBLIC_SECONDARY_COLOR=#1A1F2E
NEXT_PUBLIC_TERTIARY_COLOR=#252B3A
NEXT_PUBLIC_TEXT_PRIMARY=#FFFFFF
NEXT_PUBLIC_TEXT_SECONDARY=#E2E8F0

# App Configuration
NEXT_PUBLIC_APP_TITLE=CMBAgent Cloud
NEXT_PUBLIC_APP_TAGLINE=Your gateway to autonomous research
```

### Theme Configuration

The application uses a dark theme that exactly matches the original Streamlit design:

- **Primary Color:** `#4A9EFF` (matching original)
- **Background Colors:** 
  - Primary: `#0E1117`
  - Secondary: `#1A1F2E`
  - Tertiary: `#252B3A`
- **Text Colors:**
  - Primary: `#FFFFFF`
  - Secondary: `#E2E8F0`

## 🏗️ Architecture

### Project Structure

```
src/
├── app/                    # Next.js App Router
│   ├── api/               # API routes
│   │   ├── auth/          # NextAuth configuration
│   │   └── health/        # Health check endpoint
│   ├── auth/              # Authentication pages
│   │   └── signin/        # Sign-in page
│   ├── globals.css        # Global styles
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Home page
├── components/            # Reusable components
│   ├── auth/             # Authentication components
│   ├── environments/     # Environment management
│   ├── storage/          # Storage management
│   ├── monitoring/       # Environment monitoring
│   └── settings/         # Settings components
├── lib/                  # Utilities and configuration
│   ├── api-client.ts     # API client (matches original)
│   └── utils.ts          # Helper functions
├── types/                # TypeScript definitions
│   └── index.ts          # All type definitions
└── hooks/                # Custom React hooks
```

### API Client

The API client (`lib/api-client.ts`) maintains 100% compatibility with the original Streamlit version:

- All endpoints from `components/api_client.py`
- Same request/response formats
- Error handling patterns
- Authentication integration

### Components

1. **Environment Management** (`components/environments/`)
   - Environment list with status
   - Launch new environments
   - Restart/stop operations
   - Resource configuration

2. **Storage Management** (`components/storage/`)
   - Workspace storage buckets
   - File management
   - Storage creation/deletion

3. **Monitoring** (`components/monitoring/`)
   - Environment status monitoring
   - Resource usage metrics
   - Activity logs

4. **Settings** (`components/settings/`)
   - User preferences
   - Environment variables
   - File uploads

## 📦 Scripts

- `npm run dev` - Start development server on port 8501
- `npm run build` - Build for production
- `npm run start` - Start production server on port 8501
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript checks

## 🔍 Verification Checklist

- [x] Server starts on http://localhost:8501
- [x] Health endpoint responds at /api/health
- [x] Dark theme loads correctly matching Streamlit colors
- [x] No console errors in development
- [x] Logos display correctly (Cambridge and Infosys)
- [x] Authentication flow configured (Google OAuth)
- [x] API client matches original functionality
- [x] All components render without errors
- [x] Tailwind CSS working with custom theme
- [x] TypeScript compilation successful

## 🚧 Next Steps (Task 2+)

The foundation is complete. Next tasks will implement:

1. **Complete Component Implementation:**
   - Full environment management functionality
   - Storage management with file browser
   - Real-time monitoring dashboard
   - Settings pages with form validation

2. **Advanced Features:**
   - Real-time updates with WebSocket
   - Advanced filtering and search
   - Batch operations
   - Performance optimization

3. **Testing & Polish:**
   - Unit tests with Jest
   - E2E tests with Playwright
   - Performance optimization
   - Accessibility improvements

## 📄 License

This project is part of the CMBAgent Cloud system and follows the same licensing terms.

## 🤝 Contributing

Please follow the existing code patterns and ensure all changes maintain compatibility with the backend APIs.
