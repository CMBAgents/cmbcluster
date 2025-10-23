import { Inter } from 'next/font/google';
import { Providers } from '@/components/providers';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata = {
  title: 'CMBAgent Cloud - Enterprise Research Platform',
  description: 'CMBAgent Cloud - Enterprise research platform for autonomous discovery',
  keywords: 'research, AI, cloud computing, Cambridge, Infosys, data analysis',
  author: 'Cambridge-Infosys',
};

// Force dynamic rendering for all pages
export const dynamic = 'force-dynamic';


export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                function getInitialTheme() {
                  try {
                    const storedTheme = window.localStorage.getItem('theme');
                    if (storedTheme === 'dark' || storedTheme === 'light') return storedTheme;
                  } catch (e) {}
                  return 'light'; // Default to light theme
                }
                const theme = getInitialTheme();
                document.documentElement.setAttribute('data-theme', theme);
                document.documentElement.className = theme;
                // Also set a CSS custom property for immediate access
                document.documentElement.style.setProperty('--initial-theme', theme);
              })();
            `,
          }}
        />
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
