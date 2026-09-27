"""Тесты модели слоя доступа к данным и REPL."""

import unittest

import model
import repl

NOW = 1_000_000
OLD = NOW - model.RECENT_WINDOW
FRESH = OLD + 1


class AgentTests(unittest.TestCase):
    """Операции над таблицей Agent."""

    def setUp(self):
        """Очистить таблицы перед каждым тестом."""
        model.reset()

    def test_create_and_get(self):
        """Созданная запись является кортежем и доступна по ключу."""
        agent = model.create_agent("linux", time=NOW)
        self.assertIsInstance(agent, tuple)
        self.assertEqual(agent, (1, NOW, "linux"))
        self.assertEqual(model.get_agent(1), agent)
        self.assertEqual(model.get_agents(), [agent])

    def test_keys_are_unique(self):
        """Ключи выдаются последовательно."""
        first = model.create_agent("linux")
        second = model.create_agent("windows")
        self.assertEqual((first.key, second.key), (1, 2))

    def test_errors(self):
        """Некорректные данные и отсутствующий ключ дают ошибку."""
        with self.assertRaises(TypeError):
            model.create_agent(42)
        with self.assertRaises(TypeError):
            model.create_agent("linux", time="now")
        with self.assertRaises(KeyError):
            model.get_agent(1)
        with self.assertRaises(TypeError):
            model.get_agent("1")


class TaskFeedbackTests(unittest.TestCase):
    """Операции над таблицами Task и Feedback."""

    def setUp(self):
        """Создать агента, к которому привязываются задачи."""
        model.reset()
        model.create_agent("linux", time=NOW)

    def test_task(self):
        """Задача создаётся только для существующего агента."""
        task = model.create_task(1, "-v", "сборка", "ci", time=NOW)
        self.assertEqual(task, (1, NOW, "-v", 1, "сборка", "ci", 0, 0))
        self.assertEqual(model.get_task(1), task)
        self.assertEqual(model.get_tasks(), [task])
        with self.assertRaises(KeyError):
            model.create_task(99)
        with self.assertRaises(TypeError):
            model.create_task(1, processed="yes")

    def test_feedback(self):
        """Отзыв создаётся только для существующей задачи."""
        model.create_task(1)
        feedback = model.create_feedback(1, "ok", "done", "", 1, 30, NOW)
        self.assertEqual(feedback, (1, NOW, "ok", "done", "", 1, 1, 30))
        self.assertEqual(model.get_feedback(1), feedback)
        self.assertEqual(model.get_feedbacks(), [feedback])
        with self.assertRaises(KeyError):
            model.create_feedback(5)
        with self.assertRaises(TypeError):
            model.create_feedback(1, status=None)


class RecentAgentTasksTests(unittest.TestCase):
    """Выборка по формуле реляционной алгебры."""

    def test_join(self):
        """В выборку попадают только задачи недавних агентов."""
        model.reset()
        model.create_agent("fresh", time=FRESH)
        model.create_agent("old", time=OLD)
        model.create_agent("idle", time=NOW)
        model.create_task(1, "a", "первая")
        model.create_task(1, "a", "первая")
        model.create_task(2, "b", "вторая")
        rows = model.get_recent_agent_tasks(now=NOW)
        self.assertEqual(rows, [("fresh", "a", "первая")])


class ReplTests(unittest.TestCase):
    """Разбор и выполнение команд REPL."""

    def setUp(self):
        """Очистить таблицы перед каждым тестом."""
        model.reset()

    def test_execute(self):
        """Команды выполняют функции модели."""
        self.assertIn("linux", repl.execute("create_agent linux time=5"))
        self.assertIn("time=5", repl.execute("get_agent 1"))
        self.assertIn("'a b'", repl.execute('create_task 1 "a b"'))
        self.assertEqual(repl.execute("get_feedbacks"), "(пусто)")
        self.assertEqual(repl.execute(""), "")
        self.assertIn("create_agent", repl.execute("help"))

    def test_errors(self):
        """Ошибочные команды приводят к исключениям."""
        with self.assertRaises(ValueError):
            repl.execute("unknown")
        with self.assertRaises(ValueError):
            repl.execute("get_agent x")
        with self.assertRaises(ValueError):
            repl.execute("get_agent 1 2")
        with self.assertRaises(KeyError):
            repl.execute("get_agent 1")


if __name__ == "__main__":
    unittest.main()
