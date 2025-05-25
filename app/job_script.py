import asyncio
import pickle
import sys

from services.job_executor import JobExecutor


if __name__ == "__main__":
    with open(sys.argv[1], "rb") as f:
        job_executor = JobExecutor(pickle.load(f))
    asyncio.run(job_executor.execute_single_job())
