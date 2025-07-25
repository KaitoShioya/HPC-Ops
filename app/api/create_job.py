import concurrent.futures
from typing import Dict, Tuple

from fastapi import APIRouter

from services.job_executor import JobExecutor
from schema.create_job_schema import MultiInputModel, InputModel, OutputModel

router = APIRouter()


@router.post("/create-local-job", response_model=OutputModel)
async def create_local_job(input_model: InputModel) -> OutputModel:
    """ローカルテスト用のエンドポイント"""
    executor = JobExecutor(input_model)
    try:
        await executor.execute_single_job()
        msg = "Local job is successfuly completed"
        status = 0
    except Exception as e:
        msg = e
        status = 400
    output = OutputModel(status=status, msg=msg)
    return output


@router.post("/create-job", response_model=OutputModel)
async def create_job(input_model: InputModel) -> OutputModel:
    """1つのジョブを投入する."""
    executor = JobExecutor(input_model)
    output = executor.submit_job(input_model)
    return output


@router.post("/create-multi-job", response_model=Dict[OutputModel, InputModel])
async def create_jobs(input_models: MultiInputModel) -> Dict[OutputModel, InputModel]:
    """複数のジョブを投入する"""

    def execute_wrapper(input_model: InputModel) -> Tuple[InputModel, OutputModel]:
        executor = JobExecutor(input_model)
        output_model = executor.submit_job(input_model)
        return (input_model, output_model)

    output_models = {}
    with concurrent.futures.ProcessPoolExecutor() as executor:
        result = [
            executor.submit(execute_wrapper, input_model)
            for input_model in input_models.jobs
        ]
        for result in concurrent.futures.as_completed(result):
            result_set = result.result()
            output_models[result_set[-1]] = result_set[0]
    return output_models
