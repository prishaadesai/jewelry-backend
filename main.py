from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

from models import *
from auth import create_access_token, verify_token, get_current_user, get_password_hash, verify_password
from database import SupabaseClient

load_dotenv()

app = FastAPI(title="Jewelry Production Management System")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase client
supabase_client = SupabaseClient()

@app.get("/")
async def root():
    return {"message": "Jewelry Production Management API", "status": "running"}

# ==================== AUTH ENDPOINTS ====================

@app.post("/api/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """Owner can register new users (workers)"""
    try:
        # Check if user already exists
        existing = supabase_client.client.table("users").select("*").eq("username", user_data.username).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        # Insert user
        user_dict = {
            "username": user_data.username,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "role": user_data.role,
            "hashed_password": hashed_password,
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True
        }
        
        result = supabase_client.client.table("users").insert(user_dict).execute()
        return UserResponse(**result.data[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login endpoint for all users"""
    try:
        user = supabase_client.client.table("users").select("*").eq("username", form_data.username).execute()
        
        if not user.data or not verify_password(form_data.password, user.data[0]["hashed_password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_data = user.data[0]
        if not user_data["is_active"]:
            raise HTTPException(status_code=400, detail="Inactive user")
        
        access_token = create_access_token(data={"sub": user_data["username"], "role": user_data["role"]})
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    return UserResponse(**current_user)

# ==================== USER MANAGEMENT (OWNER ONLY) ====================

@app.get("/api/users", response_model=List[UserResponse])
async def get_all_users(current_user: dict = Depends(get_current_user)):
    """Get all users (Owner only)"""
    if current_user["role"] != "owner":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        result = supabase_client.client.table("users").select("*").execute()
        return [UserResponse(**user) for user in result.data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, current_user: dict = Depends(get_current_user)):
    """Get specific user details"""
    if current_user["role"] != "owner":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        result = supabase_client.client.table("users").select("*").eq("id", user_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")
        return UserResponse(**result.data[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_update: UserUpdate, current_user: dict = Depends(get_current_user)):
    """Update user details (Owner only)"""
    if current_user["role"] != "owner":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        update_data = user_update.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")
        
        result = supabase_client.client.table("users").update(update_data).eq("id", user_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="User not found")
        return UserResponse(**result.data[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/users/{user_id}")
async def delete_user(user_id: int, current_user: dict = Depends(get_current_user)):
    """Delete user (Owner only)"""
    if current_user["role"] != "owner":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        result = supabase_client.client.table("users").delete().eq("id", user_id).execute()
        return {"message": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== JOB MANAGEMENT ====================

@app.post("/api/jobs", response_model=JobResponse)
async def create_job(job_data: JobCreate, current_user: dict = Depends(get_current_user)):
    """Create new job (Owner only)"""
    if current_user["role"] != "owner":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        job_dict = {
            **job_data.dict(),
            "created_by": current_user["id"],
            "created_at": datetime.utcnow().isoformat(),
            "status": "created",
            "current_stage": None,
            "total_loss": 0.0,
            "loss_percentage": 0.0
        }
        
        result = supabase_client.client.table("jobs").insert(job_dict).execute()
        return JobResponse(**result.data[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs", response_model=List[JobResponse])
async def get_all_jobs(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all jobs with optional status filter"""
    try:
        query = supabase_client.client.table("jobs").select("*")
        if status:
            query = query.eq("status", status)
        
        result = query.execute()
        return [JobResponse(**job) for job in result.data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/{job_id}", response_model=JobDetailResponse)
async def get_job(job_id: int, current_user: dict = Depends(get_current_user)):
    """Get specific job with all transaction history"""
    try:
        # Get job details
        job_result = supabase_client.client.table("jobs").select("*").eq("id", job_id).execute()
        if not job_result.data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Get all transactions for this job
        transactions_result = supabase_client.client.table("transactions").select("*, users(full_name, role)").eq("job_id", job_id).order("issued_at").execute()
        
        job_data = job_result.data[0]
        job_data["transactions"] = transactions_result.data
        
        return JobDetailResponse(**job_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/jobs/{job_id}", response_model=JobResponse)
async def update_job(job_id: int, job_update: JobUpdate, current_user: dict = Depends(get_current_user)):
    """Update job details (Owner only)"""
    if current_user["role"] != "owner":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        update_data = job_update.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")
        
        result = supabase_client.client.table("jobs").update(update_data).eq("id", job_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Job not found")
        return JobResponse(**result.data[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== JOB ASSIGNMENT ====================

@app.post("/api/jobs/{job_id}/assign", response_model=TransactionResponse)
async def assign_job(job_id: int, assignment: JobAssignment, current_user: dict = Depends(get_current_user)):
    """Assign job to worker (Owner only)"""
    if current_user["role"] != "owner":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # Get job details
        job_result = supabase_client.client.table("jobs").select("*").eq("id", job_id).execute()
        if not job_result.data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        job = job_result.data[0]
        
        # Create transaction
        transaction_dict = {
            "job_id": job_id,
            "worker_id": assignment.worker_id,
            "stage": assignment.stage,
            "issued_weight": assignment.issued_weight,
            "issued_at": datetime.utcnow().isoformat(),
            "status": "in_progress"
        }
        
        transaction_result = supabase_client.client.table("transactions").insert(transaction_dict).execute()
        
        # Update job status and current stage
        supabase_client.client.table("jobs").update({
            "status": "in_progress",
            "current_stage": assignment.stage,
            "current_worker_id": assignment.worker_id
        }).eq("id", job_id).execute()
        
        return TransactionResponse(**transaction_result.data[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== WORKER OPERATIONS ====================

@app.get("/api/worker/tasks", response_model=List[WorkerTaskResponse])
async def get_my_tasks(current_user: dict = Depends(get_current_user)):
    """Get tasks assigned to current worker"""
    if current_user["role"] == "owner":
        raise HTTPException(status_code=403, detail="This endpoint is for workers only")
    
    try:
        # Get in-progress transactions for this worker
        result = supabase_client.client.table("transactions").select("*, jobs(*)").eq("worker_id", current_user["id"]).eq("status", "in_progress").execute()
        
        tasks = []
        for transaction in result.data:
            tasks.append(WorkerTaskResponse(
                transaction_id=transaction["id"],
                job_id=transaction["job_id"],
                design_no=transaction["jobs"]["design_no"],
                item_category=transaction["jobs"]["item_category"],
                stage=transaction["stage"],
                issued_weight=transaction["issued_weight"],
                issued_at=transaction["issued_at"]
            ))
        
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/worker/complete-task", response_model=TransactionResponse)
async def complete_task(task_completion: WorkerTaskCompletion, current_user: dict = Depends(get_current_user)):
    """Worker completes their assigned task"""
    if current_user["role"] == "owner":
        raise HTTPException(status_code=403, detail="This endpoint is for workers only")
    
    try:
        # Get transaction
        trans_result = supabase_client.client.table("transactions").select("*").eq("id", task_completion.transaction_id).eq("worker_id", current_user["id"]).execute()
        
        if not trans_result.data:
            raise HTTPException(status_code=404, detail="Transaction not found or not assigned to you")
        
        transaction = trans_result.data[0]
        
        # Validate returned weight
        if task_completion.returned_weight > transaction["issued_weight"]:
            raise HTTPException(status_code=400, detail="Returned weight cannot be greater than issued weight")
        
        # Calculate loss
        loss = transaction["issued_weight"] - task_completion.returned_weight
        loss_percentage = (loss / transaction["issued_weight"]) * 100 if transaction["issued_weight"] > 0 else 0
        
        # Update transaction
        update_data = {
            "returned_weight": task_completion.returned_weight,
            "returned_at": datetime.utcnow().isoformat(),
            "loss": loss,
            "loss_percentage": loss_percentage,
            "status": "completed",
            "notes": task_completion.notes
        }
        
        updated_trans = supabase_client.client.table("transactions").update(update_data).eq("id", task_completion.transaction_id).execute()
        
        # Update job total loss
        job_result = supabase_client.client.table("jobs").select("*").eq("id", transaction["job_id"]).execute()
        job = job_result.data[0]
        
        new_total_loss = job["total_loss"] + loss
        new_loss_percentage = (new_total_loss / job["initial_weight"]) * 100 if job["initial_weight"] > 0 else 0
        
        supabase_client.client.table("jobs").update({
            "total_loss": new_total_loss,
            "loss_percentage": new_loss_percentage,
            "current_worker_id": None,
            "status": "pending_assignment"
        }).eq("id", transaction["job_id"]).execute()
        
        return TransactionResponse(**updated_trans.data[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== REPORTS & ANALYTICS ====================

@app.get("/api/reports/worker-performance", response_model=List[WorkerPerformanceReport])
async def get_worker_performance(current_user: dict = Depends(get_current_user)):
    """Get worker performance report (Owner only)"""
    if current_user["role"] != "owner":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        # Get all completed transactions with user details
        result = supabase_client.client.table("transactions").select("*, users(full_name, role)").eq("status", "completed").execute()
        
        # Aggregate by worker
        worker_stats = {}
        for trans in result.data:
            worker_id = trans["worker_id"]
            if worker_id not in worker_stats:
                worker_stats[worker_id] = {
                    "worker_id": worker_id,
                    "worker_name": trans["users"]["full_name"],
                    "role": trans["users"]["role"],
                    "total_jobs": 0,
                    "total_loss": 0.0,
                    "average_loss_percentage": 0.0
                }
            
            worker_stats[worker_id]["total_jobs"] += 1
            worker_stats[worker_id]["total_loss"] += trans["loss"]
        
        # Calculate averages
        reports = []
        for worker_id, stats in worker_stats.items():
            avg_loss = (stats["total_loss"] / stats["total_jobs"]) if stats["total_jobs"] > 0 else 0
            stats["average_loss_percentage"] = avg_loss
            reports.append(WorkerPerformanceReport(**stats))
        
        return sorted(reports, key=lambda x: x.average_loss_percentage, reverse=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/job-summary")
async def get_job_summary(current_user: dict = Depends(get_current_user)):
    """Get overall job summary statistics"""
    try:
        jobs = supabase_client.client.table("jobs").select("*").execute()
        
        total_jobs = len(jobs.data)
        completed = len([j for j in jobs.data if j["status"] == "completed"])
        in_progress = len([j for j in jobs.data if j["status"] == "in_progress"])
        pending = total_jobs - completed - in_progress
        
        total_initial_weight = sum(j["initial_weight"] for j in jobs.data)
        total_loss = sum(j["total_loss"] for j in jobs.data)
        avg_loss_percentage = (total_loss / total_initial_weight * 100) if total_initial_weight > 0 else 0
        
        return {
            "total_jobs": total_jobs,
            "completed_jobs": completed,
            "in_progress_jobs": in_progress,
            "pending_jobs": pending,
            "total_initial_weight": total_initial_weight,
            "total_loss": total_loss,
            "average_loss_percentage": round(avg_loss_percentage, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/material-consumption")
async def get_material_consumption(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get material consumption report with date filters"""
    if current_user["role"] != "owner":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        query = supabase_client.client.table("jobs").select("*")
        
        if start_date:
            query = query.gte("created_at", start_date)
        if end_date:
            query = query.lte("created_at", end_date)
        
        result = query.execute()
        
        # Group by item category
        category_stats = {}
        for job in result.data:
            category = job["item_category"]
            if category not in category_stats:
                category_stats[category] = {
                    "item_category": category,
                    "total_jobs": 0,
                    "total_initial_weight": 0.0,
                    "total_loss": 0.0,
                    "loss_percentage": 0.0
                }
            
            category_stats[category]["total_jobs"] += 1
            category_stats[category]["total_initial_weight"] += job["initial_weight"]
            category_stats[category]["total_loss"] += job["total_loss"]
        
        # Calculate percentages
        for category in category_stats.values():
            if category["total_initial_weight"] > 0:
                category["loss_percentage"] = (category["total_loss"] / category["total_initial_weight"]) * 100
        
        return list(category_stats.values())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
