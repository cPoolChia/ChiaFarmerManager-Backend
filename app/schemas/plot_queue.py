from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

from enum import Enum
from fastapi_utils.api_model import APIModel


class PlotQueueStatus(Enum):
    PENDING = "pending"
    PLOTTING = "plotting"
    WAITING = "waiting"
    FAILED = "failed"
    PAUSED = "paused"


class PlotQueueCreate(APIModel):
    server_id: UUID
    temp_dir_id: UUID
    final_dir_id: UUID
    autoplot: bool = True
    plots_amount: int


class PlotQueueUpdate(APIModel):
    temp_dir_id: Optional[UUID] = None
    final_dir_id: Optional[UUID] = None
    plots_amount: Optional[int] = None
    autoplot: Optional[bool] = None


class PlotQueueReturn(APIModel):
    id: UUID
    plot_task_id: Optional[UUID]
    server_id: UUID
    temp_dir_id: UUID
    final_dir_id: UUID
    plotting_started: Optional[datetime]
    autoplot: bool
    plots_amount: int
    created: datetime
    status: PlotQueueStatus
