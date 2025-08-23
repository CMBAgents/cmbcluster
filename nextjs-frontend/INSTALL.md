# Installation Guide

If you encounter ESLint dependency conflicts, try one of these solutions:

## Option 1: Clear npm cache and reinstall
```bash
cd nextjs-frontend
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

## Option 2: Use legacy peer deps flag
```bash
npm install --legacy-peer-deps
```

## Option 3: Force resolution
```bash
npm install --force
```

## Option 4: Use specific Node.js version
```bash
# Use Node.js 18.x or 20.x LTS
nvm use 18
npm install
```

The package.json is configured with compatible versions:
- ESLint: 8.57.0 (compatible with Next.js 14.2.5)
- Next.js: 14.2.5
- React: 18.3.1

After successful installation, start the development server:
```bash
npm run dev
```

The application will be available at http://localhost:8501
