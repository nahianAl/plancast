import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Providers } from './providers'
import { Navbar } from '@/components/common/Navbar'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'PlanCast - AI-Powered Floor Plan to 3D Model Conversion',
  description: 'Transform your floor plans into stunning 3D models with AI-powered technology. Upload, preview, and export in multiple formats.',
  keywords: 'floor plan, 3D model, AI conversion, architecture, design, GLB, OBJ, STL',
  authors: [{ name: 'PlanCast Team' }],
  creator: 'PlanCast',
  publisher: 'PlanCast',
  formatDetection: {
    email: false,
    address: false,
    telephone: false,
  },
  metadataBase: new URL('https://plancast.app'),
  openGraph: {
    title: 'PlanCast - AI-Powered Floor Plan to 3D Model Conversion',
    description: 'Transform your floor plans into stunning 3D models with AI-powered technology.',
    url: 'https://plancast.app',
    siteName: 'PlanCast',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'PlanCast - Floor Plan to 3D Model Conversion',
      },
    ],
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'PlanCast - AI-Powered Floor Plan to 3D Model Conversion',
    description: 'Transform your floor plans into stunning 3D models with AI-powered technology.',
    images: ['/og-image.png'],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  verification: {
    google: 'your-google-verification-code',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>
          <div className="min-h-screen bg-background">
            <Navbar />
            <main className="flex-1">
              {children}
            </main>
          </div>
        </Providers>
      </body>
    </html>
  )
}
