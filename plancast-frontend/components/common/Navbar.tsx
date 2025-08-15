'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Menu,
  X
} from 'lucide-react';

const Navbar = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  // Handle scroll effect
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Close mobile menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (!target.closest('.mobile-menu') && !target.closest('.hamburger-button')) {
        setIsMobileMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const menuItems = [
    { name: 'Features', href: '#features' },
    { name: 'Pricing', href: '#pricing' },
    { name: 'About', href: '#about' },
    { name: 'Contact', href: '#contact' }
  ];

  return (
    <>
      {/* Navbar */}
      <motion.nav
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.5 }}
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          isScrolled 
            ? 'bg-white/95 backdrop-blur-md shadow-lg border-b border-gray-200/20' 
            : 'bg-transparent'
        }`}
      >
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-16 lg:h-20">
            {/* Logo */}
                               <motion.div
                     className="flex items-center space-x-2"
                     whileHover={{ scale: 1.05 }}
                     transition={{ duration: 0.2 }}
                   >
                     <div className={`w-8 h-8 ${isScrolled ? 'text-blue-600' : 'text-white'} flex items-center justify-center`}>
                       <div className="w-6 h-6 bg-gradient-to-br from-blue-400 to-cyan-400 rounded transform rotate-45"></div>
                     </div>
                     <span className={`text-xl font-bold ${isScrolled ? 'text-gray-900' : 'text-white'}`}>
                       PlanCast
                     </span>
                   </motion.div>

            {/* Desktop Menu */}
            <div className="hidden lg:flex items-center space-x-8">
              {menuItems.map((item) => (
                <motion.a
                  key={item.name}
                  href={item.href}
                  className={`font-medium transition-colors duration-200 hover:text-blue-500 ${
                    isScrolled ? 'text-gray-700' : 'text-white/90'
                  }`}
                  whileHover={{ y: -2 }}
                  transition={{ duration: 0.2 }}
                >
                  {item.name}
                </motion.a>
              ))}
            </div>

            {/* Desktop Buttons */}
            <div className="hidden lg:flex items-center space-x-4">
              <motion.button
                className={`font-medium transition-colors duration-200 ${
                  isScrolled ? 'text-gray-700 hover:text-blue-600' : 'text-white/90 hover:text-white'
                }`}
                whileHover={{ y: -2 }}
                transition={{ duration: 0.2 }}
              >
                Login
              </motion.button>
              <motion.button
                className="bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white font-medium px-6 py-2 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl"
                whileHover={{ scale: 1.05, y: -2 }}
                whileTap={{ scale: 0.95 }}
                transition={{ duration: 0.2 }}
              >
                Start Free
              </motion.button>
            </div>

            {/* Mobile Hamburger Button */}
            <motion.button
              className="lg:hidden hamburger-button p-2 rounded-lg transition-colors duration-200"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              whileTap={{ scale: 0.95 }}
              whileHover={{ 
                backgroundColor: isScrolled ? 'rgba(59, 130, 246, 0.1)' : 'rgba(255, 255, 255, 0.1)' 
              }}
            >
              <AnimatePresence mode="wait">
                {isMobileMenuOpen ? (
                  <motion.div
                    key="close"
                    initial={{ rotate: -90, opacity: 0 }}
                    animate={{ rotate: 0, opacity: 1 }}
                    exit={{ rotate: 90, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <X className={`w-6 h-6 ${isScrolled ? 'text-gray-700' : 'text-white'}`} />
                  </motion.div>
                ) : (
                  <motion.div
                    key="menu"
                    initial={{ rotate: 90, opacity: 0 }}
                    animate={{ rotate: 0, opacity: 1 }}
                    exit={{ rotate: -90, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <Menu className={`w-6 h-6 ${isScrolled ? 'text-gray-700' : 'text-white'}`} />
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.button>
          </div>
        </div>
      </motion.nav>

      {/* Mobile Menu Overlay */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
          />
        )}
      </AnimatePresence>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className="mobile-menu fixed top-0 right-0 h-full w-80 bg-white shadow-2xl z-50 lg:hidden"
          >
            <div className="flex flex-col h-full">
              {/* Mobile Menu Header */}
              <div className="flex items-center justify-between p-6 border-b border-gray-200">
                                       <div className="flex items-center space-x-2">
                         <div className="w-8 h-8 text-blue-600 flex items-center justify-center">
                           <div className="w-6 h-6 bg-gradient-to-br from-blue-400 to-cyan-400 rounded transform rotate-45"></div>
                         </div>
                         <span className="text-xl font-bold text-gray-900">PlanCast</span>
                       </div>
                <motion.button
                  onClick={() => setIsMobileMenuOpen(false)}
                  whileTap={{ scale: 0.95 }}
                  className="p-2 rounded-lg hover:bg-gray-100 transition-colors duration-200"
                >
                  <X className="w-6 h-6 text-gray-700" />
                </motion.button>
              </div>

              {/* Mobile Menu Items */}
              <div className="flex-1 p-6">
                <div className="space-y-6">
                  {menuItems.map((item, index) => (
                    <motion.a
                      key={item.name}
                      href={item.href}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.3, delay: index * 0.1 }}
                      className="block text-lg font-medium text-gray-700 hover:text-blue-600 transition-colors duration-200"
                      onClick={() => setIsMobileMenuOpen(false)}
                    >
                      {item.name}
                    </motion.a>
                  ))}
                </div>
              </div>

              {/* Mobile Menu Footer */}
              <div className="p-6 border-t border-gray-200 space-y-4">
                <motion.button
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: 0.4 }}
                  className="w-full text-left text-lg font-medium text-gray-700 hover:text-blue-600 transition-colors duration-200"
                >
                  Login
                </motion.button>
                <motion.button
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: 0.5 }}
                  className="w-full bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white font-medium py-3 px-6 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl"
                  whileTap={{ scale: 0.95 }}
                >
                  Start Free
                </motion.button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};

export default Navbar;
