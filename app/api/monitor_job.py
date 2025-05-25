from typing import List

from fastapi import APIRouter

from services.job_manager import JobManager
from schema.monitor_job_schema import JobItems, JobStatusModel

router = APIRouter()


@router.put("/job-status", response_model=List[JobStatusModel])
async def get_job_status(input_models: JobItems) -> List[JobStatusModel]:
    """ジョブの状態を取得する."""
    output_models = [
        JobManager(job_id).get_job_stats() for job_id in input_models.job_ids
    ]
    return output_models


@router.delete("/delete-job", response_model=List[JobStatusModel])
async def delete_running_job(input_models: JobItems) -> List[JobStatusModel]:
    """実行中のジョブを削除する."""
    output_models = [JobManager(job_id).delete_job() for job_id in input_models.job_ids]
    return output_models
