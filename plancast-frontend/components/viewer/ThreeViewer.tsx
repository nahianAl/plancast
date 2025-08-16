'use client'

import { useRef, useState, useEffect } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import { OrbitControls, Environment, Grid, useGLTF, Html } from '@react-three/drei'
import * as THREE from 'three'

interface ThreeViewerProps {
  modelUrl: string
  onLoadComplete?: () => void
  showGrid?: boolean
  enableEditing?: boolean
}

// Model component that loads the GLB file
function Model({ modelUrl, onLoadComplete }: { modelUrl: string; onLoadComplete?: () => void }) {
  const { scene } = useGLTF(modelUrl)
  const modelRef = useRef<THREE.Group>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (scene) {
      setIsLoading(false)
      onLoadComplete?.()
    }
  }, [scene, onLoadComplete])

  // Auto-rotate the model slightly for demo purposes
  useFrame((state) => {
    if (modelRef.current && !isLoading) {
      modelRef.current.rotation.y += 0.005
    }
  })

  // Center and scale the model
  useEffect(() => {
    if (scene && modelRef.current) {
      const box = new THREE.Box3().setFromObject(scene)
      const center = box.getCenter(new THREE.Vector3())
      const size = box.getSize(new THREE.Vector3())
      
      // Center the model
      scene.position.sub(center)
      
      // Scale to fit in view
      const maxDim = Math.max(size.x, size.y, size.z)
      const scale = 5 / maxDim
      scene.scale.setScalar(scale)
      
      // Position slightly above ground
      scene.position.y = 0
    }
  }, [scene])

  if (isLoading) {
    return (
      <Html center>
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
          <p className="text-sm text-gray-600 dark:text-gray-300">Loading 3D model...</p>
        </div>
      </Html>
    )
  }

  if (error) {
    return (
      <Html center>
        <div className="text-center">
          <p className="text-sm text-red-600 dark:text-red-400">Failed to load model</p>
        </div>
      </Html>
    )
  }

  return (
    <primitive 
      ref={modelRef}
      object={scene} 
      position={[0, 0, 0]}
    />
  )
}

// Camera controls component
function CameraControls() {
  const { camera } = useThree()
  
  useEffect(() => {
    // Set initial camera position
    camera.position.set(10, 10, 10)
    camera.lookAt(0, 0, 0)
  }, [camera])

  return (
    <OrbitControls
      enablePan={true}
      enableZoom={true}
      enableRotate={true}
      minDistance={2}
      maxDistance={50}
      maxPolarAngle={Math.PI / 2}
    />
  )
}

// Main ThreeViewer component
export default function ThreeViewer({ 
  modelUrl, 
  onLoadComplete, 
  showGrid = true,
  enableEditing = false 
}: ThreeViewerProps) {
  const [isModelLoaded, setIsModelLoaded] = useState(false)
  const [hasError, setHasError] = useState(false)

  const handleLoadComplete = () => {
    setIsModelLoaded(true)
    onLoadComplete?.()
  }

  const handleError = (error: string) => {
    setHasError(true)
    console.error('3D model error:', error)
  }

  return (
    <div className="w-full h-full relative">
      <Canvas
        camera={{ position: [10, 10, 10], fov: 50 }}
        shadows
        gl={{ 
          antialias: true, 
          alpha: true,
          powerPreference: "high-performance"
        }}
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
        {showGrid && (
          <Grid
            args={[20, 20]}
            cellSize={1}
            cellThickness={0.5}
            cellColor="#6b7280"
            sectionSize={5}
            sectionThickness={1}
            sectionColor="#374151"
            fadeDistance={25}
            fadeStrength={1}
            followCamera={false}
            infiniteGrid={true}
          />
        )}
        
        {/* 3D Model */}
        <Model 
          modelUrl={modelUrl} 
          onLoadComplete={handleLoadComplete}
        />
        
        {/* Camera Controls */}
        <CameraControls />
      </Canvas>
      
      {/* Loading Overlay */}
      {!isModelLoaded && !hasError && (
        <div className="absolute inset-0 bg-gray-100 dark:bg-gray-900 bg-opacity-75 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600 dark:text-gray-300">Loading 3D model...</p>
          </div>
        </div>
      )}
      
      {/* Error Overlay */}
      {hasError && (
        <div className="absolute inset-0 bg-red-50 dark:bg-red-900/20 flex items-center justify-center">
          <div className="text-center">
            <div className="w-12 h-12 bg-red-100 dark:bg-red-900 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <p className="text-red-600 dark:text-red-400 font-medium mb-2">Failed to load 3D model</p>
            <p className="text-red-500 dark:text-red-300 text-sm">Please try refreshing the page</p>
          </div>
        </div>
      )}
      
      {/* Controls Overlay */}
      {isModelLoaded && (
        <div className="absolute bottom-4 right-4 flex flex-col space-y-2">
          <button
            className="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
            title="Reset camera"
            onClick={() => {
              // Reset camera position
              const canvas = document.querySelector('canvas')
              if (canvas) {
                const event = new Event('resetCamera')
                canvas.dispatchEvent(event)
              }
            }}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
          
          <button
            className="p-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
            title="Toggle grid"
            onClick={() => {
              // Toggle grid visibility
              const grid = document.querySelector('[data-grid]')
              if (grid) {
                grid.style.display = grid.style.display === 'none' ? 'block' : 'none'
              }
            }}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
            </svg>
          </button>
        </div>
      )}
    </div>
  )
}
