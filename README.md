# Практическое задание 1 — Вариант 16

Прототип веб-приложения с поддержкой удалённого вызова процедур (RPC) на
основе протокола TCP. Данные хранятся только в памяти, на диск не
сохраняются. Группа ИКБО-71-24.

## Общее описание

Схема данных соответствует ER-диаграмме варианта 16:

| Сущность   | Поля                                                                 |
|------------|----------------------------------------------------------------------|
| `Agent`    | `key`, `time`, `platform`                                            |
| `Task`     | `key`, `time`, `argument`, `agent`, `description`, `tags`, `processed`, `launched` |
| `Feedback` | `key`, `time`, `result`, `status`, `failure`, `task`, `cache_hit`, `duration` |

`Task.agent` ссылается на `Agent.key`, `Feedback.task` ссылается на
`Task.key`. Каждая запись хранится в памяти как именованный кортеж
(`typing.NamedTuple`). Поле `time` — время в секундах (Unix time); если оно
не передано, подставляется текущее время. Ключ `key` выдаётся автоматически.

## Этап 1. Модель слоя доступа к данным

Модуль `src/model.py` содержит 10 функций:

| Функция | Описание |
|---------|----------|
| `create_agent(platform, time=None)` | создать запись `Agent` |
| `get_agents()` | получить все записи `Agent` |
| `get_agent(key)` | получить `Agent` по идентификатору |
| `create_task(agent, argument="", description="", tags="", processed=0, launched=0, time=None)` | создать запись `Task` для существующего агента |
| `get_tasks()` | получить все записи `Task` |
| `get_task(key)` | получить `Task` по идентификатору |
| `create_feedback(task, result="", status="", failure="", cache_hit=0, duration=0, time=None)` | создать запись `Feedback` для существующей задачи |
| `get_feedbacks()` | получить все записи `Feedback` |
| `get_feedback(key)` | получить `Feedback` по идентификатору |
| `get_recent_agent_tasks(now=None)` | выборка по формуле реляционной алгебры (см. ниже) |

Выборка `get_recent_agent_tasks` реализует формулу

```
π A.platform, T.argument, T.description ((σ A.time > now − 7 min (A)) ⋈ A.key = T.agent (T))
```

где `A` — таблица `Agent`, `T` — таблица `Task`. Результат — список
кортежей `(platform, argument, description)` без повторов.

Обработка ошибок:

- `TypeError` — значение поля имеет неверный тип;
- `KeyError` — запись с указанным ключом не найдена (в том числе при
  создании `Task` для несуществующего `Agent` и `Feedback` для
  несуществующего `Task`).

### REPL

Модуль `src/repl.py` — интерактивный режим. Команда — это имя функции
модели и её аргументы: позиционные или в виде `имя=значение`. Строки с
пробелами берутся в кавычки. `help` выводит список команд, `exit` —
выход.

## Сборка и запуск

Требуется Python 3.10 или новее, внешние зависимости не нужны
(для проверки стиля — `flake8`).

| Действие | Windows | Linux / macOS |
|----------|---------|---------------|
| REPL | `run.bat repl` | `./run.sh repl` |
| Тесты | `run.bat test` | `./run.sh test` |
| Проверка PEP 8 | `run.bat lint` | `./run.sh lint` |

## Примеры использования

```
>>> create_agent linux
Agent(key=1, time=1790523773, platform='linux')
>>> create_agent windows time=100
Agent(key=2, time=100, platform='windows')
>>> create_task 1 "--fast run" "сборка проекта" ci
Task(key=1, time=1790523773, argument='--fast run', agent=1, description='сборка проекта', tags='ci', processed=0, launched=0)
>>> create_task 2 x y
Task(key=2, time=1790523773, argument='x', agent=2, description='y', tags='', processed=0, launched=0)
>>> create_feedback 1 ok done "" 1 250
Feedback(key=1, time=1790523773, result='ok', status='done', failure='', task=1, cache_hit=1, duration=250)
>>> get_recent_agent_tasks
('linux', '--fast run', 'сборка проекта')
>>> get_agent 9
Ошибка (KeyError): Agent с key=9 не найден
>>> create_task 5
Ошибка (KeyError): Agent с key=5 не найден
>>> get_agent abc
Ошибка (ValueError): аргумент key должен быть целым числом
```

## Структура

```
src/
  model.py      модель слоя доступа к данным
  repl.py       интерактивный режим
tests/
  test_model.py тесты модели и REPL
run.bat, run.sh скрипты запуска
```
