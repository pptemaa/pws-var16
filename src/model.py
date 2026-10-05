"""Модель данных варианта 16. Записи хранятся как обычные кортежи."""

from time import time as clock

WINDOW = 7 * 60
agents, tasks, feedbacks = {}, {}, {}


def reset():
    """Очистить хранилище (нужно тестам)."""
    agents.clear()
    tasks.clear()
    feedbacks.clear()


def create_agent(platform, time=None):
    record = (len(agents) + 1, int(clock()) if time is None else time,
              platform)
    agents[record[0]] = record
    return record


def get_agents():
    return list(agents.values())


def get_agent(key):
    return agents[key]


def create_task(agent, argument="", description="", tags="", processed=0,
                launched=0, time=None):
    get_agent(agent)
    record = (len(tasks) + 1, int(clock()) if time is None else time,
              argument, agent, description, tags, processed, launched)
    tasks[record[0]] = record
    return record


def get_tasks():
    return list(tasks.values())


def get_task(key):
    return tasks[key]


def create_feedback(task, result="", status="", failure="", cache_hit=0,
                    duration=0, time=None):
    get_task(task)
    record = (len(feedbacks) + 1,
              int(clock()) if time is None else time, result, status,
              failure, task, cache_hit, duration)
    feedbacks[record[0]] = record
    return record


def get_feedbacks():
    return list(feedbacks.values())


def get_feedback(key):
    return feedbacks[key]


def get_recent_agent_tasks(now=None):
    now = int(clock()) if now is None else now
    return list({(agents[task[3]][2], task[2], task[4])
                 for task in tasks.values()
                 if agents[task[3]][1] > now - WINDOW})
