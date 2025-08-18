# CubiCasa Model Integration Plan

## 📋 TODO List

### Phase 1: Model Architecture Implementation
- [ ] Obtain and review the real CubiCasa5K architecture specification
- [ ] Create the actual CubiCasa5K model class in PyTorch
- [ ] Define all layers, dimensions, and configurations matching the original architecture
- [ ] Implement the forward pass method with correct inference flow
- [ ] Remove the PlaceholderModel class entirely

### Phase 2: Model Loading & Compatibility
- [ ] Update the model URL to point to the new Google Drive location
- [ ] Fix PyTorch compatibility issues for loading the pickle file
- [ ] Implement proper state dict loading from the pickle file to the model
- [ ] Handle different PyTorch versions (1.x vs 2.x) gracefully
- [ ] Add comprehensive error handling for model loading failures
- [ ] Verify model loads successfully on both local and Railway environments

### Phase 3: Input Preprocessing
- [ ] Determine exact input requirements (size, normalization, format)
- [ ] Implement proper image resizing (likely 512x512)
- [ ] Add correct normalization (mean, std values)
- [ ] Ensure RGB/BGR format matches training
- [ ] Handle different input image formats (JPG, PNG, PDF)

### Phase 4: Model Inference & Output Processing
- [ ] Understand the exact output format of the model
- [ ] Implement extraction of room segmentation masks
- [ ] Implement extraction of wall segmentation masks
- [ ] Process junction/corner heatmaps if available
- [ ] Convert segmentation masks to room bounding boxes
- [ ] Convert wall masks/junctions to wall polylines
- [ ] Extract confidence scores from model outputs

### Phase 5: Post-Processing Integration
- [ ] Replace mock `_extract_wall_coordinates` with real implementation
- [ ] Replace mock `_extract_room_bounding_boxes` with real implementation
- [ ] Implement proper `_calculate_confidence_scores` based on model outputs
- [ ] Ensure output format matches the existing pipeline expectations
- [ ] Add validation for extracted rooms and walls

### Phase 6: Testing & Validation
- [ ] Test with multiple different floor plan images
- [ ] Verify each floor plan produces unique 3D models
- [ ] Validate room detection accuracy
- [ ] Validate wall detection accuracy
- [ ] Check performance and processing times
- [ ] Test on both local and Railway deployments

### Phase 7: Cleanup & Documentation
- [ ] Remove all placeholder and mock generation code
- [ ] Remove unnecessary TODO comments
- [ ] Update code documentation to reflect real model usage
- [ ] Document any specific requirements or limitations
- [ ] Create user documentation for model requirements

---

## 📝 Change Log

### [Date: TBD] - Initial Planning
- Created this tracking document to manage CubiCasa integration
- Identified the core issue: placeholder model returning identical outputs
- Confirmed access to real model file on Google Drive
- Confirmed knowledge of real CubiCasa5K architecture location
- Established phased approach for integration

### Key Information Gathered:
- **Current Status**: Using PlaceholderModel that returns hardcoded mock data
- **Model File**: Available on user's Google Drive, accessible by Railway backend
- **Architecture**: User knows location of real CubiCasa5K architecture
- **Problem**: Different floor plans produce identical 3D models due to placeholder

### Next Steps:
1. Await architecture details from user
2. Await Google Drive model URL
3. Begin Phase 1 implementation once information is provided

---

## 🔍 Technical Notes

### Current Placeholder Behavior
- Returns same mock room layout for all inputs
- Hardcoded 2 rooms: kitchen and living_room
- Static wall coordinates regardless of input
- No actual image analysis performed

### Expected Real Model Behavior
- Analyzes floor plan images using deep learning
- Detects variable number of rooms based on input
- Identifies room types (bedroom, bathroom, kitchen, etc.)
- Extracts accurate wall boundaries
- Provides confidence scores for detections

### Integration Challenges to Address
1. PyTorch version compatibility (1.x vs 2.x)
2. Model file format (pickle compatibility)
3. Unknown exact input/output specifications
4. Post-processing logic needs complete rewrite
5. Ensuring backward compatibility with existing pipeline

---

## 📊 Success Criteria

- [ ] Different floor plans produce distinctly different 3D models
- [ ] Room detection matches visible rooms in floor plans
- [ ] Wall geometry accurately represents floor plan walls
- [ ] Processing time remains reasonable (<5 seconds per image)
- [ ] No regression in other pipeline components
- [ ] Works in both development and production environments

---

*This document will be updated as we progress through the integration.*
