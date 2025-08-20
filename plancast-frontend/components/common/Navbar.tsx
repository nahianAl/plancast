'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Box } from 'lucide-react'
import { DesktopNav } from './DesktopNav'
import { MobileNav } from './MobileNav'

export default function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  const navigation = [
    { name: 'Home', href: '/' },
    { name: 'Convert', href: '/convert' },
    { name: 'Demo', href: '/demo' },
    { name: 'Contact', href: '/contact' },
  ]

  return (
    <nav className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <Link href="/" className="flex-shrink-0 flex items-center space-x-2">
              <Box className="h-8 w-8 text-blue-600" />
              <span className="font-bold text-xl text-gray-800 dark:text-white">PlanCast</span>
            </Link>
          </div>
          <DesktopNav navigation={navigation} />
          <MobileNav isMenuOpen={isMenuOpen} setIsMenuOpen={setIsMenuOpen} navigation={navigation} />
        </div>
      </div>
    </nav>
  )
}

