'use client';

import { motion } from 'framer-motion';
import { 
  Upload, 
  Eye, 
  Download, 
  ArrowRight, 
  Zap
} from 'lucide-react';
import { useState } from 'react';
import Navbar from '@/components/common/Navbar';

export default function LandingPage() {
  const [email, setEmail] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Handle email submission
    console.log('Email submitted:', email);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      <Navbar />
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        {/* Background Elements */}
        <div className="absolute inset-0">
          <div className="absolute top-0 left-0 w-72 h-72 bg-blue-500/20 rounded-full blur-3xl animate-pulse"></div>
          <div className="absolute top-0 right-0 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse delay-1000"></div>
          <div className="absolute bottom-0 left-1/2 w-80 h-80 bg-cyan-500/20 rounded-full blur-3xl animate-pulse delay-2000"></div>
        </div>

        <div className="relative container mx-auto px-4 pt-32 pb-20 lg:pt-40 lg:pb-32">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left Content */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
              className="text-center lg:text-left"
            >
              <motion.h1 
                className="text-4xl md:text-6xl lg:text-7xl font-bold text-white mb-6 leading-tight"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.2 }}
              >
                Transform Floor Plans into{' '}
                <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                  3D Models
                </span>{' '}
                in Minutes
              </motion.h1>
              
              <motion.p 
                className="text-xl md:text-2xl text-gray-300 mb-8 max-w-2xl mx-auto lg:mx-0"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.4 }}
              >
                AI-powered conversion directly in your browser. No downloads, no complexity.
              </motion.p>

              <motion.div 
                className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 0.6 }}
              >
                <button className="bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white font-semibold py-4 px-8 rounded-xl text-lg transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-xl">
                  Start Free Trial
                  <ArrowRight className="inline ml-2 h-5 w-5" />
                </button>
                <button className="border border-gray-600 hover:border-gray-500 text-white font-semibold py-4 px-8 rounded-xl text-lg transition-all duration-300 backdrop-blur-sm bg-white/5">
                  Watch Demo
                </button>
              </motion.div>
            </motion.div>

            {/* Right - 3D Mockup */}
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, delay: 0.4 }}
              className="relative"
            >
              <div className="relative w-full h-96 lg:h-[500px] bg-gradient-to-br from-blue-500/20 to-purple-500/20 rounded-2xl backdrop-blur-sm border border-white/10 shadow-2xl">
                {/* Floating 3D Elements */}
                <motion.div
                  animate={{ 
                    y: [0, -20, 0],
                    rotateY: [0, 180, 360]
                  }}
                  transition={{ 
                    duration: 6,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                  className="absolute top-1/4 left-1/4 w-16 h-16 bg-gradient-to-br from-blue-400 to-cyan-400 rounded-lg shadow-lg"
                />
                <motion.div
                  animate={{ 
                    y: [0, 20, 0],
                    rotateX: [0, 180, 360]
                  }}
                  transition={{ 
                    duration: 8,
                    repeat: Infinity,
                    ease: "easeInOut",
                    delay: 1
                  }}
                  className="absolute top-1/2 right-1/4 w-12 h-12 bg-gradient-to-br from-purple-400 to-pink-400 rounded-lg shadow-lg"
                />
                <motion.div
                  animate={{ 
                    y: [0, -15, 0],
                    rotateZ: [0, 180, 360]
                  }}
                  transition={{ 
                    duration: 7,
                    repeat: Infinity,
                    ease: "easeInOut",
                    delay: 2
                  }}
                  className="absolute bottom-1/4 left-1/3 w-10 h-10 bg-gradient-to-br from-cyan-400 to-blue-400 rounded-lg shadow-lg"
                />
                
                                 {/* Center 3D Icon */}
                 <motion.div
                   animate={{
                     rotateY: [0, 360],
                     rotateX: [0, 360]
                   }}
                   transition={{
                     duration: 20,
                     repeat: Infinity,
                     ease: "linear"
                   }}
                   className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2"
                 >
                   <div className="w-24 h-24 text-white/80 flex items-center justify-center">
                     <div className="w-16 h-16 bg-gradient-to-br from-blue-400 to-cyan-400 rounded-lg shadow-lg transform rotate-45"></div>
                   </div>
                 </motion.div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Feature Grid */}
      <section id="features" className="py-20 px-4">
        <div className="container mx-auto">
          <motion.div 
            className="text-center mb-16"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl md:text-5xl font-bold text-white mb-6">
              Everything You Need to{' '}
              <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                Succeed
              </span>
            </h2>
            <p className="text-xl text-gray-300 max-w-3xl mx-auto">
              Professional-grade 3D conversion with enterprise-level features
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: Upload,
                title: "Upload & Convert",
                description: "Drag and drop floor plans, AI processes in seconds",
                gradient: "from-blue-500 to-cyan-500"
              },
              {
                icon: Eye,
                title: "Interactive 3D Preview",
                description: "View and manipulate models in your browser",
                gradient: "from-purple-500 to-pink-500"
              },
              {
                icon: Download,
                title: "Export Any Format",
                description: "Download as GLB, OBJ, SKP, STL, FBX, or DWG",
                gradient: "from-green-500 to-emerald-500"
              }
            ].map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: index * 0.2 }}
                viewport={{ once: true }}
                className="group"
              >
                <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-8 h-full transition-all duration-300 hover:bg-white/10 hover:border-white/20 hover:transform hover:scale-105">
                  <div className={`w-16 h-16 bg-gradient-to-r ${feature.gradient} rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300`}>
                    <feature.icon className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-4">{feature.title}</h3>
                  <p className="text-gray-300 leading-relaxed">{feature.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="pricing" className="py-20 px-4 bg-gradient-to-r from-slate-800/50 to-blue-900/50">
        <div className="container mx-auto">
          <motion.div 
            className="text-center mb-16"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl md:text-5xl font-bold text-white mb-6">
              How It{' '}
              <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                Works
              </span>
            </h2>
            <p className="text-xl text-gray-300 max-w-3xl mx-auto">
              Three simple steps to transform your floor plans into stunning 3D models
            </p>
          </motion.div>

          <div className="relative">
            {/* Connecting Lines */}
            <div className="hidden md:block absolute top-1/2 left-1/4 w-1/2 h-0.5 bg-gradient-to-r from-blue-500 to-purple-500 transform -translate-y-1/2"></div>
            
            <div className="grid md:grid-cols-3 gap-8 relative">
              {[
                {
                  step: "01",
                  title: "Upload your floor plan",
                  description: "JPG, PNG, or PDF",
                  icon: Upload
                },
                {
                  step: "02",
                  title: "AI analyzes and creates 3D model",
                  description: "Advanced neural networks process your file",
                  icon: Zap
                },
                {
                  step: "03",
                  title: "Preview and export",
                  description: "Your preferred format",
                  icon: Download
                }
              ].map((step, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 30 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.8, delay: index * 0.2 }}
                  viewport={{ once: true }}
                  className="text-center relative"
                >
                  <div className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-8 hover:bg-white/10 transition-all duration-300">
                    <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center mx-auto mb-6 text-2xl font-bold text-white">
                      {step.step}
                    </div>
                    <div className="w-16 h-16 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-xl flex items-center justify-center mx-auto mb-6">
                      <step.icon className="w-8 h-8 text-white" />
                    </div>
                    <h3 className="text-xl font-bold text-white mb-4">{step.title}</h3>
                    <p className="text-gray-300">{step.description}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section id="about" className="py-20 px-4">
        <div className="container mx-auto">
          <motion.div 
            className="text-center max-w-4xl mx-auto"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl md:text-5xl font-bold text-white mb-6">
              Ready to revolutionize your{' '}
              <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                workflow?
              </span>
            </h2>
            <p className="text-xl text-gray-300 mb-8">
              Join thousands of architects, designers, and professionals who trust PlanCast
            </p>

            <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-4 max-w-md mx-auto">
              <input
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="flex-1 px-6 py-4 bg-white/5 border border-white/10 rounded-xl text-white placeholder-gray-400 backdrop-blur-sm focus:outline-none focus:border-blue-500 transition-all duration-300"
                required
              />
              <button
                type="submit"
                className="bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white font-semibold py-4 px-8 rounded-xl transition-all duration-300 transform hover:scale-105 shadow-lg hover:shadow-xl"
              >
                Start Free Trial
              </button>
            </form>
            
            <p className="text-gray-400 mt-4 text-sm">
              No credit card required • Free 14-day trial
            </p>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer id="contact" className="py-12 px-4 border-t border-white/10">
        <div className="container mx-auto text-center">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <div className="h-6 w-6 text-blue-400 flex items-center justify-center">
              <div className="w-4 h-4 bg-gradient-to-br from-blue-400 to-cyan-400 rounded transform rotate-45"></div>
            </div>
            <span className="text-xl font-bold text-white">PlanCast</span>
          </div>
          <p className="text-gray-400">
            © 2024 PlanCast. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
