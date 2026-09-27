"""Сервер удалённого вызова процедур модели слоя доступа к данным.

Все ответы сервера журналируются в файл journal.log.

Запуск: ``python src/server.py [host] [port]``.
"""

import logging
import socketserver
import threading

import model
import protocol

JOURNAL_FILE = "journal.log"

logger = logging.getLogger("rpc.journal")
_model_lock = threading.Lock()


def setup_journal(path: str = JOURNAL_FILE) -> None:
    """Направить записи журнала ответов в файл."""
    handler = logging.FileHandler(path, encoding=protocol.ENCODING)
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def to_json(value: object) -> object:
    """Преобразовать результат модели в JSON-совместимое значение."""
    if hasattr(value, "_asdict"):
        return value._asdict()
    if isinstance(value, (list, tuple)):
        return [to_json(item) for item in value]
    return value


def _error(error: Exception) -> tuple[int, dict]:
    """Сформировать код и тело ответа с ошибкой."""
    message = str(error.args[0]) if error.args else str(error)
    return protocol.ERROR_CODE, {
        "type": type(error).__name__, "message": message,
    }


def dispatch(code: int, body: object) -> tuple[int, object]:
    """Выполнить операцию модели и вернуть код и тело ответа."""
    if code not in protocol.NAMES:
        return _error(ValueError(f"неизвестный код операции {code}"))
    if not isinstance(body, dict):
        return _error(TypeError("тело запроса должно быть объектом JSON"))
    func = getattr(model, protocol.NAMES[code])
    try:
        with _model_lock:
            result = func(**body)
    except (TypeError, KeyError, ValueError) as error:
        return _error(error)
    return code, to_json(result)


class RpcHandler(socketserver.BaseRequestHandler):
    """Обработчик соединения: принимает запросы, пока клиент подключён."""

    def handle(self) -> None:
        """Цикл чтения запросов и отправки ответов."""
        client = "%s:%d" % self.client_address
        while True:
            try:
                code, body = protocol.read_request(self.request)
                code, body = dispatch(code, body)
            except protocol.ConnectionClosed:
                break
            except protocol.ProtocolError as error:
                code, body = _error(error)
            response = protocol.encode_response(code, body)
            self.request.sendall(response)
            logger.info("%s code=%d size=%d body=%s", client, code,
                        len(response) - protocol.RESPONSE_HEADER_LEN,
                        response[protocol.RESPONSE_HEADER_LEN:]
                        .decode(protocol.ENCODING))


class RpcServer(socketserver.ThreadingTCPServer):
    """Многопоточный TCP-сервер RPC."""

    allow_reuse_address = True
    daemon_threads = True


def main() -> None:
    """Запустить сервер на адресе из аргументов командной строки."""
    host, port = protocol.parse_address(__doc__)
    setup_journal()
    with RpcServer((host, port), RpcHandler) as server:
        print(f"RPC-сервер слушает {host}:{port}, журнал: {JOURNAL_FILE}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("Сервер остановлен")


if __name__ == "__main__":
    main()
