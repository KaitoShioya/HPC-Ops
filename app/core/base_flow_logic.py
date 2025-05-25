from abc import ABCMeta, abstractmethod
from typing import Any, List, Dict


class BaseFlowLogic(metaclass=ABCMeta):
    def __init__(self, cfg) -> None:
        self.cfg = cfg

    @abstractmethod
    async def task_scheduler(self) -> List[Dict[str, Any]]:
        """Job内で実行するタスクへの入力を作成.

        Returns:
            List[Dict[Any]]: 1タスクの入力をDictとした要素を持つリスト.
        """
        return NotImplementedError

    @abstractmethod
    def run_task(self, **kwargs) -> Any:
        """Job内で実行するタスクの内容を記述.

        Args:
            **kwargs: task_schedulerの出力リスト内のDictが渡される.

        Returns:
            Any: タスク実行結果. create_resultへの入力となる.
        """
        return NotImplementedError

    @abstractmethod
    async def create_result(self, result_set: List[Any]) -> None:
        """Job内でタスク実行後にwandbに出力する.

        Args:
            List[Any]: run_taskの出力をまとめたものが渡される.
        """
        return NotImplementedError
