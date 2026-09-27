"""Бинарный протокол RPC по таблице 16 варианта.

Запрос::

    смещение 0, 4 байта  — размер тела запроса
    смещение 4, 2 байта  — код операции
    смещение 6           — тело в формате JSON

Ответ::

    смещение 0, 3 байта  — размер тела ответа
    смещение 3, 1 байт   — код операции
    смещение 4           — тело в формате JSON

Порядок байт — от старшего к младшему (big-endian). Тело запроса —
объект с именованными аргументами функции. В ответе при успехе код
операции совпадает с кодом запроса, а тело содержит результат; при
ошибке код операции равен ERROR_CODE, а тело — объект с полями
``type`` и ``message``.
"""

import argparse
import json
import socket

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9016

BYTE_ORDER = "big"
ENCODING = "utf-8"

REQUEST_SIZE_LEN = 4
REQUEST_CODE_LEN = 2
REQUEST_HEADER_LEN = REQUEST_SIZE_LEN + REQUEST_CODE_LEN

RESPONSE_SIZE_LEN = 3
RESPONSE_CODE_LEN = 1
RESPONSE_HEADER_LEN = RESPONSE_SIZE_LEN + RESPONSE_CODE_LEN

ERROR_CODE = 0

OPERATIONS = (
    "create_agent", "get_agents", "get_agent",
    "create_task", "get_tasks", "get_task",
    "create_feedback", "get_feedbacks", "get_feedback",
    "get_recent_agent_tasks",
)
CODES = {name: code for code, name in enumerate(OPERATIONS, start=1)}
NAMES = {code: name for name, code in CODES.items()}


class ProtocolError(Exception):
    """Нарушение формата сообщения."""


class ConnectionClosed(ProtocolError):
    """Собеседник закрыл соединение."""


def _max_value(length: int) -> int:
    """Максимальное беззнаковое число, помещающееся в length байт."""
    return (1 << (8 * length)) - 1


def _pack(size_len: int, code_len: int, code: int, body: object) -> bytes:
    """Упаковать заголовок и JSON-тело в байты."""
    payload = json.dumps(body, ensure_ascii=False).encode(ENCODING)
    if len(payload) > _max_value(size_len):
        raise ProtocolError("тело сообщения слишком велико")
    if not 0 <= code <= _max_value(code_len):
        raise ProtocolError(f"недопустимый код операции {code}")
    return (len(payload).to_bytes(size_len, BYTE_ORDER)
            + code.to_bytes(code_len, BYTE_ORDER) + payload)


def encode_request(code: int, body: object) -> bytes:
    """Сформировать запрос."""
    return _pack(REQUEST_SIZE_LEN, REQUEST_CODE_LEN, code, body)


def encode_response(code: int, body: object) -> bytes:
    """Сформировать ответ."""
    return _pack(RESPONSE_SIZE_LEN, RESPONSE_CODE_LEN, code, body)


def _recv_exact(sock: socket.socket, length: int) -> bytes:
    """Прочитать из сокета ровно length байт."""
    chunks = []
    remaining = length
    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            raise ConnectionClosed("соединение закрыто")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _read(sock: socket.socket, size_len: int,
          code_len: int) -> tuple[int, object]:
    """Прочитать сообщение: вернуть код операции и разобранное тело."""
    header = _recv_exact(sock, size_len + code_len)
    size = int.from_bytes(header[:size_len], BYTE_ORDER)
    code = int.from_bytes(header[size_len:], BYTE_ORDER)
    payload = _recv_exact(sock, size)
    try:
        return code, json.loads(payload.decode(ENCODING))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProtocolError(f"тело не является JSON: {error}") from error


def read_request(sock: socket.socket) -> tuple[int, object]:
    """Прочитать запрос из сокета."""
    return _read(sock, REQUEST_SIZE_LEN, REQUEST_CODE_LEN)


def read_response(sock: socket.socket) -> tuple[int, object]:
    """Прочитать ответ из сокета."""
    return _read(sock, RESPONSE_SIZE_LEN, RESPONSE_CODE_LEN)


def parse_address(description: str) -> tuple[str, int]:
    """Прочитать адрес сервера RPC из аргументов командной строки."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("host", nargs="?", default=DEFAULT_HOST)
    parser.add_argument("port", nargs="?", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    return args.host, args.port
