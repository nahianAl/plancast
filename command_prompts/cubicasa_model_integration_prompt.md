# Prompt for CubiCasa Model Integration

## Context
I'm working on PlanCast, an AI-powered web application that converts 2D architectural floor plans into 3D models. The application has a complete pipeline but is currently using a placeholder model instead of the real CubiCasa5K model for floor plan analysis. This is causing all floor plans to generate identical 3D models, which is a critical bug.

## Current Situation
1. **The Problem**: The `services/cubicasa_service.py` file contains a `PlaceholderModel` that returns hardcoded mock data for every floor plan, resulting in identical 3D outputs regardless of input.

2. **What We Have**:
   - A complete working pipeline (file processing → AI analysis → coordinate scaling → 3D generation → export)
   - Access to the real CubiCasa5K model file (`.pkl` file on Google Drive, accessible by the backend)
   - A production deployment on Railway with PostgreSQL database
   - A frontend deployed on Vercel at getplancast.com

3. **What We Need**:
   - The actual CubiCasa5K model architecture implementation in PyTorch
   - Proper model loading from the pickle file
   - Correct preprocessing and postprocessing logic
   - Integration with the existing pipeline

## Your Task
I need help implementing the real CubiCasa5K model architecture and integrating it into our pipeline. Specifically:

### 1. Model Architecture
Please provide the complete CubiCasa5K model class implementation in PyTorch. The model should:
- Match the exact architecture used to train the saved weights
- Include all layers, dimensions, and configurations
- Have a proper forward() method that outputs the expected segmentation masks

### 2. Model Outputs
Please explain what the model outputs:
- What is the exact output format? (e.g., segmentation masks, heatmaps)
- How many output channels/classes are there?
- What does each output represent? (rooms, walls, junctions, etc.)
- What are the output dimensions relative to input?

### 3. Preprocessing Requirements
Please specify the exact preprocessing needed:
- Input image size (512x512?)
- Normalization values (mean, std)
- Color format (RGB or BGR?)
- Any other transformations

### 4. Postprocessing Logic
Please provide code or guidance for:
- Converting room segmentation masks to bounding boxes with room labels
- Extracting wall coordinates/polylines from wall segmentation or junction maps
- Calculating confidence scores for detected elements
- Handling the model outputs to match our expected format:
  ```python
  CubiCasaOutput(
      wall_coordinates: List[Tuple[int, int]],  # Wall polyline points
      room_bounding_boxes: Dict[str, Dict[str, int]],  # {"room_name": {"min_x", "max_x", "min_y", "max_y"}}
      image_dimensions: Tuple[int, int],
      confidence_scores: Dict[str, float],
      processing_time: float
  )
  ```

### 5. Model Loading
The pickle file structure and how to properly load it:
- Is it just state_dict or does it contain the full model?
- Any specific loading parameters needed?
- How to handle PyTorch version compatibility?

## Current Code Structure
The key file that needs updating is `services/cubicasa_service.py`. It currently has:
- A `PlaceholderModel` class (needs to be replaced with real architecture)
- Mock functions for `_extract_wall_coordinates` and `_extract_room_bounding_boxes` (need real implementations)
- Model loading logic that falls back to placeholder (needs to load real model)

## Additional Context Files
- `@plan.md` - Contains the complete technical plan and current project status
- `@cubicasa_integration.md` - Contains the TODO list and tracking for this integration task
- `@product_brief.md` - Contains the product overview and business context

## Expected Outcome
After implementing the real CubiCasa5K model:
1. Different floor plans should produce unique, accurate 3D models
2. Rooms should be correctly detected and labeled
3. Walls should be accurately positioned
4. The system should work with the existing pipeline without breaking other components

## Important Notes
- The application is in production, so the solution needs to be robust
- We're using PyTorch (compatibility with both 1.x and 2.x would be ideal)
- The model file is accessible via Google Drive URL in the Railway deployment
- The rest of the pipeline (coordinate scaling, 3D generation, export) is working correctly

Please provide the complete model architecture implementation and integration guidance based on your knowledge of CubiCasa5K or similar floor plan analysis models.
