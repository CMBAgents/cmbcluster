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
    <html lang="en" data-theme="dark">
      <body className={inter.className}>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  );
}
