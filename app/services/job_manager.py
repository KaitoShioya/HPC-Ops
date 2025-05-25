import logging
import subprocess


from schema.monitor_job_schema import JobStatusModel


class JobManager:
    def __init__(self, job_id: str) -> None:
        self._logger = logging.getLogger("uvicorn")
        if isinstance(job_id, str):
            self.job_id = job_id
        else:
            self._logger.error("JobItem field is invalid.")
            raise ValueError("JobItem field is invalid.")

    def get_job_stats(self) -> JobStatusModel:
        """ジョブの情報を取得.

        Returns:
            JobStatusModel: ジョブの状態値を持つオブジェクト.
        """
        self._logger.info("Getting job status.")
        if not self.job_id:
            return JobStatusModel(job_id=self.job_id, status=-1, msg="job_id is empty")

        command = ["pjstat"]
        r = subprocess.run(command, stdout=subprocess.PIPE, text=True)
        if self.job_id in r.stdout:
            row_num = r.stdout.split(self.job_id)[0].count("\n")
            stats_cols = r.stdout.split("\n")[0]
            stats = r.stdout.split("\n")[row_num]
        else:
            command = ["pjstat", "-H", self.job_id]

            self._logger.info(f"command: {command}")
            r = subprocess.run(command, stdout=subprocess.PIPE, text=True)
            if not r.stdout:
                self._logger.error(f"command {command} is exited {r.returncode}")
                self._logger.info("Maybe job_id does not exist in running jobs.")
                return JobStatusModel(
                    job_id=self.job_id,
                    status=r.returncode,
                    msg="maybe job_id doen not exist in running jobs.",
                )

        stats_cols = r.stdout.split("\n")[0]
        stats = r.stdout.split("\n")[1]
        name_idx = len(stats_cols.split("JOB_NAME")[0])
        md_idx = len(stats_cols.split("MD")[0])
        st_idx = len(stats_cols.split("ST")[0])
        user_idx = len(stats_cols.split("USER")[0])
        start_date_idx = len(stats_cols.split("START_DATE")[0])
        elapse_idx = len(stats_cols.split("ELAPSE_LIM")[0])
        node_req_idx = len(stats_cols.split("NODE_REQUIRE")[0])
        vnode_idx = len(stats_cols.split("VNODE")[0])
        core_idx = len(stats_cols.split("CORE")[0])
        v_mem_idx = len(stats_cols.split("V_MEM")[0])

        job_id = stats.split(" ")[0]
        job_name = stats[name_idx:md_idx].replace(" ", "")
        job_status = stats[st_idx:user_idx].replace(" ", "")
        start_date = stats[start_date_idx:][:14]
        elapse_lim = stats[elapse_idx:node_req_idx].replace(" ", "")
        node_require = stats[node_req_idx:vnode_idx].replace(" ", "")
        vnode = stats[vnode_idx:core_idx].replace(" ", "")
        core = stats[core_idx:v_mem_idx].replace(" ", "")
        v_mem = stats[v_mem_idx:]

        job_status_model = JobStatusModel(
            job_id=job_id,
            status=r.returncode,
            msg=r.stdout,
            job_name=job_name,
            job_status=job_status,
            start_date=start_date,
            elapse_lim=elapse_lim,
            node_require=node_require,
            vnode=vnode,
            core=core,
            v_mem=v_mem,
        )
        return job_status_model

    def delete_job(self) -> JobStatusModel:
        """ "実行中のジョブを削除する

        Returns:
            JobStatusModel: ジョブの状態値を持つオブジェクト.
        """
        before_del_status = self.get_job_stats()
        if before_del_status.job_status == "EXT":
            self._logger.info(f"job {self.job_id} already finished or does not exits.")
            return before_del_status

        command = ["pjdel", self.job_id]
        r = subprocess.run(command, stdout=subprocess.PIPE, text=True)
        res_status = r.returncode
        res_msg = (
            r.stdout
            if r.stdout
            else f"job {self.job_id} already finished or does not exits."
        )
        after_del_status = self.get_job_stats()
        job_status_after_del_model = JobStatusModel(
            job_id=after_del_status.job_id,
            status=res_status,
            msg=res_msg,
            job_name=after_del_status.job_name,
            job_status=after_del_status.job_status,
            start_date=after_del_status.start_date,
            elapse_lim=after_del_status.elapse_lim,
            node_require=after_del_status.node_require,
            vnode=after_del_status.vnode,
            core=after_del_status.core,
            v_mem=after_del_status.v_mem,
        )
        return job_status_after_del_model
