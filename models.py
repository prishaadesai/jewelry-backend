from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

# ==================== ENUMS ====================

class UserRole(str, Enum):
    owner = "owner"
    caster = "caster"
    filer = "filer"
    setter = "setter"
    polisher = "polisher"

class JobStatus(str, Enum):
    created = "created"
    in_progress = "in_progress"
    pending_assignment = "pending_assignment"
    completed = "completed"
    cancelled = "cancelled"

class ProductionStage(str, Enum):
    casting = "casting"
    filing = "filing"
    setting = "setting"
    polishing = "polishing"

# ==================== USER MODELS ====================

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=6)
    role: UserRole

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

# ==================== JOB MODELS ====================

class JobCreate(BaseModel):
    design_no: str = Field(..., max_length=50)
    item_category: str = Field(..., max_length=50)
    initial_weight: float = Field(..., gt=0)
    description: Optional[str] = None

    @validator('initial_weight')
    def validate_weight(cls, v):
        if v <= 0:
            raise ValueError('Weight must be positive')
        return round(v, 3)

class JobUpdate(BaseModel):
    design_no: Optional[str] = Field(None, max_length=50)
    item_category: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    status: Optional[JobStatus] = None

class JobResponse(BaseModel):
    id: int
    design_no: str
    item_category: str
    initial_weight: float
    total_loss: float
    loss_percentage: float
    status: str
    current_stage: Optional[str] = None
    current_worker_id: Optional[int] = None
    created_at: datetime
    created_by: int
    description: Optional[str] = None

    class Config:
        from_attributes = True

class JobAssignment(BaseModel):
    worker_id: int
    stage: ProductionStage
    issued_weight: float = Field(..., gt=0)

    @validator('issued_weight')
    def validate_weight(cls, v):
        if v <= 0:
            raise ValueError('Weight must be positive')
        return round(v, 3)

# ==================== TRANSACTION MODELS ====================

class TransactionResponse(BaseModel):
    id: int
    job_id: int
    worker_id: int
    stage: str
    issued_weight: float
    returned_weight: Optional[float] = None
    loss: Optional[float] = None
    loss_percentage: Optional[float] = None
    issued_at: datetime
    returned_at: Optional[datetime] = None
    status: str
    notes: Optional[str] = None

    class Config:
        from_attributes = True

class JobDetailResponse(JobResponse):
    transactions: List[TransactionResponse] = []

# ==================== WORKER MODELS ====================

class WorkerTaskResponse(BaseModel):
    transaction_id: int
    job_id: int
    design_no: str
    item_category: str
    stage: str
    issued_weight: float
    issued_at: datetime

class WorkerTaskCompletion(BaseModel):
    transaction_id: int
    returned_weight: float = Field(..., gt=0)
    notes: Optional[str] = None

    @validator('returned_weight')
    def validate_weight(cls, v):
        if v <= 0:
            raise ValueError('Weight must be positive')
        return round(v, 3)

# ==================== REPORT MODELS ====================

class WorkerPerformanceReport(BaseModel):
    worker_id: int
    worker_name: str
    role: str
    total_jobs: int
    total_loss: float
    average_loss_percentage: float

class MaterialConsumptionReport(BaseModel):
    item_category: str
    total_jobs: int
    total_initial_weight: float
    total_loss: float
    loss_percentage: float
