# PlanCast Frontend

A modern Next.js 14 application for AI-powered 2D to 3D floor plan conversion.

## 🚀 Features

- **Modern Tech Stack**: Next.js 14 with App Router, TypeScript, and Tailwind CSS
- **Professional UI**: shadcn/ui components with custom brand colors
- **3D Visualization**: Three.js integration for interactive 3D model previews
- **State Management**: Zustand for global state management
- **Authentication**: NextAuth.js for user authentication
- **File Upload**: Drag-and-drop file upload with progress tracking
- **Responsive Design**: Mobile-first responsive design
- **Type Safety**: Full TypeScript support with comprehensive type definitions
- **Stunning Landing Page**: Modern design with animations and interactive elements
- **Navigation System**: Sticky navbar with mobile menu and smooth animations

## 🎨 Brand Colors

- **Primary**: Deep Navy (#1E3A8A)
- **Secondary**: Sky Cyan (#38BDF8)
- **Accent**: Golden Yellow (#FACC15)
- **Background**: Soft White (#F9FAFB)
- **Text**: Charcoal Black (#111827)

## 📁 Project Structure

```
plancast-frontend/
├── app/                          # Next.js App Router
│   ├── (auth)/                   # Authentication routes
│   │   ├── login/page.tsx        # Login page
│   │   ├── signup/page.tsx       # Signup page
│   │   └── layout.tsx            # Auth layout
│   ├── dashboard/                # User dashboard
│   │   ├── projects/             # Project management
│   │   ├── billing/              # Subscription management
│   │   └── settings/             # User preferences
│   ├── convert/                  # Conversion workflow
│   │   ├── upload/               # File upload interface
│   │   ├── preview/[id]/         # 3D preview and editing
│   │   └── export/[id]/          # Export and download
│   ├── globals.css               # Global styles with brand colors
│   ├── layout.tsx                # Root layout
│   └── page.tsx                  # Landing page
├── components/                   # Reusable components
│   ├── ui/                       # shadcn/ui components
│   ├── auth/                     # Authentication components
│   ├── upload/                   # File upload components
│   ├── viewer/                   # 3D viewer components
│   ├── dashboard/                # Dashboard components
│   └── common/                   # Shared components
├── lib/                          # Utilities and configuration
│   ├── api.ts                    # API client configuration
│   ├── auth.ts                   # Authentication helpers
│   ├── utils.ts                  # Utility functions
│   ├── constants.ts              # App constants
│   └── three/                    # Three.js utilities
├── hooks/                        # Custom React hooks
├── stores/                       # Zustand stores
├── types/                        # TypeScript type definitions
├── public/                       # Static assets
├── .github/                      # GitHub Actions workflows
│   └── workflows/
│       └── deploy.yml            # Deployment workflow
├── vercel.json                   # Vercel deployment configuration
├── .env.example                  # Environment variables template
└── README.md                     # This file
```

## 🛠️ Tech Stack

### Core Framework
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework

### UI Components
- **shadcn/ui** - Modern component library
- **Lucide React** - Beautiful icons
- **Framer Motion** - Animation library

### 3D Graphics
- **Three.js** - 3D graphics library
- **React Three Fiber** - React renderer for Three.js
- **React Three Drei** - Useful helpers for R3F

### State Management
- **Zustand** - Lightweight state management
- **React Query** - Server state management

### Authentication
- **NextAuth.js** - Authentication for Next.js

### File Handling
- **React Dropzone** - Drag-and-drop file upload

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd plancast-frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env.local
   ```
   
   Update `.env.local` with your configuration:
   ```env
   NEXT_PUBLIC_API_URL=https://your-railway-api.railway.app
   NEXTAUTH_SECRET=your-super-secret-key-change-this-in-production
   NEXTAUTH_URL=http://localhost:3000
   ```

4. **Start the development server**
   ```bash
   npm run dev
   ```

5. **Open your browser**
   Navigate to [http://localhost:3000](http://localhost:3000)

## 📦 Available Scripts

- `npm run dev` - Start development server with Turbopack
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking
- `npm run deploy` - Deploy to Vercel (production)
- `npm run deploy:preview` - Deploy to Vercel (preview)

## 🚀 Deployment

### Vercel Deployment

This project is configured for automatic deployment to Vercel.

#### Automatic Deployment (Recommended)

1. **Connect to Vercel**
   - Push your code to GitHub
   - Connect your repository to Vercel
   - Set up environment variables in Vercel dashboard

2. **GitHub Actions**
   - The project includes GitHub Actions for automatic deployment
   - Deploys on push to `main` branch
   - Creates preview deployments for pull requests

#### Manual Deployment

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Deploy to production**
   ```bash
   npm run deploy
   ```

3. **Deploy preview**
   ```bash
   npm run deploy:preview
   ```

### Environment Variables

Set these environment variables in your Vercel dashboard:

- `NEXT_PUBLIC_API_URL` - Your backend API URL
- `NEXTAUTH_SECRET` - Secret key for NextAuth.js
- `NEXTAUTH_URL` - Your production URL

### GitHub Secrets

For GitHub Actions deployment, set these secrets:

- `VERCEL_TOKEN` - Your Vercel API token
- `VERCEL_ORG_ID` - Your Vercel organization ID
- `VERCEL_PROJECT_ID` - Your Vercel project ID

## 🎯 Key Features

### Landing Page
- **Hero Section**: Gradient background with animated 3D mockup
- **Feature Grid**: 3-column layout showcasing key features
- **How It Works**: 3-step process with connecting animations
- **CTA Section**: Email capture with call-to-action

### Navigation
- **Sticky Navbar**: Transparent background that turns white on scroll
- **Mobile Menu**: Hamburger menu with slide-in animation
- **Smooth Scrolling**: Custom scrollbar with gradient styling

### Animations
- **Framer Motion**: Smooth entrance animations and hover effects
- **Intersection Observer**: Scroll-triggered animations
- **Hover Effects**: Scale, lift, and color transitions

## 🔧 Configuration

### Vercel Configuration

The `vercel.json` file includes:
- Build settings optimized for Next.js
- Security headers for XSS protection and content type options
- CORS headers for API routes
- Cache control for static assets
- Redirect rules for www to non-www

### GitHub Actions

The `.github/workflows/deploy.yml` includes:
- Type checking and linting before deployment
- Automatic deployment on push to main
- Preview deployments for pull requests
- Build verification

## 🛡️ Security

- **Security Headers**: XSS protection, content type options, frame options
- **CORS Configuration**: Proper CORS headers for API routes
- **Environment Variables**: Secure handling of sensitive data
- **Input Validation**: Comprehensive validation for all inputs

## 📱 Performance

- **Static Asset Caching**: 1-year cache for static files
- **Dynamic Content**: No-cache for HTML and JSON
- **Image Optimization**: Next.js automatic image optimization
- **Code Splitting**: Automatic code splitting by Next.js

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support, email support@plancast.com or create an issue in the repository.
