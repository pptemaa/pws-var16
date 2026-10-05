"""Небольшие проверки модели: записи варианта 16 являются кортежами."""

import unittest

import model


class ModelTests(unittest.TestCase):
    def setUp(self):
        model.reset()

    def test_records_are_tuples(self):
        agent = model.create_agent("linux", 1000)
        task = model.create_task(agent[0], "-v", time=1000)
        feedback = model.create_feedback(task[0], status="done", time=1000)
        self.assertEqual(agent, (1, 1000, "linux"))
        self.assertIsInstance(task, tuple)
        self.assertIsInstance(feedback, tuple)

    def test_join(self):
        agent = model.create_agent("linux", 1000)
        model.create_task(agent[0], "-v", "build", time=1000)
        self.assertEqual(model.get_recent_agent_tasks(1000),
                         [("linux", "-v", "build")])


if __name__ == "__main__":
    unittest.main()
