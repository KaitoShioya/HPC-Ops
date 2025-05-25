from typing import List

from pydantic import BaseModel, Field


class JobItems(BaseModel):
    job_ids: List[str] = Field([""], description="状態を取得するジョブIDのリスト")


class JobStatusModel(BaseModel):
    job_id: str = Field("", description="JOB_ID")
    status: int = Field(0, description="リクエスト結果のステータス")
    msg: str = Field("", description="リクエストに対するレスポンスメッセージ")
    job_name: str = Field("", description="JOB_NAME")
    job_status: str = Field(
        "",
        description="ジョブの状態('QUE': 待ち状態, 'RNA': 実行開始中, 'RUN': 実行中, 'RNO': 実行終了中, 'EXT': 終了済)",
    )
    start_date: str = Field("", description="ジョブの開始時刻")
    elapse_lim: str = Field("", description="ジョブタイムアウトまでの残り時間")
    node_require: str = Field("", description="必要ノード数")
    vnode: str = Field("", description="VNODE")
    core: str = Field("", description="コア数")
    v_mem: str = Field("", description="V_MEM")
