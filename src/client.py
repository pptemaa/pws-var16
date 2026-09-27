"""Клиент RPC и демонстрация удалённого вызова всех функций модели.

Запуск демонстрации (сервер должен быть запущен):
``python src/client.py [host] [port]``.
"""

import socket

import protocol

KNOWN_ERRORS = {
    error.__name__: error for error in (TypeError, KeyError, ValueError)
}


class RpcError(Exception):
    """Ошибка, возвращённая сервером RPC."""


class RpcClient:
    """Клиент RPC: имена методов совпадают с функциями модели."""

    def __init__(self, host: str = protocol.DEFAULT_HOST,
                 port: int = protocol.DEFAULT_PORT) -> None:
        """Подключиться к серверу RPC."""
        self._sock = socket.create_connection((host, port))

    def close(self) -> None:
        """Закрыть соединение с сервером."""
        self._sock.close()

    def __enter__(self) -> "RpcClient":
        """Вернуть клиент для использования в блоке with."""
        return self

    def __exit__(self, *exc_info) -> None:
        """Закрыть соединение при выходе из блока with."""
        self.close()

    def call(self, name: str, **kwargs) -> object:
        """Вызвать удалённую функцию по имени и вернуть результат."""
        self._sock.sendall(
            protocol.encode_request(protocol.CODES[name], kwargs))
        code, body = protocol.read_response(self._sock)
        if code == protocol.ERROR_CODE:
            error = KNOWN_ERRORS.get(body.get("type"), RpcError)
            raise error(body.get("message"))
        return body

    def create_agent(self, platform: str, time: int | None = None) -> dict:
        """Создать запись Agent."""
        return self.call("create_agent", platform=platform, time=time)

    def get_agents(self) -> list[dict]:
        """Получить все записи Agent."""
        return self.call("get_agents")

    def get_agent(self, key: int) -> dict:
        """Получить запись Agent по идентификатору."""
        return self.call("get_agent", key=key)

    def create_task(self, agent: int, **fields) -> dict:
        """Создать запись Task.

        Необязательные поля: argument, description, tags, processed,
        launched, time.
        """
        return self.call("create_task", agent=agent, **fields)

    def get_tasks(self) -> list[dict]:
        """Получить все записи Task."""
        return self.call("get_tasks")

    def get_task(self, key: int) -> dict:
        """Получить запись Task по идентификатору."""
        return self.call("get_task", key=key)

    def create_feedback(self, task: int, **fields) -> dict:
        """Создать запись Feedback.

        Необязательные поля: result, status, failure, cache_hit,
        duration, time.
        """
        return self.call("create_feedback", task=task, **fields)

    def get_feedbacks(self) -> list[dict]:
        """Получить все записи Feedback."""
        return self.call("get_feedbacks")

    def get_feedback(self, key: int) -> dict:
        """Получить запись Feedback по идентификатору."""
        return self.call("get_feedback", key=key)

    def get_recent_agent_tasks(
            self, now: int | None = None) -> list[tuple[str, str, str]]:
        """Выборка (platform, argument, description) за последние 7 мин."""
        rows = self.call("get_recent_agent_tasks", now=now)
        return [tuple(row) for row in rows]


def show(title: str, action) -> None:
    """Выполнить вызов клиента и напечатать результат или ошибку."""
    print(f"> {title}")
    try:
        print(f"  {action()}")
    except (TypeError, KeyError, ValueError, RpcError) as error:
        message = error.args[0] if error.args else error
        print(f"  Ошибка ({type(error).__name__}): {message}")


def demo(client: RpcClient) -> None:
    """Продемонстрировать вызов всех функций модели через RPC."""
    agent = client.create_agent("linux")
    old = client.create_agent("windows", time=agent["time"] - 600)
    show("create_agent('linux')", lambda: agent)
    show("create_agent('windows', time=now-10min)", lambda: old)
    show("get_agents()", client.get_agents)
    show("get_agent(1)", lambda: client.get_agent(1))
    show("create_task(1, ...)", lambda: client.create_task(
        1, argument="--fast", description="сборка", tags="ci"))
    show("create_task(2, ...)", lambda: client.create_task(
        2, argument="--full", description="старая задача"))
    show("get_tasks()", client.get_tasks)
    show("get_task(2)", lambda: client.get_task(2))
    show("create_feedback(1, ...)", lambda: client.create_feedback(
        1, result="ok", status="done", cache_hit=1, duration=250))
    show("get_feedbacks()", client.get_feedbacks)
    show("get_feedback(1)", lambda: client.get_feedback(1))
    show("get_recent_agent_tasks()", client.get_recent_agent_tasks)
    print("--- обработка ошибок ---")
    show("get_agent(100)", lambda: client.get_agent(100))
    show("get_task('1')", lambda: client.get_task("1"))
    show("create_task(100)", lambda: client.create_task(100))
    show("create_feedback(1, duration='x')",
         lambda: client.create_feedback(1, duration="x"))
    show("create_agent(platform=42)", lambda: client.create_agent(42))
    show("create_task(1, color='red')",
         lambda: client.create_task(1, color="red"))


def main() -> None:
    """Подключиться к серверу и запустить демонстрацию."""
    host, port = protocol.parse_address(__doc__)
    with RpcClient(host, port) as client:
        demo(client)


if __name__ == "__main__":
    main()
