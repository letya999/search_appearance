from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

class SearchStage(BaseModel):
    name: str
    status: str = "pending"  # pending, running, completed, error
    progress: float = 0.0
    message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class SearchSession(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: Optional[UUID] = None
    collection_id: Optional[UUID] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    stages: List[SearchStage] = []
    results: List[dict] = []

    def get_stage(self, name: str) -> Optional[SearchStage]:
        for stage in self.stages:
            if stage.name == name:
                return stage
        return None

    def add_stage(self, name: str) -> SearchStage:
        stage = SearchStage(name=name)
        self.stages.append(stage)
        return stage

    def update_stage(self, name: str, progress: float, status: str = "running", message: str = None):
        stage = self.get_stage(name)
        if not stage:
            stage = self.add_stage(name)
        
        stage.progress = progress
        stage.status = status
        
        if message:
            stage.message = message
            
        if status == "running" and not stage.started_at:
            stage.started_at = datetime.utcnow()
            
        if status == "completed":
            if not stage.started_at:
                stage.started_at = datetime.utcnow()
            stage.completed_at = datetime.utcnow()
            stage.progress = 1.0

    def complete(self):
        self.completed_at = datetime.utcnow()
