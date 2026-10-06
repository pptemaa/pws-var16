"""Model-based test: every RPC method is called by a Hypothesis rule."""

import threading

from hypothesis import settings, strategies as st
from hypothesis.stateful import RuleBasedStateMachine, rule

import client
import model
import server


class RpcMachine(RuleBasedStateMachine):
    """Сравнение состояния RPC с простой моделью из списков кортежей."""

    def __init__(self):
        super().__init__()
        model.reset()
        self.server = server.RpcServer(("127.0.0.1", 0), server.RpcHandler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.rpc = client.RpcClient(*self.server.server_address)
        self.agents, self.tasks, self.feedbacks = [], [], []

    def teardown(self):
        self.rpc.close()
        self.server.shutdown()
        self.server.server_close()

    def create_agent(self, platform, moment):
        agent = (len(self.agents) + 1, moment, platform)
        assert self.rpc.create_agent(platform, moment) == list(agent)
        self.agents.append(agent)
        assert self.rpc.get_agents() == [list(item) for item in self.agents]
        assert self.rpc.get_agent(agent[0]) == list(agent)
        return agent

    def create_task(self, agent, argument, description, moment):
        task = (len(self.tasks) + 1, moment, argument, agent[0], description,
                "", 0, 0)
        result = self.rpc.create_task(agent[0], argument=argument,
                                      description=description, time=moment)
        assert result == list(task)
        self.tasks.append(task)
        assert self.rpc.get_tasks() == [list(item) for item in self.tasks]
        assert self.rpc.get_task(task[0]) == list(task)
        return task

    def create_feedback(self, task, status, moment):
        feedback = (len(self.feedbacks) + 1, moment, "", status, "", task[0],
                    0, 0)
        result = self.rpc.create_feedback(task[0], status=status, time=moment)
        assert result == list(feedback)
        self.feedbacks.append(feedback)
        assert self.rpc.get_feedbacks() == [list(item)
                                            for item in self.feedbacks]
        assert self.rpc.get_feedback(feedback[0]) == list(feedback)

    def check_recent_tasks(self, moment):
        expected = {(self.agents[item[3] - 1][2], item[2], item[4])
                    for item in self.tasks
                    if self.agents[item[3] - 1][1] > moment - model.WINDOW}
        assert set(self.rpc.get_recent_agent_tasks(moment)) == expected

    @rule(platform=st.text(max_size=12), argument=st.text(max_size=12),
          description=st.text(max_size=12), status=st.text(max_size=12),
          moment=st.integers(min_value=1_000, max_value=2_000))
    def all_rpc_methods(self, platform, argument, description, status, moment):
        agent = self.create_agent(platform, moment)
        task = self.create_task(agent, argument, description, moment)
        self.create_feedback(task, status, moment)
        self.check_recent_tasks(moment)


TestRpcMachine = RpcMachine.TestCase
TestRpcMachine.settings = settings(max_examples=20, stateful_step_count=10,
                                   deadline=None)
