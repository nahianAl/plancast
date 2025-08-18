"""
WebSocket Manager for Real-time Updates

Handles WebSocket connections, job subscriptions, and real-time status updates
for the PlanCast application using Socket.IO.
"""

import asyncio
import logging
import json
from typing import Dict, Set, Optional, Any
from datetime import datetime

import socketio
from fastapi import FastAPI
from sqlalchemy.orm import Session

from models.database_connection import get_db_session
from models.repository import ProjectRepository
from models.data_structures import ProcessingStatus
from models.database import ProjectStatus
from pathlib import Path
import os

# Configure logging
logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections and real-time updates."""
    
    def __init__(self):
        # Create Socket.IO server with longer timeouts for real model processing
        self.sio = socketio.AsyncServer(
            async_mode='asgi',
            cors_allowed_origins=[
                "https://getplancast.com",
                "https://www.getplancast.com",
                "http://getplancast.com", 
                "http://www.getplancast.com",
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "https://localhost:3000",
                "https://127.0.0.1:3000"
            ],
            logger=True,
            engineio_logger=True,
            ping_timeout=60,  # Increased from default 20
            ping_interval=25,  # Increased from default 25
            max_http_buffer_size=1e8,  # 100MB buffer for large files
            allow_upgrades=True,
            transports=['websocket', 'polling']
        )
        
        # Connection tracking
        self.connections: Dict[str, Dict[str, Any]] = {}  # sid -> connection info
        self.job_subscriptions: Dict[str, Set[str]] = {}  # job_id -> set of sids
        self.user_connections: Dict[str, Set[str]] = {}   # user_id -> set of sids
        
        # Register event handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register Socket.IO event handlers."""
        
        @self.sio.event
        async def connect(sid, environ):
            """Handle client connection."""
            logger.info(f"WebSocket client connected: {sid}")
            
            # Initialize connection info
            self.connections[sid] = {
                'connected_at': datetime.utcnow().isoformat(),
                'user_id': None,
                'authenticated': False,
                'subscribed_jobs': set(),
            }
            
            # Send welcome message
            await self.sio.emit('message', {
                'type': 'welcome',
                'message': 'Connected to PlanCast real-time updates',
                'timestamp': datetime.utcnow().isoformat(),
            }, room=sid)
        
        @self.sio.event
        async def disconnect(sid):
            """Handle client disconnection."""
            logger.info(f"WebSocket client disconnected: {sid}")
            
            if sid in self.connections:
                connection = self.connections[sid]
                user_id = connection.get('user_id')
                
                # Clean up job subscriptions
                for job_id in connection.get('subscribed_jobs', set()):
                    if job_id in self.job_subscriptions:
                        self.job_subscriptions[job_id].discard(sid)
                        if not self.job_subscriptions[job_id]:
                            del self.job_subscriptions[job_id]
                
                # Clean up user connections
                if user_id and user_id in self.user_connections:
                    self.user_connections[user_id].discard(sid)
                    if not self.user_connections[user_id]:
                        del self.user_connections[user_id]
                
                # Remove connection
                del self.connections[sid]
        
        @self.sio.event
        async def authenticate(sid, data):
            """Handle client authentication."""
            try:
                user_id = data.get('userId')
                email = data.get('email')
                
                if not user_id or not email:
                    await self.sio.emit('error', {
                        'message': 'Invalid authentication data'
                    }, room=sid)
                    return
                
                # Update connection info
                if sid in self.connections:
                    self.connections[sid]['user_id'] = user_id
                    self.connections[sid]['email'] = email
                    self.connections[sid]['authenticated'] = True
                    
                    # Track user connections
                    if user_id not in self.user_connections:
                        self.user_connections[user_id] = set()
                    self.user_connections[user_id].add(sid)
                
                logger.info(f"Client authenticated: {sid} -> {email}")
                
                await self.sio.emit('message', {
                    'type': 'authenticated',
                    'message': f'Authenticated as {email}',
                    'timestamp': datetime.utcnow().isoformat(),
                }, room=sid)
                
            except Exception as e:
                logger.error(f"Authentication error for {sid}: {e}")
                await self.sio.emit('error', {
                    'message': 'Authentication failed'
                }, room=sid)
        
        @self.sio.event
        async def subscribe_job(sid, data):
            """Handle job subscription."""
            try:
                job_id = data.get('jobId')
                
                if not job_id:
                    await self.sio.emit('error', {
                        'message': 'Job ID is required'
                    }, room=sid)
                    return
                
                # Add to job subscriptions
                if job_id not in self.job_subscriptions:
                    self.job_subscriptions[job_id] = set()
                self.job_subscriptions[job_id].add(sid)
                
                # Update connection info
                if sid in self.connections:
                    self.connections[sid]['subscribed_jobs'].add(job_id)
                
                logger.info(f"Client {sid} subscribed to job {job_id}")
                
                # Send current job status immediately
                await self._send_job_status(job_id, sid)
                
                await self.sio.emit('message', {
                    'type': 'subscribed',
                    'jobId': job_id,
                    'message': f'Subscribed to job updates',
                    'timestamp': datetime.utcnow().isoformat(),
                }, room=sid)
                
            except Exception as e:
                logger.error(f"Subscription error for {sid}: {e}")
                await self.sio.emit('error', {
                    'message': 'Failed to subscribe to job'
                }, room=sid)
        
        @self.sio.event
        async def unsubscribe_job(sid, data):
            """Handle job unsubscription."""
            try:
                job_id = data.get('jobId')
                
                if not job_id:
                    return
                
                # Remove from job subscriptions
                if job_id in self.job_subscriptions:
                    self.job_subscriptions[job_id].discard(sid)
                    if not self.job_subscriptions[job_id]:
                        del self.job_subscriptions[job_id]
                
                # Update connection info
                if sid in self.connections:
                    self.connections[sid]['subscribed_jobs'].discard(job_id)
                
                logger.info(f"Client {sid} unsubscribed from job {job_id}")
                
                await self.sio.emit('message', {
                    'type': 'unsubscribed',
                    'jobId': job_id,
                    'message': f'Unsubscribed from job updates',
                    'timestamp': datetime.utcnow().isoformat(),
                }, room=sid)
                
            except Exception as e:
                logger.error(f"Unsubscription error for {sid}: {e}")
    
    async def _send_job_status(self, job_id: str, sid: Optional[str] = None):
        """Send current job status to client(s)."""
        try:
            print(f"🔍 Sending job status for {job_id} to {sid or 'all subscribers'}")
            
            with get_db_session() as session:
                project = ProjectRepository.get_project_by_id(session, int(job_id))
                
                if not project:
                    print(f"❌ Project not found for job {job_id}")
                    return
                
                print(f"🔍 Project status: {project.status}, progress: {project.progress_percent}")
                
                # Build result payload if completed
                result_payload = None
                if project.status == ProjectStatus.COMPLETED:
                    print(f"🔍 Project completed, building result payload")
                    exported_files = project.output_files or {}
                    print(f"🔍 Exported files: {exported_files}")
                    
                    # Prefer GLB
                    glb_path = exported_files.get('glb')
                    if glb_path:
                        filename_only = Path(glb_path).name
                        relative_url = f"/models/{job_id}/{filename_only}"
                        public_api_url = os.getenv('PUBLIC_API_URL', '')
                        model_url = f"{public_api_url}{relative_url}" if public_api_url else relative_url
                    else:
                        # Fallback to any available format
                        first_path = next(iter(exported_files.values()), '')
                        filename_only = Path(first_path).name if first_path else ''
                        relative_url = f"/models/{job_id}/{filename_only}" if first_path else ''
                        public_api_url = os.getenv('PUBLIC_API_URL', '')
                        model_url = f"{public_api_url}{relative_url}" if public_api_url and relative_url else relative_url
                    
                    result_payload = {
                        'model_url': model_url,
                        'formats': list(exported_files.keys()),
                        'output_files': {
                            fmt: (
                                (f"{os.getenv('PUBLIC_API_URL', '')}/models/{job_id}/{Path(p).name}") if os.getenv('PUBLIC_API_URL') else f"/models/{job_id}/{Path(p).name}"
                            ) for fmt, p in exported_files.items()
                        }
                    }
                    print(f"🔍 Result payload: {result_payload}")

                status_update = {
                    'jobId': job_id,
                    'status': project.status.value,
                    'progress': project.progress_percent or 0,
                    'message': project.error_message or None,
                    'result': result_payload,
                }
                
                print(f"🔍 Status update: {status_update}")
                
                if sid:
                    # Send to specific client
                    print(f"🔍 Sending to specific client {sid}")
                    await self.sio.emit('job_status', status_update, room=sid)
                    print(f"✅ Sent to client {sid}")
                else:
                    # Send to all subscribers of this job
                    if job_id in self.job_subscriptions:
                        for subscriber_sid in self.job_subscriptions[job_id]:
                            print(f"🔍 Sending to subscriber {subscriber_sid}")
                            await self.sio.emit('job_status', status_update, room=subscriber_sid)
                            print(f"✅ Sent to subscriber {subscriber_sid}")
                
        except Exception as e:
            logger.error(f"Error sending job status for {job_id}: {e}")
            print(f"❌ Error sending job status for {job_id}: {e}")
    
    async def broadcast_job_update(self, job_id: str, status: str, progress: float = 0, 
                                 message: Optional[str] = None, result: Optional[Dict] = None):
        """Broadcast job status update to all subscribers."""
        try:
            print(f"🔍 Broadcasting job update for {job_id}: {status} ({progress}%)")
            print(f"🔍 Subscribers: {self.job_subscriptions.get(job_id, set())}")
            
            if job_id not in self.job_subscriptions:
                print(f"❌ No subscribers found for job {job_id}")
                return
            
            status_update = {
                'jobId': job_id,
                'status': status,
                'progress': progress,
                'message': message,
                'result': result,
                'timestamp': datetime.utcnow().isoformat(),
            }
            
            print(f"🔍 Status update payload: {status_update}")
            
            # Send to all subscribers
            for sid in self.job_subscriptions[job_id]:
                try:
                    print(f"🔍 Sending to subscriber {sid}")
                    await self.sio.emit('job_status', status_update, room=sid)
                    print(f"✅ Sent to subscriber {sid}")
                except Exception as e:
                    logger.error(f"Failed to send update to {sid}: {e}")
                    print(f"❌ Failed to send to {sid}: {e}")
            
            logger.info(f"Broadcasted job update for {job_id}: {status} ({progress}%)")
            print(f"✅ Broadcasted job update for {job_id}: {status} ({progress}%)")
            
        except Exception as e:
            logger.error(f"Error broadcasting job update for {job_id}: {e}")
            print(f"❌ Error broadcasting job update for {job_id}: {e}")
    
    async def broadcast_processing_progress(self, job_id: str, step: str, progress: float, 
                                          details: Optional[str] = None):
        """Broadcast detailed processing progress."""
        try:
            if job_id not in self.job_subscriptions:
                return
            
            progress_update = {
                'jobId': job_id,
                'step': step,
                'progress': progress,
                'details': details,
                'timestamp': datetime.utcnow().isoformat(),
            }
            
            # Send to all subscribers
            for sid in self.job_subscriptions[job_id]:
                try:
                    await self.sio.emit('processing_progress', progress_update, room=sid)
                except Exception as e:
                    logger.error(f"Failed to send progress to {sid}: {e}")
            
        except Exception as e:
            logger.error(f"Error broadcasting processing progress for {job_id}: {e}")
    
    async def notify_user(self, user_id: str, notification_type: str, data: Dict[str, Any]):
        """Send notification to all connections of a specific user."""
        try:
            if user_id not in self.user_connections:
                return
            
            notification = {
                'type': notification_type,
                'data': data,
                'timestamp': datetime.utcnow().isoformat(),
            }
            
            # Send to all user connections
            for sid in self.user_connections[user_id]:
                try:
                    await self.sio.emit('notification', notification, room=sid)
                except Exception as e:
                    logger.error(f"Failed to send notification to {sid}: {e}")
            
        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {e}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            'total_connections': len(self.connections),
            'authenticated_connections': len([c for c in self.connections.values() if c['authenticated']]),
            'job_subscriptions': len(self.job_subscriptions),
            'user_connections': len(self.user_connections),
        }
    
    def mount_to_app(self, app: FastAPI):
        """Mount Socket.IO to FastAPI app."""
        socketio_app = socketio.ASGIApp(self.sio, other_asgi_app=app, socketio_path='socket.io')
        return socketio_app

# Global WebSocket manager instance
websocket_manager = WebSocketManager()
