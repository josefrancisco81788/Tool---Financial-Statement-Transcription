import json
import time
from datetime import datetime
from typing import Dict, Optional, Any
import threading

class JobManager:
    """Manages background job processing and status tracking"""
    
    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
    
    def create_job(self, job_id: str, job_data: Dict[str, Any]) -> None:
        """Create a new job"""
        with self.lock:
            self.jobs[job_id] = {
                **job_data,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "progress": 0,
                "message": "Job created"
            }
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status and data"""
        with self.lock:
            return self.jobs.get(job_id)
    
    def update_job(self, job_id: str, updates: Dict[str, Any]) -> bool:
        """Update job status and data"""
        with self.lock:
            if job_id not in self.jobs:
                return False
            
            self.jobs[job_id].update(updates)
            self.jobs[job_id]["updated_at"] = datetime.utcnow().isoformat()
            return True
    
    def update_progress(self, job_id: str, progress: int, message: str = None) -> bool:
        """Update job progress"""
        updates = {"progress": progress}
        if message:
            updates["message"] = message
        return self.update_job(job_id, updates)
    
    def complete_job(self, job_id: str, result: Dict[str, Any], error: str = None) -> bool:
        """Mark job as completed"""
        updates = {
            "status": "completed" if not error else "failed",
            "completed_at": datetime.utcnow().isoformat(),
            "progress": 100
        }
        
        if result:
            updates["result"] = result
        if error:
            updates["error"] = error
            updates["message"] = f"Processing failed: {error}"
        else:
            updates["message"] = "Processing completed successfully"
        
        return self.update_job(job_id, updates)
    
    def list_jobs(self, limit: int = 50) -> Dict[str, Dict[str, Any]]:
        """List recent jobs"""
        with self.lock:
            # Sort by creation time, newest first
            sorted_jobs = sorted(
                self.jobs.items(),
                key=lambda x: x[1]["created_at"],
                reverse=True
            )
            return dict(sorted_jobs[:limit])
    
    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """Remove old completed jobs"""
        cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        removed_count = 0
        
        with self.lock:
            jobs_to_remove = []
            for job_id, job_data in self.jobs.items():
                created_time = datetime.fromisoformat(job_data["created_at"]).timestamp()
                if created_time < cutoff_time and job_data.get("status") in ["completed", "failed"]:
                    jobs_to_remove.append(job_id)
            
            for job_id in jobs_to_remove:
                del self.jobs[job_id]
                removed_count += 1
        
        return removed_count
    
    def get_job_stats(self) -> Dict[str, Any]:
        """Get job processing statistics"""
        with self.lock:
            total_jobs = len(self.jobs)
            completed_jobs = sum(1 for job in self.jobs.values() if job.get("status") == "completed")
            failed_jobs = sum(1 for job in self.jobs.values() if job.get("status") == "failed")
            processing_jobs = sum(1 for job in self.jobs.values() if job.get("status") == "processing")
            
            return {
                "total_jobs": total_jobs,
                "completed_jobs": completed_jobs,
                "failed_jobs": failed_jobs,
                "processing_jobs": processing_jobs,
                "success_rate": (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
            } 