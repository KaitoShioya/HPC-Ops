import uvicorn
import yaml
from fastapi import FastAPI

from api import create_job, monitor_job


app = FastAPI(
    title="HPC-Ops server",
    version="0.1.0",
    description="Experiments operations for using super computer",
)
# routerを読み込む
app.include_router(create_job.router)
app.include_router(monitor_job.router)


if __name__ == "__main__":
    # uvicornログ設定ロード
    logging_config = yaml.safe_load(
        open("app/logging_config.yaml", "r", encoding="utf-8_sig")
    )
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_config=logging_config,
    )
