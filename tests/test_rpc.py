"""Тесты протокола, сервера и клиента RPC."""

import os
import socket
import tempfile
import threading
import unittest

import client
import model
import protocol
import server

NOW = 1_000_000


class ProtocolTests(unittest.TestCase):
    """Формат сообщений по таблице 16."""

    def test_request_layout(self):
        """Запрос: 4 байта размера, 2 байта кода, затем JSON."""
        data = protocol.encode_request(3, {"key": 1})
        self.assertEqual(data[:4], (10).to_bytes(4, "big"))
        self.assertEqual(data[4:6], b"\x00\x03")
        self.assertEqual(data[6:], b'{"key": 1}')

    def test_response_layout(self):
        """Ответ: 3 байта размера, 1 байт кода, затем JSON."""
        data = protocol.encode_response(10, [])
        self.assertEqual(data, b"\x00\x00\x02\x0a[]")

    def test_limits(self):
        """Код операции должен помещаться в своё поле."""
        with self.assertRaises(protocol.ProtocolError):
            protocol.encode_response(256, {})

    def test_codes(self):
        """Каждой функции модели соответствует свой код операции."""
        self.assertEqual(len(protocol.CODES), len(protocol.OPERATIONS))
        self.assertNotIn(protocol.ERROR_CODE, protocol.NAMES)
        for name in protocol.OPERATIONS:
            self.assertTrue(callable(getattr(model, name)))


class RpcTests(unittest.TestCase):
    """Вызов функций модели через настоящий TCP-сервер."""

    @classmethod
    def setUpClass(cls):
        """Запустить сервер на свободном порту и настроить журнал."""
        cls.journal_dir = tempfile.TemporaryDirectory()
        cls.journal = os.path.join(cls.journal_dir.name, "journal.log")
        server.setup_journal(cls.journal)
        cls.server = server.RpcServer(("127.0.0.1", 0), server.RpcHandler)
        cls.address = cls.server.server_address
        threading.Thread(target=cls.server.serve_forever,
                         daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        """Остановить сервер и закрыть журнал."""
        cls.server.shutdown()
        cls.server.server_close()
        for handler in list(server.logger.handlers):
            handler.close()
            server.logger.removeHandler(handler)
        cls.journal_dir.cleanup()

    def setUp(self):
        """Очистить модель и подключить клиента."""
        model.reset()
        self.client = client.RpcClient(*self.address)

    def tearDown(self):
        """Отключить клиента."""
        self.client.close()

    def test_all_functions(self):
        """Все 10 функций модели доступны удалённо."""
        rpc = self.client
        agent = rpc.create_agent("linux", time=NOW)
        self.assertEqual(agent, {"key": 1, "time": NOW, "platform": "linux"})
        self.assertEqual(rpc.get_agents(), [agent])
        self.assertEqual(rpc.get_agent(1), agent)
        task = rpc.create_task(1, argument="-v", description="d")
        self.assertEqual(rpc.get_tasks(), [task])
        self.assertEqual(rpc.get_task(1), task)
        feedback = rpc.create_feedback(1, status="done", duration=5)
        self.assertEqual(rpc.get_feedbacks(), [feedback])
        self.assertEqual(rpc.get_feedback(1), feedback)
        rows = rpc.get_recent_agent_tasks(now=NOW)
        self.assertEqual(rows, [("linux", "-v", "d")])

    def test_errors(self):
        """Ошибки модели передаются клиенту с исходным типом."""
        with self.assertRaises(KeyError):
            self.client.get_agent(1)
        with self.assertRaises(TypeError):
            self.client.create_agent(1)
        with self.assertRaises(TypeError):
            self.client.create_task(1, unknown=True)
        self.assertEqual(self.client.get_agents(), [])

    def test_bad_requests(self):
        """Неизвестный код, не-объект и не-JSON дают ответ с ошибкой."""
        with socket.create_connection(self.address) as sock:
            for request in (protocol.encode_request(99, {}),
                            protocol.encode_request(1, [1]),
                            b"\x00\x00\x00\x01\x00\x01{"):
                sock.sendall(request)
                code, body = protocol.read_response(sock)
                self.assertEqual(code, protocol.ERROR_CODE)
                self.assertIn("message", body)

    def test_journal(self):
        """Ответы сервера записываются в журнал."""
        self.client.create_agent("journal-check")
        self.client.get_agents()
        with open(self.journal, encoding="utf-8") as journal:
            self.assertIn("journal-check", journal.read())

    def test_server_error_type(self):
        """Неизвестный тип ошибки превращается в RpcError."""
        self.assertIs(client.KNOWN_ERRORS.get("OSError", client.RpcError),
                      client.RpcError)


if __name__ == "__main__":
    unittest.main()
