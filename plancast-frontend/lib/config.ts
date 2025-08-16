export const config = {
  // API Configuration
  api: {
    baseUrl: process.env.NEXT_PUBLIC_API_URL || 'https://plancast-api.railway.app',
    timeout: 30000, // 30 seconds
    retryAttempts: 3,
    retryDelay: 1000, // 1 second
  },

  // File Upload Configuration
  upload: {
    maxFileSize: 50 * 1024 * 1024, // 50MB (matching backend)
    supportedFormats: ['image/jpeg', 'image/png', 'application/pdf'] as const,
    supportedExtensions: ['.jpg', '.jpeg', '.png', '.pdf'] as const,
    maxFiles: 1, // Single file upload
  },

  // Export Formats (matching backend mesh_exporter.py)
  exportFormats: {
    GLB: 'glb', // Web-optimized, primary format
    OBJ: 'obj', // Universal 3D format
    SKP: 'skp', // SketchUp format
    STL: 'stl', // 3D printing format
    FBX: 'fbx', // Animation format
    DWG: 'dwg', // CAD format (future)
  } as const,

  // Job Status Configuration
  job: {
    statusPollingInterval: 2000, // 2 seconds
    maxPollingAttempts: 150, // 5 minutes max
    progressSteps: {
      UPLOAD: 10,
      AI_ANALYSIS: 25,
      COORDINATE_SCALING: 40,
      ROOM_GENERATION: 55,
      WALL_GENERATION: 70,
      BUILDING_ASSEMBLY: 80,
      EXPORT: 90,
      COMPLETE: 100,
    },
  },

  // Error Messages
  errors: {
    fileTooLarge: 'File size exceeds 50MB limit',
    unsupportedFormat: 'Only JPG, PNG, and PDF files are supported',
    uploadFailed: 'File upload failed. Please try again.',
    processingFailed: 'Processing failed. Please check your file and try again.',
    networkError: 'Network error. Please check your connection.',
    serverError: 'Server error. Please try again later.',
  },
} as const;

// Type exports
export type SupportedFormat = typeof config.upload.supportedFormats[number];
export type SupportedExtension = typeof config.upload.supportedExtensions[number];
export type ExportFormat = typeof config.exportFormats[keyof typeof config.exportFormats];
export type JobProgressStep = keyof typeof config.job.progressSteps;
