'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { ConfigProvider, theme } from 'antd';

type Theme = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [currentTheme, setCurrentTheme] = useState<Theme>(() => {
    // Try to get theme from document attribute set by the script
    if (typeof window !== 'undefined') {
      const documentTheme = document.documentElement.getAttribute('data-theme') as Theme;
      if (documentTheme === 'dark' || documentTheme === 'light') {
        return documentTheme;
      }
      // Fallback to localStorage
      try {
        const savedTheme = localStorage.getItem('theme') as Theme;
        if (savedTheme === 'dark' || savedTheme === 'light') {
          return savedTheme;
        }
      } catch (e) {
        // localStorage might not be available
      }
    }
    return 'light';
  });

  useEffect(() => {
    // Sync with localStorage if not already set
    if (typeof window !== 'undefined') {
      try {
        const savedTheme = localStorage.getItem('theme') as Theme;
        if (savedTheme && savedTheme !== currentTheme) {
          setCurrentTheme(savedTheme);
        }
      } catch (e) {
        // localStorage might not be available
      }
    }
  }, []);

  useEffect(() => {
    // Apply theme to document
    if (typeof window !== 'undefined') {
      document.documentElement.setAttribute('data-theme', currentTheme);
      document.documentElement.className = currentTheme;
      try {
        localStorage.setItem('theme', currentTheme);
      } catch (e) {
        // localStorage might not be available
      }
    }
  }, [currentTheme]);

  const toggleTheme = () => {
    setCurrentTheme((prev: Theme) => prev === 'dark' ? 'light' : 'dark');
  };

  const antdTheme = {
    algorithm: currentTheme === 'dark' ? theme.darkAlgorithm : theme.defaultAlgorithm,
    token: {
      colorPrimary: '#4A9EFF',
      borderRadius: 8,
      colorBgContainer: currentTheme === 'dark' ? '#1A1F2E' : '#ffffff',
      colorBgElevated: currentTheme === 'dark' ? '#252B3A' : '#ffffff',
      colorText: currentTheme === 'dark' ? '#FFFFFF' : '#000000',
      colorTextSecondary: currentTheme === 'dark' ? '#E2E8F0' : '#666666',
      colorBorder: currentTheme === 'dark' ? '#2D3748' : '#d9d9d9',
    },
  };

  return (
    <ThemeContext.Provider value={{ theme: currentTheme, toggleTheme }}>
      <ConfigProvider theme={antdTheme}>
        {children}
      </ConfigProvider>
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}