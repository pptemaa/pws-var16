"""Модель слоя доступа к данным.

Сущности соответствуют ER-диаграмме варианта 16: Agent, Task, Feedback.
Записи таблиц хранятся в памяти в виде именованных кортежей, таблицы
представлены словарями вида ``{key: запись}``.
"""

from time import time as unix_time
from typing import NamedTuple

SECONDS_IN_MINUTE = 60
RECENT_MINUTES = 7
RECENT_WINDOW = RECENT_MINUTES * SECONDS_IN_MINUTE


class Agent(NamedTuple):
    """Запись таблицы Agent."""

    key: int
    time: int
    platform: str


class Task(NamedTuple):
    """Запись таблицы Task. Поле agent ссылается на Agent.key."""

    key: int
    time: int
    argument: str
    agent: int
    description: str
    tags: str
    processed: int
    launched: int


class Feedback(NamedTuple):
    """Запись таблицы Feedback. Поле task ссылается на Task.key."""

    key: int
    time: int
    result: str
    status: str
    failure: str
    task: int
    cache_hit: int
    duration: int


_agents: dict[int, Agent] = {}
_tasks: dict[int, Task] = {}
_feedbacks: dict[int, Feedback] = {}
_last_keys: dict[str, int] = {"agent": 0, "task": 0, "feedback": 0}


def reset() -> None:
    """Очистить все таблицы и сбросить счётчики ключей."""
    _agents.clear()
    _tasks.clear()
    _feedbacks.clear()
    for table in _last_keys:
        _last_keys[table] = 0


def _next_key(table: str) -> int:
    """Выдать следующий свободный ключ для таблицы."""
    _last_keys[table] += 1
    return _last_keys[table]


def _now() -> int:
    """Текущее время в секундах (Unix time)."""
    return int(unix_time())


def _check_str(name: str, value: object) -> None:
    """Проверить, что значение поля является строкой."""
    if not isinstance(value, str):
        raise TypeError(f"поле {name} должно быть строкой (str)")


def _check_int(name: str, value: object) -> None:
    """Проверить, что значение поля является целым числом."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"поле {name} должно быть целым числом (int)")


def _resolve_time(value: int | None) -> int:
    """Вернуть переданное время или текущее, если оно не задано."""
    if value is None:
        return _now()
    _check_int("time", value)
    return value


def _get(table: dict, name: str, key: object):
    """Найти запись в таблице по ключу или выбросить KeyError."""
    _check_int("key", key)
    if key not in table:
        raise KeyError(f"{name} с key={key} не найден")
    return table[key]


def create_agent(platform: str, time: int | None = None) -> Agent:
    """Создать запись Agent и вернуть её."""
    _check_str("platform", platform)
    record = Agent(_next_key("agent"), _resolve_time(time), platform)
    _agents[record.key] = record
    return record


def get_agents() -> list[Agent]:
    """Получить все записи Agent."""
    return list(_agents.values())


def get_agent(key: int) -> Agent:
    """Получить запись Agent по идентификатору."""
    return _get(_agents, "Agent", key)


def create_task(
    agent: int,
    argument: str = "",
    description: str = "",
    tags: str = "",
    processed: int = 0,
    launched: int = 0,
    time: int | None = None,
) -> Task:
    """Создать запись Task для существующего Agent и вернуть её."""
    get_agent(agent)
    for name, value in (("argument", argument),
                        ("description", description), ("tags", tags)):
        _check_str(name, value)
    _check_int("processed", processed)
    _check_int("launched", launched)
    record = Task(_next_key("task"), _resolve_time(time), argument, agent,
                  description, tags, processed, launched)
    _tasks[record.key] = record
    return record


def get_tasks() -> list[Task]:
    """Получить все записи Task."""
    return list(_tasks.values())


def get_task(key: int) -> Task:
    """Получить запись Task по идентификатору."""
    return _get(_tasks, "Task", key)


def create_feedback(
    task: int,
    result: str = "",
    status: str = "",
    failure: str = "",
    cache_hit: int = 0,
    duration: int = 0,
    time: int | None = None,
) -> Feedback:
    """Создать запись Feedback для существующего Task и вернуть её."""
    get_task(task)
    for name, value in (("result", result), ("status", status),
                        ("failure", failure)):
        _check_str(name, value)
    _check_int("cache_hit", cache_hit)
    _check_int("duration", duration)
    record = Feedback(_next_key("feedback"), _resolve_time(time), result,
                      status, failure, task, cache_hit, duration)
    _feedbacks[record.key] = record
    return record


def get_feedbacks() -> list[Feedback]:
    """Получить все записи Feedback."""
    return list(_feedbacks.values())


def get_feedback(key: int) -> Feedback:
    """Получить запись Feedback по идентификатору."""
    return _get(_feedbacks, "Feedback", key)


def get_recent_agent_tasks(
        now: int | None = None) -> list[tuple[str, str, str]]:
    """Выборка по формуле реляционной алгебры варианта 16.

    π A.platform, T.argument, T.description (
        (σ A.time > now − 7 min (A)) ⋈ A.key = T.agent (T)
    )

    Возвращает кортежи (platform, argument, description) без повторов,
    так как проекция в реляционной алгебре даёт множество.
    """
    moment = _resolve_time(now)
    border = moment - RECENT_WINDOW
    recent = {key: a for key, a in _agents.items() if a.time > border}
    rows: list[tuple[str, str, str]] = []
    for task in _tasks.values():
        agent = recent.get(task.agent)
        if agent is None:
            continue
        row = (agent.platform, task.argument, task.description)
        if row not in rows:
            rows.append(row)
    return rows
