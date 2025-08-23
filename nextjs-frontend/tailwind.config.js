/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#4A9EFF',
          50: '#EDF6FF',
          100: '#D6EAFF',
          200: '#B3D9FF',
          300: '#8AC4FF',
          400: '#66AFFF',
          500: '#4A9EFF',
          600: '#1E7FFF',
          700: '#0066E6',
          800: '#004DB3',
          900: '#003380',
        },
        background: {
          primary: '#0E1117',
          secondary: '#1A1F2E',
          tertiary: '#252B3A',
          accent: '#2D3748',
        },
        text: {
          primary: '#FFFFFF',
          secondary: '#E2E8F0',
          muted: '#A0AEC0',
          disabled: '#718096',
        },
        border: {
          primary: '#2D3748',
          secondary: '#4A5568',
          accent: '#4A9EFF',
        },
        success: '#48BB78',
        warning: '#ED8936',
        error: '#F56565',
        info: '#4299E1',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Monaco', 'Menlo', 'monospace'],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
      borderRadius: {
        '4xl': '2rem',
      },
      boxShadow: {
        'soft': '0 2px 8px rgba(0, 0, 0, 0.1)',
        'medium': '0 4px 12px rgba(0, 0, 0, 0.15)',
        'large': '0 8px 24px rgba(0, 0, 0, 0.2)',
        'glow': '0 0 20px rgba(74, 158, 255, 0.3)',
      },
    },
  },
  plugins: [],
}
