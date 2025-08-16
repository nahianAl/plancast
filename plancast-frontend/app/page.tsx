'use client';

import Link from 'next/link'
import { 
  Upload, 
  Box, 
  Download, 
  Zap, 
  Shield, 
  Globe,
  ArrowRight,
  CheckCircle
} from 'lucide-react'

const features = [
  {
    icon: Upload,
    title: 'Easy Upload',
    description: 'Drag & drop your floor plans in JPG, PNG, or PDF format. Our AI handles the rest.'
  },
  {
    icon: Zap,
    title: 'AI-Powered Conversion',
    description: 'Advanced machine learning algorithms analyze your floor plan and generate accurate 3D models.'
  },
  {
    icon: Box,
    title: '3D Preview',
    description: 'Interactive 3D viewer lets you explore your model from every angle before export.'
  },
  {
    icon: Download,
    title: 'Multiple Formats',
    description: 'Export in GLB, OBJ, or STL formats for use in any 3D software or game engine.'
  },
  {
    icon: Shield,
    title: 'Secure & Private',
    description: 'Your files are processed securely and automatically deleted after processing.'
  },
  {
    icon: Globe,
    title: 'Cloud-Based',
    description: 'Access your projects from anywhere. No software installation required.'
  }
]

const pricingTiers = [
  {
    name: 'Free',
    price: '$0',
    description: 'Perfect for trying out PlanCast',
    features: [
      '3 conversions per month',
      'Basic 3D models',
      'Standard export formats',
      'Community support'
    ],
    cta: 'Start Free',
    popular: false
  },
  {
    name: 'Pro',
    price: '$29',
    period: '/month',
    description: 'For professionals and small teams',
    features: [
      'Unlimited conversions',
      'High-quality 3D models',
      'All export formats',
      'Priority processing',
      'Email support'
    ],
    cta: 'Start Pro Trial',
    popular: true
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    description: 'For large organizations',
    features: [
      'Everything in Pro',
      'Custom integrations',
      'Dedicated support',
      'SLA guarantees',
      'On-premise options'
    ],
    cta: 'Contact Sales',
    popular: false
  }
]

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-cyan-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 dark:text-white mb-6">
              Transform Floor Plans into
              <span className="block bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
                Stunning 3D Models
              </span>
            </h1>
            <p className="text-xl text-gray-600 dark:text-gray-300 mb-8 max-w-3xl mx-auto">
              Upload your floor plan and watch our AI convert it into a beautiful, interactive 3D model. 
              Perfect for architects, real estate agents, and interior designers.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link 
                href="/convert"
                className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-blue-600 to-cyan-600 text-white font-semibold rounded-xl hover:from-blue-700 hover:to-cyan-700 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-1"
              >
                Start Converting Now
                <ArrowRight className="ml-2 w-5 h-5" />
              </Link>
              <Link 
                href="/demo"
                className="inline-flex items-center px-8 py-4 border-2 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 font-semibold rounded-xl hover:border-blue-500 hover:text-blue-600 dark:hover:border-blue-400 dark:hover:text-blue-400 transition-all duration-200"
              >
                View Demo
              </Link>
            </div>
          </div>
        </div>
        
        {/* Floating 3D elements */}
        <div className="absolute top-20 right-10 w-32 h-32 bg-gradient-to-br from-blue-400/20 to-cyan-400/20 rounded-full blur-3xl"></div>
        <div className="absolute bottom-20 left-10 w-40 h-40 bg-gradient-to-br from-purple-400/20 to-pink-400/20 rounded-full blur-3xl"></div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">
              Why Choose PlanCast?
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
              Our AI-powered platform makes 3D model generation simple, fast, and accurate.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div 
                key={feature.title}
                className="group p-6 bg-gray-50 dark:bg-gray-800 rounded-xl hover:bg-white dark:hover:bg-gray-700 transition-all duration-200 hover:shadow-lg border border-gray-200 dark:border-gray-700"
              >
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-200">
                  <feature.icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600 dark:text-gray-300">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20 bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-slate-800 dark:to-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">
              How It Works
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
              Get your 3D model in just three simple steps
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                1
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Upload Floor Plan
              </h3>
              <p className="text-gray-600 dark:text-gray-300">
                Drag and drop your floor plan image or PDF. We support JPG, PNG, and PDF formats.
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                2
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                AI Processing
              </h3>
              <p className="text-gray-600 dark:text-gray-300">
                Our AI analyzes your floor plan and generates a detailed 3D model with walls, rooms, and dimensions.
              </p>
            </div>
            
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-600 text-white rounded-full flex items-center justify-center text-2xl font-bold mx-auto mb-4">
                3
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Download & Use
              </h3>
              <p className="text-gray-600 dark:text-gray-300">
                Preview your 3D model and download in GLB, OBJ, or STL format for your projects.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="py-20 bg-white dark:bg-gray-900">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">
              Simple, Transparent Pricing
            </h2>
            <p className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
              Choose the plan that fits your needs. No hidden fees, cancel anytime.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {pricingTiers.map((tier) => (
              <div 
                key={tier.name}
                className={`relative p-8 rounded-2xl border-2 transition-all duration-200 hover:shadow-xl ${
                  tier.popular 
                    ? 'border-blue-500 bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20' 
                    : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800'
                }`}
              >
                {tier.popular && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                    <span className="bg-blue-600 text-white px-4 py-2 rounded-full text-sm font-semibold">
                      Most Popular
                    </span>
                  </div>
                )}
                
                <div className="text-center mb-6">
                  <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                    {tier.name}
                  </h3>
                  <div className="flex items-baseline justify-center mb-2">
                    <span className="text-4xl font-bold text-gray-900 dark:text-white">
                      {tier.price}
                    </span>
                    {tier.period && (
                      <span className="text-gray-600 dark:text-gray-300 ml-1">
                        {tier.period}
                      </span>
                    )}
                  </div>
                  <p className="text-gray-600 dark:text-gray-300">
                    {tier.description}
                  </p>
                </div>
                
                <ul className="space-y-3 mb-8">
                  {tier.features.map((feature) => (
                    <li key={feature} className="flex items-center">
                      <CheckCircle className="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
                      <span className="text-gray-700 dark:text-gray-300">{feature}</span>
                    </li>
                  ))}
                </ul>
                
                <Link
                  href={tier.name === 'Enterprise' ? '/contact' : '/convert'}
                  className={`block w-full text-center py-3 px-6 rounded-xl font-semibold transition-all duration-200 ${
                    tier.popular
                      ? 'bg-blue-600 text-white hover:bg-blue-700 shadow-lg hover:shadow-xl'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white hover:bg-gray-200 dark:hover:bg-gray-600'
                  }`}
                >
                  {tier.cta}
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-blue-600 to-cyan-600">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Ready to Transform Your Floor Plans?
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            Join thousands of professionals who trust PlanCast for their 3D modeling needs.
          </p>
          <Link
            href="/convert"
            className="inline-flex items-center px-8 py-4 bg-white text-blue-600 font-semibold rounded-xl hover:bg-gray-100 transition-all duration-200 shadow-lg hover:shadow-xl transform hover:-translate-y-1"
          >
            Start Your First Conversion
            <ArrowRight className="ml-2 w-5 h-5" />
          </Link>
        </div>
      </section>
    </div>
  )
}
