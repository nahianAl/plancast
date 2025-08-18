'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { motion } from 'framer-motion';
import { ArrowLeft, ArrowRight, CheckCircle, AlertCircle, Info } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { apiClient } from '@/lib/api/client';

interface RoomSuggestion {
  room_name: string;
  confidence: number;
  bounding_box: {
    min_x: number;
    max_x: number;
    min_y: number;
    max_y: number;
  };
  pixel_dimensions: {
    width: number;
    height: number;
  };
  suggested_dimension: 'width' | 'length';
  is_recommended: boolean;
  highlight_color: string;
  priority: number;
  reason: string;
}

interface RoomAnalysisResponse {
  job_id: string;
  rooms: RoomSuggestion[];
  image_dimensions: [number, number];
  analysis_complete: boolean;
}

export default function RoomSelectionPage() {
  const router = useRouter();
  const params = useParams();
  const jobId = params.jobId as string;

  const [rooms, setRooms] = useState<RoomSuggestion[]>([]);
  const [selectedRoom, setSelectedRoom] = useState<RoomSuggestion | null>(null);
  const [dimension, setDimension] = useState('');
  const [dimensionType, setDimensionType] = useState<'width' | 'length'>('width');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [imageUrl, setImageUrl] = useState<string>('');
  const [validationError, setValidationError] = useState<string | null>(null);
  const [validationWarning, setValidationWarning] = useState<string | null>(null);

  useEffect(() => {
    if (jobId) {
      loadRoomAnalysis();
    }
  }, [jobId]);

  const loadRoomAnalysis = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await apiClient.get<RoomAnalysisResponse>(`/analyze/${jobId}/rooms`);
      setRooms(response.data.rooms);
      
      // Set the first recommended room as default selection
      const recommendedRoom = response.data.rooms.find(room => room.is_recommended);
      if (recommendedRoom) {
        setSelectedRoom(recommendedRoom);
        setDimensionType(recommendedRoom.suggested_dimension);
      }

      // Set image URL for display
      setImageUrl(`/api/jobs/${jobId}/image`); // This endpoint needs to be created

    } catch (err: any) {
      console.error('Failed to load room analysis:', err);
      setError(err.response?.data?.message || 'Failed to load room analysis');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRoomSelect = (room: RoomSuggestion) => {
    setSelectedRoom(room);
    setDimensionType(room.suggested_dimension);
    setDimension(''); // Reset dimension when room changes
    setValidationError(null);
    setValidationWarning(null);
  };

  const handleSubmit = async () => {
    if (!selectedRoom || !dimension) return;

    // Validate dimension
    const validation = validateDimension(dimension);
    if (!validation.isValid) {
      setValidationError(validation.error || 'Invalid dimension');
      return;
    }
    
    setValidationError(null);
    setValidationWarning(validation.warning || null);

    try {
      setIsSubmitting(true);

      // Submit scale input to backend
      await apiClient.post(`/scale/${jobId}`, {
        room_type: selectedRoom.room_name,
        dimension_type: dimensionType,
        real_world_feet: parseFloat(dimension)
      });

      // Navigate to preview page
      router.push(`/convert/preview/${jobId}`);

    } catch (err: any) {
      console.error('Failed to submit scale input:', err);
      setError(err.response?.data?.message || 'Failed to submit scale input');
    } finally {
      setIsSubmitting(false);
    }
  };

  const validateDimension = (value: string): { isValid: boolean; error?: string; warning?: string } => {
    const num = parseFloat(value);
    if (isNaN(num) || num <= 0) {
      return { isValid: false, error: "Please enter a valid positive number" };
    }
    
    // Room-specific validation
    if (selectedRoom) {
      const roomType = selectedRoom.room_name.toLowerCase();
      const roomDimensionLimits = {
        "kitchen": { min: 8, max: 20, typical: 12 },
        "living_room": { min: 12, max: 30, typical: 16 },
        "bedroom": { min: 10, max: 25, typical: 12 },
        "bathroom": { min: 5, max: 15, typical: 8 },
        "dining_room": { min: 10, max: 25, typical: 14 }
      };
      
      // Find matching room type
      const roomKey = Object.keys(roomDimensionLimits).find(key => roomType.includes(key));
      if (roomKey) {
        const limits = roomDimensionLimits[roomKey as keyof typeof roomDimensionLimits];
        
        if (num < limits.min) {
          return { 
            isValid: false, 
            error: `${selectedRoom.room_name} ${dimensionType} too small: ${num} feet. Minimum: ${limits.min} feet` 
          };
        }
        
        if (num > limits.max) {
          return { 
            isValid: false, 
            error: `${selectedRoom.room_name} ${dimensionType} too large: ${num} feet. Maximum: ${limits.max} feet` 
          };
        }
        
        // Warning for unusual dimensions
        if (Math.abs(num - limits.typical) > limits.typical * 0.5) {
          return { 
            isValid: true, 
            warning: `Unusual ${selectedRoom.room_name} ${dimensionType}: ${num} feet (typical: ${limits.typical} feet). Please verify this measurement.` 
          };
        }
      }
    }
    
    return { isValid: true };
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 py-12">
        <div className="container mx-auto px-4 max-w-6xl">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Analyzing your floor plan...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 py-12">
        <div className="container mx-auto px-4 max-w-6xl">
          <Alert className="max-w-md mx-auto">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
          <div className="text-center mt-4">
            <Button onClick={() => router.push('/convert/upload')}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Upload
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 py-12">
      <div className="container mx-auto px-4 max-w-6xl">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-8"
        >
          <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            Select a Room for Scale Reference
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Click on a room in your floor plan and provide its dimensions for accurate 3D model scaling
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Floor Plan with Room Highlighting */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-4"
          >
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Info className="w-5 h-5" />
                  Floor Plan Analysis
                </CardTitle>
                <CardDescription>
                  {rooms.length} rooms detected. Click on a room to select it for scaling.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="relative border rounded-lg overflow-hidden bg-white">
                  {imageUrl && (
                    <img 
                      src={imageUrl} 
                      alt="Floor Plan" 
                      className="w-full h-auto"
                      onError={() => setImageUrl('/placeholder-floorplan.jpg')}
                    />
                  )}
                  
                  {/* Room Highlighting Overlay */}
                  <div className="absolute inset-0">
                    {rooms.map((room) => (
                      <div
                        key={room.room_name}
                        className={`absolute border-2 cursor-pointer transition-all duration-200 ${
                          selectedRoom?.room_name === room.room_name 
                            ? 'border-blue-500 bg-blue-500/20 shadow-lg' 
                            : 'border-gray-300 hover:border-gray-400 hover:bg-gray-100/20'
                        }`}
                        style={{
                          left: `${(room.bounding_box.min_x / 512) * 100}%`,
                          top: `${(room.bounding_box.min_y / 512) * 100}%`,
                          width: `${((room.bounding_box.max_x - room.bounding_box.min_x) / 512) * 100}%`,
                          height: `${((room.bounding_box.max_y - room.bounding_box.min_y) / 512) * 100}%`,
                          borderColor: selectedRoom?.room_name === room.room_name ? room.highlight_color : undefined
                        }}
                        onClick={() => handleRoomSelect(room)}
                      >
                        <div 
                          className="absolute -top-6 left-0 px-2 py-1 rounded text-xs font-medium text-white"
                          style={{ backgroundColor: room.highlight_color }}
                        >
                          {room.room_name}
                          {room.is_recommended && (
                            <CheckCircle className="w-3 h-3 ml-1 inline" />
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Room Selection and Dimension Input */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="space-y-6"
          >
            {selectedRoom ? (
              <>
                {/* Selected Room Info */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <CheckCircle className="w-5 h-5 text-green-600" />
                      Selected Room
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="p-4 bg-blue-50 rounded-lg">
                      <h3 className="font-medium text-blue-900">
                        {selectedRoom.room_name}
                      </h3>
                      <p className="text-blue-700 text-sm mt-1">
                        {selectedRoom.reason}
                      </p>
                      <div className="flex items-center gap-2 mt-2">
                        <Badge variant="secondary">
                          Confidence: {(selectedRoom.confidence * 100).toFixed(0)}%
                        </Badge>
                        {selectedRoom.is_recommended && (
                          <Badge variant="default" className="bg-green-600">
                            Recommended
                          </Badge>
                        )}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Pixel Width:</span>
                        <span className="ml-2 font-medium">{selectedRoom.pixel_dimensions.width}px</span>
                      </div>
                      <div>
                        <span className="text-gray-600">Pixel Height:</span>
                        <span className="ml-2 font-medium">{selectedRoom.pixel_dimensions.height}px</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Dimension Input */}
                <Card>
                  <CardHeader>
                    <CardTitle>Enter Room Dimension</CardTitle>
                    <CardDescription>
                      Provide the real-world measurement for accurate scaling
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <Label htmlFor="dimension-type">Dimension Type</Label>
                      <Select value={dimensionType} onValueChange={(value: 'width' | 'length') => setDimensionType(value)}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="width">Width</SelectItem>
                          <SelectItem value="length">Length</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                                         <div>
                       <Label htmlFor="dimension">Measurement (feet)</Label>
                       <Input
                         id="dimension"
                         type="number"
                         placeholder="12"
                         value={dimension}
                         onChange={(e) => {
                           setDimension(e.target.value);
                           const validation = validateDimension(e.target.value);
                           setValidationError(validation.error || null);
                           setValidationWarning(validation.warning || null);
                         }}
                         className={validationError ? 'border-red-500' : validationWarning ? 'border-yellow-500' : ''}
                       />
                       {validationError && (
                         <p className="text-red-500 text-sm mt-1">
                           {validationError}
                         </p>
                       )}
                       {validationWarning && !validationError && (
                         <p className="text-yellow-600 text-sm mt-1">
                           ⚠️ {validationWarning}
                         </p>
                       )}
                     </div>

                                         <Button 
                       onClick={handleSubmit}
                       disabled={!dimension || !validateDimension(dimension).isValid || isSubmitting}
                       className="w-full"
                     >
                      {isSubmitting ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          Processing...
                        </>
                      ) : (
                        <>
                          Continue to 3D Preview
                          <ArrowRight className="w-4 h-4 ml-2" />
                        </>
                      )}
                    </Button>
                  </CardContent>
                </Card>
              </>
            ) : (
              <Card>
                <CardContent className="p-8 text-center">
                  <Info className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600">
                    Click on a room in the floor plan to select it for scaling
                  </p>
                </CardContent>
              </Card>
            )}
          </motion.div>
        </div>

        {/* Navigation */}
        <div className="text-center mt-8">
          <Button 
            variant="outline" 
            onClick={() => router.push('/convert/upload')}
            className="mr-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Upload
          </Button>
        </div>
      </div>
    </div>
  );
}
