# [HPC-Ops](https://github.com/KaitoShioya/HPC-Ops)

スーパーコンピューター玄海とwandbを用いた実験運用レポジトリ．

## クイックスタート

以下をHPC上とローカル上で行う．

1. 仮想環境としてRyeを用いてセットアップを行う．
    - https://rye.astral.sh/

2. 以下コマンドにより本レポジトリをclone

```bash
git clone git@github.com:KaitoShioya/HPC-Ops.git
```

3. ryeの環境をセットアップ

```bash
cd HPC-Ops
rye pin 3.10
rye sync
```

4. `.env`ファイルにHPCの計算資源のリソースグループとwandbのAPIキーを記述する．

5. HPC上で以下コマンドを実行
```bash
rye run python app/main.py
```

上記に加えて，wandbアカウントを作成し，APIKEYを発行する必要があります．

以上が完了後は，HPC上で以下コマンドのようにAPIサーバーをバックグラウンド実行すると，ssh接続を閉じてもバックグラウンドでサーバーが動作する．

```bash
cd HPC-Ops
screen
rye run python main/app.py
<CTRL>+<a>
<d>
```

この状態でssh接続を一度切断し，ターミナルから以下のようにsshポート転送を行うことでAPIサーバーへの接続が可能となる．

```bash
ssh -L 8000:genkai0002:8000 <Host Name>
```

## HPC-Opsによる実験管理チュートリアル

チュートリアルでは，optunaを用いたハイパーパラメータ探索の例を使って基本的なHPC-Opsの利用方法を説明します．
扱う実験内容については以下の書籍を参考にしてください．

[Optunaによるブラックボックス最適化 Chaper2 Section 3.4](https://books.google.co.jp/books/about/Optuna%E3%81%AB%E3%82%88%E3%82%8B%E3%83%96%E3%83%A9%E3%83%83%E3%82%AF%E3%83%9C%E3%83%83%E3%82%AF%E3%82%B9.html?id=geatEAAAQBAJ&source=kp_book_description&redir_esc=y)
- code: https://github.com/pfnet-research/optuna-book/blob/master/chapter2/list_2_16_optimize_rf_gb_with_conditional_search_space.py

### 必要なモジュールのインポート

```python
import aiohttp
import os
import pickle
import sys

sys.path.append("app/")

import wandb
from sklearn.datasets import fetch_openml

from app.schema.create_job_schema import InputModel

import warnings

warnings.simplefilter("ignore")
```

**実験の流れ**

1. Flow Logicの作成

2. logicファイルをwandbにアップロード

3. 利用する生データ等があればwandbにアップロード

4. ローカルからHPCに実験の実行をリクエストする．

上記を順に行うことで1つの実験が完了します．

**1. Flow Logicの作成**

- HPC-Opsでは，実験ロジックをBaseFlowLogicクラスを継承したMyFlowLogicクラスに記述し，これをHPC側から読み込むことで実験を行います．
- HPC-Opsでは，実験をその中で並列実行可能なタスクに分解して実行することで高速に実験を行います．
- MyFlowLogicでは実験の準備(task_scheduler)，実験の実行(run_task)，実験結果の集約(create_result)の3つのメソッドを実装する必要があります．
    - task_scheduler(self) -> List[Dict[str, Any]]:
        - ここでは，実験に使うデータやパラメータ等のオブジェクトを並列可能なタスクへの入力として前処理します．
        - 出力の各要素はrun_taskメソッドに入力されます．
    - run_task(self, **kwargs) -> Any:
        - ここでは，実験の実行ロジックを記述します．task_schedulerの要素である辞書を受け取り，実行結果を出力します．
        - 入力は並列実行するタスクごとに異なる値(task_scheduler出力の各要素)が与えられ，共通化されたrun_taskメソッドにより各タスクを実行します．
    - create_result(self, result_set: List[Any]) -> None:
        - ここでは，各タスクの実行結果を受け取り，実行結果から最終的な実験結果を集約します．
        - 集約結果はwandbによって管理します．

- 本チュートリアルでは，scikit-learnを使った機械学習によるタスクのハイパーパラメータ探索を扱います．
- 手順1のFlow Logicとして`flow_logics/optuna_example.py`を利用します.

**2. logicファイルをwandbにアップロード**

- `flow_logics/optuna_example.py`をwandbのArtifactsにアップロードします．
- HPC-Ops利用時の注意点として，アップロードするファイル名とArtifact名を統一する必要があります．

```python
# 実験のproject, group, jobtypeを定義する.
project = "hpc-ops-tutorial"
group = "optuna-example"
jobtype = "my-first-tutorial"

# wandbにログイン
wandb.login(key="<your wandb apikey here>")
```

```python
## wandbにoptuna_example.pyをアップロード
run = wandb.init(project=project, group=group, job_type=jobtype, name="upload-flow-logic")
logic_artifact = wandb.Artifact(name="optuna_example", type="flow logic")
logic_artifact.add_file(local_path="flow_logics/optuna_example.py")
run.log_artifact(logic_artifact)
run.finish()
```

**3. 利用する生データ等があればwandbにアップロード**

- scikit-learnのデータセットを利用するため，データを作成し，wandbにアップロードします．
- 手順4においてデータセット名をパラメータとして指定することでFlow Logic内で読み込みます．

```python
## 利用データを作成し，wandbにアップロード

# データ作成
data = fetch_openml(name="adult")
os.makedirs("data/", exist_ok=True)
with open("data/optuna-example.pkl", "wb") as f:
    pickle.dump(data, f)

# wandbにアップロード
run = wandb.init(project=project, group=group, job_type=jobtype, name="upload-dataset")
dataset_artifact = wandb.Artifact(name="optuna-example", type="dataset")
dataset_artifact.add_file(local_path="data/optuna-example.pkl")
run.log_artifact(dataset_artifact)
run.finish()
```

**4. ローカルからHPCに実験の実行をリクエストする．**

- HPCのFastAPIサーバーに対して実験ジョブの投入リクエストを行います．
- リクエストボディとして以下のようなInputModelをjsonに変換してリクエストします．

**InputModel(BaseModel):**

- node: Optional[int]
    - ノード数の指定（１ノード以上の資源を使用する場合に必須）．デフォルトは`None`．
- vnode_core: Optional[int]
    - コア数の指定（ノードグループAで１ノード未満の資源を利用する場合に必須）．デフォルトは`None`．
- gpu: Optional[int]
    - GPU数の指定（ノードグループB，Cで１ノード未満の資源を利用する場合に必須）．デフォルトは`None`．
- elapse: Optional[str]
    - ジョブの実行時間の上限を指定．デフォルトは`01:00:00`．
- params: Optional[dict]
    - 実験に関するパラメータ設定．
- project: str
    - wandbのプロジェクト名．必須．
- group: Optional[str]
    - wandbのプロジェクトグループ名．
- jobtype: Optional[str]
    - wandbのプロジェクトジョブタイプ名．
- run: Optional[str]
    - wandbのプロジェクトラン名．
- flow_logic: str
    - wandbに保存したflow logicファイルの名前と使用バージョン．デフォルトは`sample_flow_logic:latest`．

```python
base_url = "http://127.0.0.1:8000"
endpoint = "/create-job"

# リクエストボディ作成
data = InputModel(
    node=None,
    vnode_core=1,
    gpu=None,
    elapse="02:00:00",
    params={
        "dataset": "optuna-example:v0",
        "clf": ("clf", ("RF", "GB")),
        "rf_max_depth": ("rf_max_depth", 2, 32),
        "rf_min_samples_split": ("rf_min_samples_split", 0, 1),
        "gb_max_depth": ("gb_max_depth", 2, 32),
        "gb_min_samples_split": ("gb_min_samples_split", 0, 1),
    },
    project=project,
    group=group,
    jobtype=jobtype,
    flow_logic="optuna_example:v0"
).model_dump()
# HPCにリクエスト
async with aiohttp.ClientSession() as session:
    async with session.post(base_url + endpoint, json=data) as r:
        res = await r.json()
```
