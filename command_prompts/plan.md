## PlanCast Feature Technical Plan — 3D Mesh Generation, Web Preview, Export Pipeline & Complete Frontend Integration

Context
- "PlanCast is an AI-powered web application that automatically converts 2D architectural floor plans (images/PDFs) into accurate 3D models with minimal user input, delivering the entire experience through a seamless web interface with interactive 3D preview capabilities." (from updated product brief)
- Foundation complete: File processing, AI service, coordinate scaling operational. In progress: Interactive 3D preview system, mesh generation, and export pipeline. Target: Complete web-based MVP with full upload-to-export functionality and professional user experience.

Scope
- Implement remaining pipeline stages after coordinate scaling: room mesh generation, wall mesh creation, building assembly, web-optimized preview generation, and multi-format export (GLB/OBJ/SKP//FBX/DWG). Provide web-first orchestration in `core`, browser-optimized preview service, and RESTful/WebSocket interfaces in `api` while maintaining strict harmony with existing services and models.
- **NEW**: Complete frontend application with professional UX/UI, user management, billing integration, and comprehensive Three.js 3D preview system.

## Backend Implementation Status

### Data Layer Updates
- `models/data_structures.py`
  - Add core 3D types:
    - `Vertex3D(x: float, y: float, z: float)`
    - `Face(indices: List[int])`
    - `Room3D(name: str, vertices: List[Vertex3D], faces: List[Face], elevation_feet: float, height_feet: float)`
    - `Wall3D(id: str, vertices: List[Vertex3D], faces: List[Face], height_feet: float, thickness_feet: float)`
    - `Building3D(rooms: List[Room3D], walls: List[Wall3D], units: str, metadata: Dict[str, Any])`
  - Add web-specific types:
    - `WebPreviewData(glb_url: str, thumbnail_url: str, scene_metadata: Dict[str, Any])`
    - `MeshExportResult(files: Dict[str, str], preview_data: WebPreviewData, summary: Dict[str, Any])`
    - `InteractiveSession(session_id: str, building: Building3D, modifications: List[Dict], created_at: datetime)`
  - Extend `ScaledCoordinates` with preview-friendly metadata (camera positions, optimal viewing angles).

### Core Geometry Services
- `services/room_generator.py`
  - Core functions:
    - `generate_room_meshes(scaled_coords: ScaledCoordinates, floor_thickness_feet: float = 0.25, room_height_feet: float = 9.0) -> List[Room3D]`
    - `bbox_to_floor_mesh(room_name: str, bbox_pixels: Dict[str, int], scale_factor: float, height_feet: float) -> Room3D`
    - `triangulate_rectangle(min_x_ft: float, min_y_ft: float, max_x_ft: float, max_y_ft: float) -> Tuple[List[Vertex3D], List[Face]]`
  - Web optimization: Generate LOD (Level of Detail) versions for preview

- `services/wall_generator.py`
  - Core functions:
    - `generate_wall_meshes(scaled_coords: ScaledCoordinates, wall_thickness_feet: float = 0.5, wall_height_feet: float = 9.0) -> List[Wall3D]`
    - `offset_wall_polyline(points_feet: List[Tuple[float, float]], offset_feet: float) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]]]`
    - `build_wall_prisms(left_poly: List[Tuple[float, float]], right_poly: List[Tuple[float, float]], height_feet: float) -> Tuple[List[Vertex3D], List[Face]]`
  - Web optimization: Simplified geometry for browser rendering

### Web Preview Service (NEW)
- `services/web_preview_generator.py`
  - Functions to create:
    - `generate_web_preview(building: Building3D, quality: str = "medium") -> WebPreviewData`
    - `optimize_for_web(building: Building3D, target_poly_count: int = 10000) -> Building3D`
    - `generate_thumbnail(building: Building3D, width: int = 512, height: int = 512) -> bytes`
    - `calculate_camera_positions(building: Building3D) -> Dict[str, List[float]]`
    - `create_glb_stream(building: Building3D, compressed: bool = True) -> bytes`
  - Streaming support for progressive loading in browser

### Export Pipeline
- `services/mesh_exporter.py` ✅ **IMPLEMENTED**
  - Core export functions:
    - `export_building(building: Building3D, formats: List[ExportFormat], out_dir: str = "output/generated_models") -> MeshExportResult` ✅
  - Format-specific helpers:
    - `export_glb(building: Building3D, out_path: str, web_optimized: bool = False) -> str` ✅ **FULLY WORKING**
    - `export_obj(building: Building3D, out_path: str) -> str` ✅ **FULLY WORKING**
    - `export_stl(building: Building3D, out_path: str) -> str` ✅ **FULLY WORKING**
    - `export_fbx(building: Building3D, out_path: str) -> str` ✅ **PLACEHOLDER** (exports OBJ)
    - `export_skp(building: Building3D, out_path: str) -> str` ✅ **HYBRID** (SKP → Collada → OBJ)
    - `export_dwg(building: Building3D, out_path: str) -> str` (FUTURE - for CAD compatibility)
  - Web-first: GLB as primary format for browser preview, others for download
  - **Status**: All 5 core formats supported (3 fully working, 1 hybrid, 1 placeholder)

### Orchestration Layer ✅ **IMPLEMENTED**
- `core/floorplan_processor.py` ✅ **COMPLETE**
  - Main orchestrator with comprehensive pipeline:
    - `process_floorplan(file_content: bytes, filename: str, scale_reference: Optional[Dict], export_formats: List[str], output_dir: str) -> ProcessingJob` ✅
  - **Complete Pipeline**: FileProcessor → CubiCasaService → CoordinateScaler → RoomGenerator → WallGenerator → Building Assembly → MeshExporter ✅
  - **Progress Tracking**: 7-step pipeline with percentage progress (10% → 25% → 40% → 55% → 70% → 80% → 90% → 100%) ✅
  - **Error Handling**: Comprehensive exception handling for each pipeline step ✅
  - **Job Management**: ProcessingJob with status tracking, timing, and results ✅
  - **Utility Methods**: Format validation, file format detection, job status retrieval ✅

### API Layer (Web-First)
- `api/main.py`, `api/endpoints.py`
  - RESTful endpoints:
    - `POST /convert` - Multipart upload (images/PDF) → returns job_id for tracking
    - `GET /preview/{job_id}` - Returns web-optimized GLB and metadata for browser preview
    - `GET /download/{job_id}/{format}` - Download in specific format
    - `GET /health` - Component health and status
  - WebSocket endpoints (NEW):
    - `/ws/preview/{job_id}` - Real-time preview updates during processing
    - `/ws/edit/{session_id}` - Interactive editing session
  - CORS configuration for web app integration

- `api/preview_endpoints.py` (NEW)
  - Browser-specific endpoints:
    - `GET /preview/stream/{job_id}` - Progressive GLB streaming
    - `POST /preview/adjust` - Apply real-time adjustments
    - `GET /preview/thumbnail/{job_id}` - Preview thumbnail

### User Management & Database
- Database schema (PostgreSQL on Railway):
  ```sql
  -- Users and authentication
  users (
    id, email, password_hash, 
    subscription_tier, api_key, 
    created_at, last_login, is_active
  )
  
  -- Project/Job tracking
  projects (
    id, user_id, filename, status,
    input_file_path, output_files_json,
    scale_reference, processing_metadata,
    created_at, completed_at, file_size_mb
  )
  
  -- Usage tracking for billing
  usage_logs (
    id, user_id, project_id, action_type,
    api_endpoint, processing_time, 
    credits_used, created_at
  )
  
  -- Team collaboration (future)
  teams (
    id, name, owner_id, subscription_tier,
    max_members, created_at
  )
  
  team_members (
    id, team_id, user_id, role, 
    permissions, joined_at
  )
  ```

### Validation and Security ✅ **COMPLETE**
- `utils/validators.py` ✅ **PRODUCTION-READY**
  - **File Upload Validation**: Comprehensive security checks, MIME type detection, size limits, malicious file detection
  - **Scale Reference Validation**: Bounds checking, consistency validation, reasonable dimension limits
  - **Export Format Validation**: Supported format filtering, fallback to defaults, duplicate removal
  - **Coordinate Validation**: Bounds checking, data integrity validation, building dimension validation
  - **Building3D Validation**: Mesh integrity checks, vertex/face validation, bounding box consistency
  - **Security Features**: Path traversal prevention, executable signature detection, null byte detection, filename sanitization
  - **Convenience Functions**: Easy-to-use validation functions for all data types
  - **Status**: All validation tests passing (8/8) - production-ready with comprehensive security measures

## Frontend Implementation Plan

### Phase 4 - Complete Frontend Application

#### **4A: Application Architecture**

**Technology Stack:**
- **Framework**: Next.js 14 with App Router (TypeScript)
- **Styling**: Tailwind CSS + shadcn/ui component library
- **State Management**: Zustand for global state, React Query for server state
- **3D Rendering**: Three.js + React Three Fiber + Drei helpers
- **Authentication**: NextAuth.js with JWT tokens
- **File Upload**: react-dropzone with progress tracking
- **Real-time**: Socket.io client for WebSocket connections

**Project Structure:**
```
frontend/
├── app/                          # Next.js App Router
│   ├── (auth)/                   # Authentication routes
│   │   ├── login/page.tsx
│   │   ├── signup/page.tsx
│   │   └── layout.tsx
│   ├── dashboard/                # User dashboard
│   │   ├── page.tsx              # Project overview
│   │   ├── projects/             # Project management
│   │   ├── billing/              # Subscription management
│   │   └── settings/             # User preferences
│   ├── convert/                  # Conversion workflow
│   │   ├── upload/page.tsx       # File upload interface
│   │   ├── preview/[id]/page.tsx # 3D preview and editing
│   │   └── export/[id]/page.tsx  # Export and download
│   ├── globals.css               # Global styles
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
└── public/                       # Static assets
```

#### **4B: Core Components & Features**

**Landing Page & Marketing:**
```typescript
// app/page.tsx - Professional B2B landing page
- Hero section with value proposition
- Interactive demo or video
- Feature showcase with animations
- Pricing tiers with clear CTAs
- Customer testimonials
- Technical specifications
- Footer with company info

// Components needed:
- Hero with animated 3D preview
- Feature cards with icons
- Pricing table with tier comparison
- Testimonial carousel
- FAQ accordion
- Newsletter signup
- Contact forms
```

**Authentication System:**
```typescript
// app/(auth)/login/page.tsx
// app/(auth)/signup/page.tsx
- Clean, professional forms
- Email/password authentication
- Social login options (Google, Microsoft)
- Password reset flow
- Email verification
- Team invitation system

// components/auth/
- LoginForm.tsx
- SignupForm.tsx
- PasswordReset.tsx
- EmailVerification.tsx
- AuthGuard.tsx (route protection)
```

**User Dashboard:**
```typescript
// app/dashboard/page.tsx
- Project overview with thumbnails
- Usage statistics and billing info
- Recent conversions timeline
- Quick upload shortcut
- Team management (future)

// components/dashboard/
- ProjectGrid.tsx (project thumbnails)
- UsageChart.tsx (conversion analytics)
- QuickStats.tsx (usage summary)
- RecentActivity.tsx (conversion history)
- BillingStatus.tsx (subscription info)
```

**File Upload Interface:**
```typescript
// app/convert/upload/page.tsx
- Drag-and-drop zone with visual feedback
- File validation with clear error messages
- Upload progress with cancellation
- Multiple file support
- Preview thumbnails
- Scale reference input form

// components/upload/
- DropZone.tsx (main upload interface)
- FilePreview.tsx (uploaded file display)
- ProgressBar.tsx (upload progress)
- ScaleInput.tsx (dimension input form)
- ValidationErrors.tsx (error display)
```

**3D Viewer & Preview System:**
```typescript
// app/convert/preview/[id]/page.tsx
- Interactive 3D model viewer
- Camera controls (orbit, zoom, pan)
- Model information panel
- Export format selection
- Real-time processing updates
- Mobile-optimized controls

// components/viewer/
- ThreeViewer.tsx (main 3D canvas)
- CameraControls.tsx (navigation controls)
- SceneSettings.tsx (lighting, materials)
- ModelInfo.tsx (dimensions, statistics)
- ExportPanel.tsx (format selection)
- ProcessingStatus.tsx (progress display)
```

#### **4C: Three.js Integration Architecture**

**3D Viewer Component Structure:**
```typescript
// components/viewer/ThreeViewer.tsx
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Environment, Grid } from '@react-three/drei'

interface ThreeViewerProps {
  modelUrl: string;
  onLoadComplete: () => void;
  showGrid?: boolean;
  enableEditing?: boolean;
}

// Core features:
- GLB model loading with progress
- Automatic camera positioning
- Professional lighting setup
- Grid and measurement tools
- Screenshot capture
- Performance optimization for mobile
```

**Scene Setup & Optimization:**
```typescript
// lib/three/SceneManager.ts
- Optimal lighting configuration
- Camera position calculation
- Performance monitoring
- Mobile device detection
- WebGL capability checking
- Memory management

// lib/three/ModelLoader.ts
- Progressive GLB loading
- LOD management
- Texture optimization
- Error handling and fallbacks
- Caching strategy
```

**User Interaction Patterns:**
```typescript
// components/viewer/Controls.tsx
- Mouse/touch orbit controls
- Zoom limits and smooth interpolation
- Double-click to focus
- Keyboard shortcuts
- Mobile gesture support
- Accessibility considerations

// Camera presets:
- Isometric view (default)
- Top-down floor plan view
- Perspective walkthrough
- Custom positions from backend
```

#### **4D: User Experience Flows**

**Onboarding Flow:**
```
1. Landing page → Sign up CTA
2. Account creation with email verification
3. Welcome tour with interactive guide
4. First upload with sample file option
5. 3D preview introduction
6. Export demonstration
7. Dashboard overview
```

**Core Conversion Flow:**
```
1. Dashboard → "New Project" button
2. File upload with drag-and-drop
3. Scale reference input (optional)
4. Processing with real-time progress
5. 3D preview with interaction tutorial
6. Model adjustment tools (future)
7. Export format selection
8. Download with format explanations
```

**Project Management Flow:**
```
1. Dashboard project grid
2. Project details page
3. Re-export with different formats
4. Sharing and collaboration
5. Project organization and search
6. Bulk operations
```

**Billing & Subscription Flow:**
```
1. Usage tracking display
2. Subscription tier comparison
3. Upgrade/downgrade interface
4. Payment method management
5. Billing history
6. Usage alerts and limits
```

#### **4E: Responsive Design Strategy**

**Breakpoint System:**
```css
/* Mobile-first approach */
- Mobile: 320px - 768px (single column, touch-optimized)
- Tablet: 768px - 1024px (adaptive layout)
- Desktop: 1024px+ (full feature set)

/* Key considerations: */
- 3D viewer adapts to screen size
- Touch-friendly controls on mobile
- Simplified navigation on small screens
- Progressive disclosure of features
```

**Mobile Optimizations:**
- Reduced 3D model complexity for mobile
- Touch gesture recognition
- Offline capability for downloaded models
- Battery usage optimization
- Network-aware loading

#### **4F: Performance & Accessibility**

**Performance Targets:**
```
- Initial page load: < 2 seconds
- 3D model load: < 3 seconds
- Route transitions: < 500ms
- 3D interaction response: < 16ms (60fps)
- Mobile performance: Optimized for mid-range devices
```

**Accessibility Features:**
```
- WCAG 2.1 AA compliance
- Keyboard navigation for all features
- Screen reader support
- High contrast mode
- Focus management
- Alternative text for 3D content
- Voice descriptions for model features
```

**Progressive Enhancement:**
```
- Graceful degradation for older browsers
- WebGL fallback options
- Reduced functionality mode
- Clear browser requirement messaging
```

### Phase 5 - Advanced Frontend Features

#### **5A: Interactive Editing Tools**
```typescript
// Future features for model adjustment:
- Room dimension editing
- Wall thickness adjustment
- Material assignment
- Texture application
- Lighting customization
- Annotation system
```

#### **5B: Collaboration Features**
```typescript
// Team collaboration tools:
- Project sharing with permissions
- Real-time collaborative editing
- Comment and annotation system
- Version history and branching
- Team workspace management
```

#### **5C: Advanced Visualization**
```typescript
// Enhanced 3D features:
- Virtual reality (WebXR) support
- Augmented reality preview
- Animated walkthroughs
- 360° panorama generation
- Lighting simulation
- Material library integration
```

## Implementation Phases (Complete)

### Phase 1 - Data Layer & Web Types ✅ **COMPLETED**
- Add 3D data structures ✅
- Add web-specific types (WebPreviewData, InteractiveSession) ✅
- Design browser-friendly coordinate system ✅

### Phase 2 - Core Services ✅ **COMPLETED**
- **2A**: Room/Wall generators with LOD support ✅
- **2B**: Web preview generator with streaming ✅
- **2C**: Export pipeline with web-optimized GLB ✅

### Phase 3 - Web API & Database
- RESTful endpoints for upload/download
- WebSocket support for real-time preview
- User authentication and authorization
- PostgreSQL database integration
- Usage tracking and billing API

### Phase 4 - Frontend Application (NEW)
- **4A**: Next.js application architecture (1 week)
- **4B**: Core components and user flows (2 weeks)
- **4C**: Three.js 3D viewer integration (1 week)
- **4D**: Responsive design and mobile optimization (1 week)
- **4E**: Authentication and user management (1 week)

### Phase 5 - Production Optimization
- Performance monitoring and analytics
- Error tracking and user feedback
- CDN integration for 3D assets
- Caching strategies
- A/B testing framework

### Phase 6 - Advanced Features (Future)
- Interactive editing tools
- Team collaboration features
- Advanced visualization options
- API for third-party integrations
- Enterprise features and SSO

## Development Timeline

### **Week 1-2: Infrastructure Setup**
- Deploy backend to Railway with PostgreSQL
- Set up Vercel frontend deployment
- Configure domain and SSL
- Implement user authentication

### **Week 3-4: Core Application**
- Build landing page and marketing site
- Implement upload and conversion flow
- Create basic 3D viewer
- Add project dashboard

### **Week 5-6: Advanced Features**
- Enhance 3D viewer with full controls
- Add billing and subscription management
- Implement real-time progress updates
- Mobile optimization and testing

### **Week 7-8: Production Polish**
- Performance optimization
- Error handling and edge cases
- User testing and feedback integration
- Analytics and monitoring setup

## Technical Dependencies

### Core Dependencies (existing)
- `shapely` - Geometry operations
- `trimesh` - Mesh manipulation
- `numpy` - Numerical computations

### Web-Specific Dependencies (NEW)
- `pygltflib` or `trimesh` - GLB generation with Draco support
- `pillow` - Thumbnail generation
- `fastapi[websockets]` - Real-time communication
- `aiofiles` - Async file operations
- `python-multipart` - File upload handling

### Frontend Dependencies (NEW)
```json
{
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "typescript": "^5.0.0",
    "@react-three/fiber": "^8.0.0",
    "@react-three/drei": "^9.0.0",
    "three": "^0.157.0",
    "tailwindcss": "^3.0.0",
    "@radix-ui/react-*": "latest",
    "zustand": "^4.0.0",
    "@tanstack/react-query": "^5.0.0",
    "next-auth": "^5.0.0",
    "react-dropzone": "^14.0.0",
    "socket.io-client": "^4.0.0",
    "framer-motion": "^10.0.0"
  }
}
```

### Optional Performance
- `meshio` - Additional format support
- `draco3d` - Geometry compression
- `redis` - Session state management

## Web-Specific Considerations

### Performance Targets
- Initial preview load: < 2 seconds
- Full model load: < 5 seconds
- Real-time preview updates: < 100ms latency
- Maximum file size for web preview: 10MB (compressed)

### Browser Compatibility
- Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- WebGL 2.0 support required
- WebAssembly for Draco decompression
- Progressive enhancement for older browsers

### Security
- File upload validation and sandboxing
- Rate limiting on conversion endpoints
- Session-based access control for exports
- CORS configuration for web app domains
- JWT token authentication
- API key management for enterprise users

### User Experience
- Progress indicators during processing
- Preview available before full export
- Graceful degradation for slow connections
- Mobile-responsive preview controls
- Offline capability for downloaded models
- Clear error messages and recovery options

## Business Integration

### Subscription Management
- Tier-based feature access
- Usage tracking and limits
- Automatic billing integration
- Enterprise team management
- API usage monitoring

### Analytics & Monitoring
- User behavior tracking
- Conversion funnel analysis
- Performance monitoring
- Error tracking and alerting
- A/B testing framework

### Customer Support
- In-app help system
- Video tutorials and documentation
- Support ticket integration
- User feedback collection
- Feature request tracking

## Notes on Harmony with Existing Codebase
- Maintain `utils.logger` patterns with web-specific events
- Extend `ProcessingJob` with preview status and WebSocket notifications
- Keep CPU-only operation for core processing
- Add async patterns for web endpoints only
- Preserve deterministic outputs while adding web optimizations
- **NEW**: Ensure frontend state management aligns with backend job tracking
- **NEW**: Maintain consistent error handling patterns across frontend and backend
- **NEW**: Design API responses for optimal frontend consumption