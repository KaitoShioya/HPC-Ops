import pickle
from pathlib import Path
from typing import Any, List, Dict, Callable

import numpy as np
import pandas as pd
import optuna
import wandb
from sklearn.datasets import fetch_openml
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import KFold

from app.core.base_flow_logic import BaseFlowLogic
from app.utils.config import settings


class MyFlowLogic(BaseFlowLogic):
    def __init__(self, cfg):
        super().__init__(cfg)
        self.wandb_key = settings.WANDB_APIKEY

    def objective_vr(self, X: pd.DataFrame, y: np.ndarray) -> Callable:
        def objective(trial):
            clf_name = trial.suggest_categorical(*self.cfg["params"]["clf"])
            # clf_name の値によってハイパーパラメータを分岐させる
            if clf_name == "RF":
                rf_max_depth = trial.suggest_int(*self.cfg["params"]["rf_max_depth"])
                rf_min_samples_split = trial.suggest_float(
                    *self.cfg["params"]["rf_min_samples_split"]
                )
                gb_max_depth = None
                gb_min_samples_split = None
                clf = RandomForestClassifier(
                    max_depth=rf_max_depth,
                    min_samples_split=rf_min_samples_split,
                )
            else:
                rf_max_depth = None
                rf_min_samples_split = None
                gb_max_depth = trial.suggest_int(*self.cfg["params"]["gb_max_depth"])
                gb_min_samples_split = trial.suggest_float(
                    *self.cfg["params"]["gb_min_samples_split"]
                )
                clf = GradientBoostingClassifier(
                    max_depth=gb_max_depth,
                    min_samples_split=gb_min_samples_split,
                )
            expt_log = {
                "rf_max_depth": rf_max_depth,
                "rf_min_samples_split": rf_min_samples_split,
                "gb_max_depth": gb_max_depth,
                "gb_min_samples_split": gb_min_samples_split,
            }
            acc_list = []
            kfold_indicies = list(KFold(n_splits=3).split(X))
            for train_idx, val_idx in kfold_indicies:
                X_train, y_train = X.loc[train_idx], y[train_idx]
                X_val, y_val = X.loc[val_idx], y[val_idx]
                clf.fit(X_train, y_train)
                y_pred = clf.predict(X_val)
                # print(clf.feature_importances_)
                acc_list.append(accuracy_score(y_val, y_pred))
            expt_log = dict(
                **expt_log,
                **{f"fold{i + 1} Acc": acc_list[i] for i in range(len(acc_list))},
            )
            accuracy = np.mean(acc_list)
            expt_log["Acc"] = accuracy
            if hasattr(self, "run"):
                self.run.log(expt_log, step=trial.number)
            return accuracy

        return objective

    async def task_scheduler(self) -> List[Dict[str, Any]]:
        """Job内で実行するタスクへの入力を作成.

        Returns:
            List[Dict[str, Any]]: 1タスクの入力をDictとした要素を持つリスト.
        """
        # data = fetch_openml(name="adult")
        download_path = str(Path(settings.BASE_DIR_PATH) / Path("data"))
        run = wandb.init(
            project=self.cfg["project"],
            group=self.cfg["group"],
            job_type=self.cfg["jobtype"],
            name="fetch-dataset",
        )
        artifact = run.use_artifact(self.cfg["params"]["dataset"])
        artifact_dir = artifact.download(root=download_path)
        download_path = str(
            Path(download_path)
            / Path(self.cfg["params"]["dataset"].split(":")[0] + ".pkl")
        )
        with open(download_path, "rb") as f:
            data = pickle.load(f)

        X = pd.get_dummies(data["data"])
        y = np.array([1 if d == ">50K" else 0 for d in data["target"]])
        run.finish()
        return [{"X": X, "y": y}]

    def run_task(self, **kwargs) -> Any:
        """Job内で実行するタスクの内容を記述.

        Args:
            **kwargs: task_schedulerの出力リスト内のtupleが渡される.

        Returns:
            Any: タスク実行結果. create_resultへの入力となる.
        """
        self.run = wandb.init(
            project=self.cfg["project"],
            group=self.cfg["group"],
            job_type=self.cfg["jobtype"],
            name="run-tasks",
            config=self.cfg,
        )
        study_name = self.cfg["project"]
        if self.cfg["group"]:
            study_name += "-" + self.cfg["group"]
        if self.cfg["jobtype"]:
            study_name += "-" + self.cfg["jobtype"]
        study_name += f"-{self.cfg['flow_logic']}-{self.cfg['params']['dataset']}"
        study = optuna.create_study(
            direction="maximize",
            study_name=study_name,
        )
        study.optimize(self.objective_vr(kwargs["X"], kwargs["y"]), n_trials=100)

        return study

    async def create_result(self, result_set: list[Any]) -> None:
        """Job内でタスク実行後にwandbに出力する.

        Args:
            List[Any]: run_taskの出力をまとめたものが渡される.
        """
        # https://optuna.readthedocs.io/en/stable/tutorial/10_key_features/005_visualization.html#visualization
        self.run = wandb.init(
            project=self.cfg["project"],
            group=self.cfg["group"],
            job_type=self.cfg["jobtype"],
            name="create-result",
            config=self.cfg,
        )
        study = result_set[0]
        importance_fig = optuna.visualization.plot_param_importances(
            study=study,
            params=["gb_max_depth", "gb_min_samples_split"],
        )
        contour_fig = optuna.visualization.plot_contour(
            study=study,
            params=["gb_max_depth", "gb_min_samples_split"],
        )
        self.run.log(
            {
                "importance plot": wandb.Plotly(importance_fig),
                "contour plot": wandb.Plotly(contour_fig),
            }
        )
        self.run.finish()

        return None
