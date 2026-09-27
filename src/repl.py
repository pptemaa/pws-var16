"""Интерактивный режим (REPL) для модели слоя доступа к данным.

Команда состоит из имени функции модели и её аргументов. Аргументы
передаются позиционно или в виде ``имя=значение``, строки с пробелами
заключаются в кавычки::

    create_agent linux
    create_task 1 "--fast" "описание" tags=ci
    get_recent_agent_tasks
"""

import inspect
import shlex

import model

INT_PARAMS = {
    "key", "time", "now", "agent", "task",
    "processed", "launched", "cache_hit", "duration",
}

COMMANDS = {
    func.__name__: func for func in (
        model.create_agent, model.get_agents, model.get_agent,
        model.create_task, model.get_tasks, model.get_task,
        model.create_feedback, model.get_feedbacks, model.get_feedback,
        model.get_recent_agent_tasks,
    )
}

EXIT_COMMANDS = {"exit", "quit"}


def _convert(name: str, raw: str) -> object:
    """Привести строковый аргумент к типу параметра функции модели."""
    if name not in INT_PARAMS:
        return raw
    try:
        return int(raw)
    except ValueError:
        raise ValueError(f"аргумент {name} должен быть целым числом")


def parse_args(func, tokens: list[str]) -> dict[str, object]:
    """Сопоставить токены команды с параметрами функции модели."""
    params = list(inspect.signature(func).parameters)
    kwargs: dict[str, object] = {}
    for index, token in enumerate(tokens):
        name, sep, value = token.partition("=")
        if not sep or name not in params:
            if index >= len(params):
                raise ValueError("слишком много аргументов")
            name, value = params[index], token
        kwargs[name] = _convert(name, value)
    return kwargs


def format_result(result: object) -> str:
    """Представить результат функции модели в виде текста."""
    if isinstance(result, list):
        if not result:
            return "(пусто)"
        return "\n".join(str(item) for item in result)
    return str(result)


def show_help() -> str:
    """Сформировать справку по доступным командам."""
    lines = ["Доступные команды:"]
    for name, func in COMMANDS.items():
        signature = " ".join(inspect.signature(func).parameters)
        lines.append(f"  {name} {signature}".rstrip())
    lines.append("  help")
    lines.append("  exit")
    return "\n".join(lines)


def execute(line: str) -> str:
    """Выполнить одну строку REPL и вернуть текст ответа."""
    tokens = shlex.split(line)
    if not tokens:
        return ""
    name, args = tokens[0], tokens[1:]
    if name == "help":
        return show_help()
    if name not in COMMANDS:
        raise ValueError(f"неизвестная команда {name!r}, см. help")
    func = COMMANDS[name]
    try:
        return format_result(func(**parse_args(func, args)))
    except TypeError as error:
        raise TypeError(f"{name}: {error}") from error


def main() -> None:
    """Запустить цикл чтения и выполнения команд."""
    print("REPL модели данных (вариант 16). Введите help для справки.")
    while True:
        try:
            line = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if line in EXIT_COMMANDS:
            break
        try:
            output = execute(line)
        except (ValueError, TypeError, KeyError) as error:
            message = error.args[0] if error.args else error
            output = f"Ошибка ({type(error).__name__}): {message}"
        if output:
            print(output)


if __name__ == "__main__":
    main()
