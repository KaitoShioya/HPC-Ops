from typing import List, Optional
from pydantic import BaseModel, Field


class InputModel(BaseModel):
    node: Optional[int] = Field(
        None, description="ノード数の指定（１ノード以上の資源を使用する場合に必須）"
    )
    vnode_core: Optional[int] = Field(
        1,
        description="コア数の指定（ノードグループAで１ノード未満の資源を利用する場合に必須）",
    )
    gpu: Optional[int] = Field(
        None,
        description="GPU数の指定（ノードグループB,Cで１ノード未満の資源を利用する場合に必須）",
    )
    elapse: Optional[str] = Field(
        "01:00:00", description="ジョブの実行時間の上限を指定"
    )
    params: Optional[dict] = Field({}, description="実験に関するパラメータ設定")
    project: str = Field("hpc-ops", description="wandbのプロジェクト名")
    group: Optional[str] = Field(None, description="wandbのプロジェクトグループ")
    jobtype: Optional[str] = Field(None, description="wandbのプロジェクトジョブタイプ")
    run: Optional[str] = Field(None, description="wandbのプロジェクトラン")
    flow_logic: str = Field(
        "sample_flow_logic:latest",
        description="wandbに保存したflow logicファイルの使用バージョン",
    )


class MultiInputModel(BaseModel):
    jobs: List[InputModel] = Field([], description="投入するジョブ情報のリスト")


class OutputModel(BaseModel):
    status: int = Field(0, description="ジョブの投入処理レスポンス")
    msg: str = Field("", description="ジョブの投入処理メッセージ")
    job_id: str = Field("", description="ジョブID")
