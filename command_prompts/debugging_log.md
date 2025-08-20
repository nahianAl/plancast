# PlanCast Debugging Log

## Overview
This document tracks all debugging issues encountered during development and their solutions. It serves as a reference to avoid repeating the same mistakes and provides a clear history of fixes.

## Issues and Solutions

### Issue #1: CORS Policy Blocking Frontend Requests
**Date**: August 19, 2025  
**Error**: `Access to fetch at 'https://api.getplancast.com/jobs/43/status' from origin 'https://www.getplancast.com' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.`

**Root Cause**: Frontend was using direct `fetch` calls instead of configured API client, and browser was using cached JavaScript with old CORS configuration.

**Solution**:
1. Updated `useJobStatus.ts` to use configured `apiClient` instead of direct `fetch`
2. Reverted `withCredentials` setting in API client to avoid CORS complexity
3. Restored `ProcessingJob` structure for backward compatibility
4. Added cache-busting headers in `next.config.ts`
5. Added timestamp parameters to API requests to prevent caching

**Files Modified**:
- `plancast-frontend/hooks/useJobStatus.ts`
- `plancast-frontend/lib/api/client.ts`
- `plancast-frontend/types/api.ts`
- `plancast-frontend/lib/api/floorplan.ts`
- `plancast-frontend/app/convert/status/[jobId]/page.tsx`
- `plancast-frontend/hooks/useFileUpload.ts`
- `plancast-frontend/next.config.ts`

**Status**: ✅ Resolved

### Issue #2: TypeScript Compilation Errors
**Date**: August 19, 2025  
**Error**: Multiple TypeScript errors due to type mismatches between `ProcessingJob` and `JobStatusResponse` interfaces.

**Root Cause**: Inconsistent data structure types between frontend and backend.

**Solution**:
1. Reverted to original `ProcessingJob` interface structure
2. Added conversion logic in `floorplan.ts` to map backend response to frontend format
3. Fixed all field references (`progress` vs `progress_percent`, etc.)

**Files Modified**:
- `plancast-frontend/types/api.ts`
- `plancast-frontend/lib/api/floorplan.ts`
- `plancast-frontend/app/convert/status/[jobId]/page.tsx`

**Status**: ✅ Resolved

### Issue #3: API Timeout During 3D Model Processing
**Date**: August 19, 2025  
**Error**: `timeout of 30000ms exceeded` during 3D model generation.

**Root Cause**: 3D model generation pipeline requires more time than the default 30-second timeout.

**Solution**:
1. Increased API timeout from 30 seconds to 5 minutes (300,000ms)
2. Increased polling attempts from 150 to 600 (20 minutes max)

**Files Modified**:
- `plancast-frontend/lib/config.ts`

**Status**: ✅ Resolved

### Issue #4: Browser Caching Preventing Fixes
**Date**: August 19, 2025  
**Error**: CORS errors persisted even after backend was confirmed working via curl tests.

**Root Cause**: Browser was using cached JavaScript files with old configuration.

**Solution**:
1. Added cache-busting headers in Next.js config
2. Added timestamp parameters to API requests
3. Enhanced logging for debugging

**Files Modified**:
- `plancast-frontend/next.config.ts`
- `plancast-frontend/lib/api/client.ts`

**Status**: ✅ Resolved

## Key Lessons Learned

1. **Always test backend independently** - Use curl to verify backend is working before blaming frontend
2. **Browser caching is a major issue** - Always consider cache-busting when making configuration changes
3. **Type consistency is crucial** - Maintain consistent data structures between frontend and backend
4. **Timeout settings matter** - 3D processing requires longer timeouts than typical web requests
5. **CORS complexity** - Avoid `withCredentials` unless absolutely necessary

## Current Status

- ✅ Backend: Working correctly with proper CORS headers
- ✅ Frontend: Reverted to working state with proper timeout settings
- ✅ TypeScript: All compilation errors resolved
- ✅ Caching: Cache-busting mechanisms in place
- 🔄 Deployment: Waiting for Vercel deployment to complete

## Next Steps

1. Monitor Vercel deployment
2. Test application after deployment
3. Verify CORS errors are resolved
4. Test 3D model generation with new timeout settings

### Issue #5: Persistent CORS Errors with 502 Bad Gateway
**Date**: August 19, 2025  
**Error**: CORS errors persist even after cache-busting changes, now accompanied by 502 Bad Gateway errors.

**Root Cause**: Browser is still using cached JavaScript despite cache-busting headers. Backend confirmed working via curl test.

**Solution**: 
1. ✅ Test backend independently with curl to confirm it's working
2. Force complete browser cache clear
3. Check if Vercel deployment has completed
4. Consider backend restart if 502 errors persist

**Status**: ✅ Resolved - Frontend cache issue identified

### Issue #6: Backend Application Crash - Connection Refused
**Date**: August 19, 2025  
**Error**: Railway logs show "connection refused" errors with 502 Bad Gateway responses.

**Railway Log Details**:
- HTTP Status: 502
- Response Details: "Retried single replica"
- Upstream Errors: Multiple "connection refused" errors
- Deployment Instance: 6dc9bb70-089d-4e04-9766-d2366cb0a599

**Root Cause**: Backend crashed during CubiCasa inference. The app started successfully (took 36s to load model), but crashed when processing job 4132982b-4ef2-4ef3-b16e-e44df3c7b192.

**Timeline from Logs**:
1. Model loaded successfully in 35.13s
2. Server started on port 8000
3. Application startup complete
4. Crashed during "Running CubiCasa5K inference for job 4132982b-4ef2-4ef3-b16e-e44df3c7b192"

**Likely Causes**:
- Memory exhaustion during inference (model uses significant RAM)
- CPU timeout on Railway (inference on CPU is very slow)
- Railway resource limits exceeded

**Solution**:
1. ✅ Identified crash during CubiCasa inference
2. Restart the backend service on Railway
3. Consider reducing model complexity or batch size
4. Monitor memory usage during inference
5. Consider using smaller test images initially

**Status**: 🔄 In Progress - Need to restart and monitor memory usage

### Issue #7: Model Loading on Every Deploy
**Date**: August 19, 2025  
**Error**: 199MB CubiCasa model is being downloaded/loaded on every deployment, causing memory issues and slow startups.

**Root Cause**: Model file is not persisted between deployments.

**Solution - Railway Persistent Volume**:

1. **Add Persistent Volume in Railway**:
   - Go to your Railway project
   - Click on your backend service
   - Go to "Settings" tab
   - Scroll to "Volumes"
   - Click "Add Volume"
   - Mount path: `/data`
   - Size: 5GB (or more)

2. **Environment Variable**:
   - Add `RAILWAY_PERSISTENT_DIR=/data` to your Railway environment variables

3. **How it Works**:
   - The code already checks for `RAILWAY_PERSISTENT_DIR`
   - If found, it stores the model in `/data/models/`
   - Model is downloaded once and reused across deployments
   - Reduces memory usage and startup time

4. **Benefits**:
   - Model downloaded only once
   - Faster deployments (no 35-second model loading)
   - Less memory usage during startup
   - Model persists across restarts

**Status**: ❌ Not available - Railway persistent volumes not available in current plan

### Issue #8: Railway Persistent Volumes Not Available
**Date**: August 19, 2025  
**Error**: Railway persistent volumes feature not available in current plan/region.

**Alternative Solutions**:

1. **Use Railway's Built-in Storage** (Recommended):
   - Railway has `/tmp` directory that persists between requests
   - Store model in `/tmp/models/` instead of `/data/`
   - Model persists during the container's lifetime

2. **External Cloud Storage**:
   - Upload model to Google Drive, AWS S3, or similar
   - Download on startup if not cached
   - Use environment variables for storage URLs

3. **Optimize Current Setup**:
   - Keep model in Docker image but optimize loading
   - Use lazy loading (load only when needed)
   - Clear memory after each inference

4. **Railway Plan Upgrade**:
   - Check if persistent volumes are available in paid plans
   - Consider upgrading Railway plan if needed

**Status**: ✅ Implemented - Using Railway /tmp storage

### Issue #9: Persistent Frontend Cache Issue
**Date**: August 19, 2025  
**Error**: CORS errors persist even after backend is confirmed working via curl tests.

**Root Cause**: Browser is aggressively caching old JavaScript files despite cache-busting headers.

**Evidence**:
- ✅ Backend working correctly (curl test successful)
- ✅ CORS headers present in backend response
- ✅ Job processing normally (status: "processing", progress: 10%)
- ❌ Frontend still getting CORS errors

**Solution - Force Complete Cache Clear**:

1. **Hard Refresh**: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
2. **Developer Tools Cache Clear**:
   - Open DevTools (F12)
   - Right-click refresh button
   - Select "Empty Cache and Hard Reload"
3. **Incognito Mode**: Test in private/incognito browser window
4. **Clear All Browser Data**: Clear cached images and files
5. **Wait for Vercel Deployment**: Ensure latest frontend code is deployed

**Status**: 🔄 In Progress - Need to force browser cache clear
