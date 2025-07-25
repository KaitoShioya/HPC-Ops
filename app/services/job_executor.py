import concurrent.futures
import logging
import pickle
import os
import subprocess
import sys
from importlib import import_module
from pathlib import Path
from uuid import uuid4

import pandas as pd
import wandb

from core.base_flow_logic import BaseFlowLogic
from schema.create_job_schema import InputModel, OutputModel
from utils.config import settings

sys.path.append(settings.BASE_DIR_PATH)


class JobExecutor:
    def __init__(self, input_model: InputModel) -> None:
        self._logger = logging.getLogger("uvicorn")
        self.cfg = input_model.model_dump()
        self.wandb_apikey = settings.WANDB_APIKEY
        self.params = input_model.params
        # wandb内の実験粒度
        self.project_name = input_model.project
        self.group_name = input_model.group
        self.jobtype_name = input_model.jobtype
        self.run_name = input_model.run
        # flow logicのバージョン
        self.flow_logic_name = input_model.flow_logic

    def submit_job(self, input_model: InputModel) -> OutputModel:
        """1つのジョブを投入する."""
        self._logger.info("Start to submit job")
        job_number = str(uuid4())
        ts_str = pd.Timestamp.now(tz="Asia/Tokyo").strftime("%Y%m%d%H%M%S")
        tmp_dir = str(
            Path(settings.BASE_DIR_PATH) / Path(f"tmp/{ts_str}_{job_number}/")
        )
        os.makedirs(tmp_dir, exist_ok=True)
        pkl_path = str(Path(tmp_dir) / Path(f"tmp_{job_number}.pkl"))
        with open(pkl_path, "wb") as f:
            pickle.dump(input_model, f)
        py_path = str(Path(settings.BASE_DIR_PATH) / Path("app/job_script.py"))
        sh_path = str(Path(tmp_dir) / Path(f"job_{job_number}.sh"))
        with open(sh_path, "w") as f:
            f.writelines([f"cd {settings.BASE_DIR_PATH}\n"])
            f.writelines([f"python {py_path} {pkl_path}"])
        self._logger.info("InputModel info:")
        self._logger.info(f"\tInputModel: {input_model}")
        self._logger.info(f"\tInputModel path: {pkl_path}")
        self._logger.info("path info:")
        self._logger.info(f"\tpy script path: {py_path}")
        self._logger.info(f"\tsh script path: {sh_path}")

        command = ["pjsub", "-L", f"rscgrp={settings.RESOURCE_GROUP}"]
        if input_model.node:
            command[-1] += f",node={input_model.node}"
        if input_model.vnode_core:
            command[-1] += f",vnode-core={input_model.vnode_core}"
        if input_model.gpu:
            command[-1] += f",gpu={input_model.gpu}"
        if input_model.elapse:
            command[-1] += f",elapse={input_model.elapse}"
        log_path = str(Path(tmp_dir) / Path(f"result_{job_number}.out"))
        self._logger.info(f"\tstdout path: {log_path}")
        command += ["-j", "-o", log_path, sh_path]

        self._logger.info(f"command: {command}")
        r = subprocess.run(command, stdout=subprocess.PIPE, text=True)
        job_id = r.stdout.split(" ")[-2] if r.stdout else ""
        msg = r.stdout
        if not job_id:
            msg += "(submit error)"
            self._logger.error(f"submit error: {r.stdout}")
        response = OutputModel(status=r.returncode, msg=msg, job_id=job_id)
        return response

    async def execute_single_job(self) -> None:
        """シングルジョブの実行"""
        # wandbログイン
        wandb.login(key=self.wandb_apikey)
        expt_size_dict = {"project": self.project_name}
        if self.group_name:
            expt_size_dict["group"] = self.group_name
        if self.jobtype_name:
            expt_size_dict["job_type"] = self.jobtype_name
        # flow logicの取得
        download_path = str(Path(settings.BASE_DIR_PATH) / Path("dl_logics"))
        run = wandb.init(**expt_size_dict, name="fetch-flow-logic")
        fl_artifact = run.use_artifact(self.flow_logic_name)
        fl_artifact.download(root=download_path)
        run.finish()
        flow_logic: BaseFlowLogic = import_module(
            f"dl_logics.{self.flow_logic_name.split(':')[0]}"
        ).MyFlowLogic(self.cfg)

        # タスクの入力を取得
        task_inputs = await flow_logic.task_scheduler()
        print("Successfuly get task inputs")
        # タスクを実行
        task_results = []
        with concurrent.futures.ProcessPoolExecutor() as executor:
            result = [
                executor.submit(flow_logic.run_task, **dict(**param, **self.params))
                for param in task_inputs
            ]
            for result in concurrent.futures.as_completed(result):
                task_results.append(result.result())
        print("Successfuly complete tasks")
        # ジョブの結果をwandbに出力
        await flow_logic.create_result(task_results)
        print("Successfuly save results")
