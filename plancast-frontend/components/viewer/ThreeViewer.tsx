'use client';

import { Suspense, useRef, useState, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Grid, Environment, Html } from '@react-three/drei';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import type { GLTF } from 'three/addons/loaders/GLTFLoader.js';
import { Loader2, AlertCircle, Eye, EyeOff } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { Mesh } from 'three';

interface ThreeViewerProps {
  jobId: string;
  onModelLoad?: (model: GLTF) => void;
  onError?: (error: string) => void;
}

interface ModelViewerProps {
  url: string;
  onLoad: (model: GLTF) => void;
  onError: (error: string) => void;
}

// Model loading component
function ModelViewer({ url, onLoad, onError }: ModelViewerProps) {
  const meshRef = useRef<Mesh>(null);
  const [error, setError] = useState<string | null>(null);
  const [gltf, setGltf] = useState<GLTF | null>(null);

  useEffect(() => {
    const loadModel = async () => {
      try {
        const loader = new GLTFLoader();
        const model = await loader.loadAsync(url);
        setGltf(model);
        onLoad(model);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load model';
        setError(errorMessage);
        onError(errorMessage);
      }
    };

    loadModel();
  }, [url, onLoad, onError]);

  useFrame(() => {
    if (meshRef.current) {
      // Optional: Add subtle rotation animation
      // meshRef.current.rotation.y += 0.001;
    }
  });

  if (error) {
    return (
      <Html center>
        <div className="text-center p-4 bg-red-50 border border-red-200 rounded-lg">
          <AlertCircle className="w-8 h-8 text-red-500 mx-auto mb-2" />
          <p className="text-red-700 font-medium">Model Load Error</p>
          <p className="text-red-600 text-sm">{error}</p>
        </div>
      </Html>
    );
  }

  if (!gltf) {
    return <LoadingSpinner />;
  }

  return (
    <primitive 
      object={gltf.scene} 
      ref={meshRef}
      scale={[1, 1, 1]}
      position={[0, 0, 0]}
    />
  );
}

// Loading component
function LoadingSpinner() {
  return (
    <Html center>
      <div className="text-center p-6 bg-white/80 backdrop-blur-sm rounded-lg shadow-lg">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin mx-auto mb-3" />
        <p className="text-gray-700 font-medium">Loading 3D Model...</p>
        <p className="text-gray-500 text-sm">This may take a few moments</p>
      </div>
    </Html>
  );
}

// Camera controls component
function CameraControls() {
  const [showGrid, setShowGrid] = useState(true);
  const [showEnvironment, setShowEnvironment] = useState(true);

  return (
    <div className="absolute top-4 right-4 z-10 space-y-2">
      <Card className="w-64">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">View Controls</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowGrid(!showGrid)}
            className="w-full justify-start"
          >
            {showGrid ? <Eye className="w-4 h-4 mr-2" /> : <EyeOff className="w-4 h-4 mr-2" />}
            {showGrid ? 'Hide' : 'Show'} Grid
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowEnvironment(!showEnvironment)}
            className="w-full justify-start"
          >
            {showEnvironment ? <Eye className="w-4 h-4 mr-2" /> : <EyeOff className="w-4 h-4 mr-2" />}
            {showEnvironment ? 'Hide' : 'Show'} Environment
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

// Main ThreeViewer component
export default function ThreeViewer({ jobId, onModelLoad, onError }: ThreeViewerProps) {
  const [modelUrl, setModelUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    // Generate the GLB model URL from the backend
    const generateModelUrl = async () => {
      try {
        setIsLoading(true);
        setLoadError(null);
        
        // For now, we'll construct the URL based on the job ID
        // In a real implementation, you might get this from the job status
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'https://plancast-api.railway.app';
        const url = `${baseUrl}/download/${jobId}/glb`;
        
        setModelUrl(url);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Failed to generate model URL';
        setLoadError(errorMessage);
        onError?.(errorMessage);
      } finally {
        setIsLoading(false);
      }
    };

    generateModelUrl();
  }, [jobId, onError]);

  const handleModelLoad = (model: GLTF) => {
    onModelLoad?.(model);
  };

  const handleModelError = (error: string) => {
    setLoadError(error);
    onError?.(error);
  };

  if (isLoading) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Preparing 3D viewer...</p>
        </div>
      </div>
    );
  }

  if (loadError) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-50">
        <div className="text-center p-6 bg-red-50 border border-red-200 rounded-lg">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <p className="text-red-700 font-medium mb-2">Failed to Load Model</p>
          <p className="text-red-600 text-sm">{loadError}</p>
        </div>
      </div>
    );
  }

  if (!modelUrl) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-50">
        <div className="text-center p-6 bg-yellow-50 border border-yellow-200 rounded-lg">
          <AlertCircle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
          <p className="text-yellow-700 font-medium">No Model URL</p>
          <p className="text-yellow-600 text-sm">Unable to generate model URL</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative w-full h-full">
      <Canvas
        camera={{ 
          position: [10, 10, 10], 
          fov: 50,
          near: 0.1,
          far: 1000
        }}
        gl={{ 
          antialias: true, 
          alpha: true,
          preserveDrawingBuffer: true
        }}
        shadows
      >
        {/* Lighting */}
        <ambientLight intensity={0.4} />
        <directionalLight
          position={[10, 10, 5]}
          intensity={1}
          castShadow
          shadow-mapSize-width={2048}
          shadow-mapSize-height={2048}
        />
        <pointLight position={[-10, -10, -10]} intensity={0.5} />

        {/* Environment */}
        <Environment preset="apartment" />

        {/* Grid */}
        <Grid 
          args={[20, 20]} 
          cellSize={1} 
          cellThickness={0.5} 
          cellColor="#6b7280" 
          sectionSize={5} 
          sectionThickness={1} 
          sectionColor="#9ca3af" 
          fadeDistance={25} 
          fadeStrength={1} 
          followCamera={false} 
          infiniteGrid={true} 
        />

        {/* Model */}
        <Suspense fallback={<LoadingSpinner />}>
          <ModelViewer
            url={modelUrl}
            onLoad={handleModelLoad}
            onError={handleModelError}
          />
        </Suspense>

        {/* Camera Controls */}
        <OrbitControls
          enablePan={true}
          enableZoom={true}
          enableRotate={true}
          minDistance={2}
          maxDistance={50}
          maxPolarAngle={Math.PI}
          minPolarAngle={0}
        />
      </Canvas>

      {/* View Controls */}
      <CameraControls />

      {/* Instructions */}
      <div className="absolute bottom-4 left-4 z-10">
        <Card className="w-64">
          <CardContent className="pt-4">
            <p className="text-xs text-gray-600">
              <strong>Controls:</strong><br />
              • Left click + drag: Rotate<br />
              • Right click + drag: Pan<br />
              • Scroll: Zoom<br />
              • Double click: Reset view
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
