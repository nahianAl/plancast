# PlanCast Product Brief

## 1. Project Overview

**PlanCast** is an AI-powered web application that automatically converts 2D architectural floor plans (images/PDFs) into accurate 3D models with minimal user input. The entire user experience is delivered through a seamless web interface with interactive 3D preview capabilities, transforming hours of manual 3D modeling work into minutes of automated processing.

**Core Value Proposition:** Convert architectural floor plans to professional-grade 3D models entirely within your browser - 10x-100x faster than traditional methods, reducing costs from $500-2000 per project to $49-199/month subscriptions.

**Platform Philosophy:** Complete web-based experience - no downloads, no installations, just upload and export.

**Market Opportunity:** Targeting the $14.5B architecture design market (growing at 16.3% CAGR) with validated $300k+ ARR potential.

## 2. Target Audience

### Primary Users
- **Architects & Architectural Firms** - Need rapid 3D visualization for client presentations
- **Real Estate Developers** - Require 3D models for marketing and planning
- **Interior Designers** - Want quick 3D representations for space planning
- **Construction Professionals** - Need accurate 3D models for project planning

### User Personas
- **Professional Tier** ($99/month) - Established firms with regular 3D modeling needs
- **Enterprise Tier** ($199/month) - Large firms requiring team collaboration and API access
- **Occasional Users** ($149/project) - Smaller firms or individuals with sporadic needs

## 3. Primary Benefits & Features

### Core Benefits
- **100% Web-Based:** No software installation required - works on any device with a browser
- **Speed:** Convert floor plans in minutes vs hours/days of manual work
- **Cost Efficiency:** 10x-100x cost savings compared to traditional 3D modeling
- **Professional Quality:** Enterprise-grade accuracy suitable for client presentations
- **Universal Compatibility:** Multiple export formats (GLB, OBJ, SKP, STL, FBX, DWG)

### Key Features
- **Smart File Processing** - Direct web upload supporting JPG, PNG, and single-page PDF files
- **AI-Powered Conversion** - CubiCasa5K neural network for intelligent floor plan analysis
- **Interactive 3D Preview** - Real-time browser-based 3D model visualization and manipulation
- **Intelligent Scaling** - Smart room detection with user-friendly dimension input
- **Multiple Export Formats** - Professional CAD and 3D modeling format support
- **Web-Based Editing** - Make adjustments directly in the browser before export
- **Future Features** - 360° panoramas, rendered animations, interactive walkthroughs (all web-based)

### Competitive Advantages
- **Pure Web Experience** - No desktop software required unlike most competitors
- **End-to-End Automation** - True automated conversion vs competitors' partial automation
- **Sub-Second Processing** - Optimized performance with 0.01s processing times
- **Interactive Preview** - Full 3D manipulation in browser before download
- **Production-Ready Reliability** - Enterprise-grade error handling and monitoring

## 4. High-Level Tech/Architecture

### Frontend Web Application (Primary User Interface)
- **Framework:** Modern reactive web stack (React/Vue.js/Next.js)
- **3D Visualization:** Three.js for interactive browser-based 3D model preview
- **File Upload:** Drag-and-drop interface with real-time progress tracking
- **3D Editor:** Web-based tools for model adjustment and refinement
- **Export Interface:** Multi-format download with live preview capabilities
- **Responsive Design:** Optimized for desktop, tablet, and mobile browsers

### Backend Architecture (Supporting Web Services)
- **Python-based microservices** with modular, scalable design
- **File Processing Service** - Handles image (JPG/PNG) and PDF uploads with validation
- **CubiCasa5K AI Service** - Neural network for floor plan analysis
- **Coordinate Scaling System** - Converts pixels to real-world measurements
- **3D Mesh Generators** - Creates room and wall geometry
- **Export Pipeline** - Multi-format file generation (GLB/OBJ/SKP/STL/FBX/DWG)
- **Preview Service** - Optimized 3D model streaming for browser visualization

### Core User Flow (Web-Based Journey)
```
Web Upload (Image/PDF) → AI Analysis → Interactive 3D Preview → 
User Adjustments (Optional) → Format Selection → Export/Download
```

### Technical Infrastructure
- **AI Model:** CubiCasa5K neural network for architectural analysis
- **3D Engine:** Three.js for web-based interactive preview
- **Performance:** Sub-second processing with real-time preview updates
- **Scaling:** Cloud-native architecture for concurrent user support
- **Reliability:** Comprehensive error handling with user-friendly feedback

### Development Status
- **Foundation Complete:** File processing, AI service, coordinate scaling operational
- **In Progress:** Interactive 3D preview system and export pipeline
- **Next Phase:** Web-based editing tools and enhanced preview features
- **Target:** Complete web-based MVP with full upload-to-export functionality