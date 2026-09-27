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

## Этап 2. Удалённый вызов процедур на основе TCP

Сервер (`src/server.py`) предоставляет удалённый вызов всех 10 функций
модели. Клиент (`src/client.py`) — класс `RpcClient`, имена методов
которого совпадают с именами функций модели.

### Формат сообщений (таблица 16)

Порядок байт — от старшего к младшему (big-endian).

| Структура | Поле | Смещение | Размер |
|-----------|------|----------|--------|
| Запрос | размер тела запроса | 0 байт | 4 байта |
| Запрос | код операции | 4 байта | 2 байта |
| Запрос | тело в формате JSON | 6 байт | определяется запросом |
| Ответ | размер тела ответа | 0 байт | 3 байта |
| Ответ | код операции | 3 байта | 1 байт |
| Ответ | тело в формате JSON | 4 байта | определяется ответом |

Тело запроса — JSON-объект с именованными аргументами функции.
В успешном ответе код операции совпадает с кодом запроса, в теле —
результат (записи передаются объектами с именами полей). При ошибке
код операции равен `0`, тело — `{"type": "...", "message": "..."}`;
клиент заново возбуждает `TypeError`, `KeyError` или `ValueError`,
остальные ошибки — как `RpcError`.

| Код | Функция | Код | Функция |
|-----|---------|-----|---------|
| 1 | `create_agent` | 6 | `get_task` |
| 2 | `get_agents` | 7 | `create_feedback` |
| 3 | `get_agent` | 8 | `get_feedbacks` |
| 4 | `create_task` | 9 | `get_feedback` |
| 5 | `get_tasks` | 10 | `get_recent_agent_tasks` |

### Журнал

Все ответы сервера записываются в файл `journal.log` в рабочем каталоге
сервера: время, адрес клиента, код операции, размер и тело ответа.

```
2026-09-27 18:45:36,866 127.0.0.1:53727 code=1 size=51 body={"key": 1, "time": 1790523936, "platform": "linux"}
2026-09-27 18:45:36,871 127.0.0.1:53727 code=0 size=69 body={"type": "KeyError", "message": "Agent с key=100 не найден"}
```

### Настройки

Адрес сервера задаётся позиционными аргументами `host` и `port`
(по умолчанию `127.0.0.1` и `9016`) и у сервера, и у клиента.

## Сборка и запуск

Требуется Python 3.10 или новее, внешние зависимости не нужны
(для проверки стиля — `flake8`).

| Действие | Windows | Linux / macOS |
|----------|---------|---------------|
| REPL | `run.bat repl` | `./run.sh repl` |
| Сервер RPC | `run.bat server [host] [port]` | `./run.sh server [host] [port]` |
| Демонстрация клиента | `run.bat client [host] [port]` | `./run.sh client [host] [port]` |
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

### Клиент RPC

Сначала запускается сервер (`run.bat server`), затем в другом терминале —
демонстрация всех функций (`run.bat client`). Использование в коде:

```python
from client import RpcClient

with RpcClient("127.0.0.1", 9016) as rpc:
    agent = rpc.create_agent("linux")
    rpc.create_task(agent["key"], argument="--fast", description="сборка")
    print(rpc.get_recent_agent_tasks())
    # [('linux', '--fast', 'сборка')]
```

## Структура

```
src/
  model.py      модель слоя доступа к данным
  repl.py       интерактивный режим
  protocol.py   бинарный протокол RPC
  server.py     сервер RPC с журналом ответов
  client.py     клиент RPC и демонстрация
tests/
  test_model.py тесты модели и REPL
  test_rpc.py   тесты протокола, сервера и клиента
run.bat, run.sh скрипты запуска
```
