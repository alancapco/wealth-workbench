import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AppProvider } from '@/lib/app-context';
import { AppChrome } from '@/components/AppChrome';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'WM Workbench',
  description: 'Relationship Manager Workbench — live book, advice and governance',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <AppProvider>
          <AppChrome>{children}</AppChrome>
        </AppProvider>
      </body>
    </html>
  );
}
