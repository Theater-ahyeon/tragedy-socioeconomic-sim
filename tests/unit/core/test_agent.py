"""Tests for Agent and AgentSet classes."""

import pytest

from tragedy.core.agent import Agent, AgentSet


class TestAgent:
    def test_create_agent(self):
        agent = Agent(agent_id=1, agent_type="Household")
        assert agent.id == 1
        assert agent.agent_type == "Household"
        assert agent.alive is True
        assert agent.creation_tick == 0

    def test_agent_defaults(self):
        agent = Agent(agent_id=42)
        assert agent.agent_type == "Agent"
        assert agent.attributes == {}

    def test_agent_attributes_dict(self):
        agent = Agent(agent_id=1)
        agent.attributes["wealth"] = 100.0
        agent.attributes["age"] = 25
        assert agent.attributes["wealth"] == 100.0
        assert agent.attributes["age"] == 25

    def test_agent_repr(self):
        agent = Agent(agent_id=7, agent_type="Firm")
        assert "Firm" in repr(agent)
        assert "7" in repr(agent)

    def test_agent_hash(self):
        a1 = Agent(agent_id=1)
        a2 = Agent(agent_id=1)
        a3 = Agent(agent_id=2)
        assert hash(a1) == hash(a2)
        assert hash(a1) != hash(a3)

    def test_agent_equality(self):
        a1 = Agent(agent_id=1)
        a2 = Agent(agent_id=1)
        a3 = Agent(agent_id=2)
        assert a1 == a2
        assert a1 != a3
        assert a1 != "not an agent"


class TestAgentSet:
    def test_create_empty(self):
        agents = AgentSet()
        assert len(agents) == 0

    def test_create_with_list(self):
        a1 = Agent(agent_id=1)
        a2 = Agent(agent_id=2)
        agents = AgentSet([a1, a2])
        assert len(agents) == 2

    def test_add(self):
        agents = AgentSet()
        agent = Agent(agent_id=1)
        agents.add(agent)
        assert len(agents) == 1
        assert agents.get(1) is agent

    def test_add_duplicate(self):
        agents = AgentSet()
        agent = Agent(agent_id=1)
        agents.add(agent)
        agents.add(agent)
        assert len(agents) == 1

    def test_remove_by_reference(self):
        agent = Agent(agent_id=1)
        agents = AgentSet([agent])
        removed = agents.remove(agent)
        assert removed is agent
        assert len(agents) == 0

    def test_remove_by_id(self):
        agent = Agent(agent_id=1)
        agents = AgentSet([agent])
        removed = agents.remove(1)
        assert removed is agent
        assert len(agents) == 0

    def test_remove_nonexistent(self):
        agents = AgentSet()
        result = agents.remove(99)
        assert result is None

    def test_get(self):
        agent = Agent(agent_id=42)
        agents = AgentSet([agent])
        assert agents.get(42) is agent
        assert agents.get(99) is None

    def test_clear(self):
        agents = AgentSet([Agent(agent_id=i) for i in range(5)])
        agents.clear()
        assert len(agents) == 0

    def test_filter(self):
        agents = AgentSet()
        for i in range(10):
            a = Agent(agent_id=i)
            a.alive = i % 2 == 0
            agents.add(a)

        alive = agents.filter(lambda a: a.alive)
        assert len(alive) == 5
        assert all(a.alive for a in alive)

    def test_iteration(self):
        ids = [1, 5, 9, 3, 7]
        agents = AgentSet([Agent(agent_id=i) for i in ids])
        iterated = [a.id for a in agents]
        assert iterated == ids  # Insertion order preserved

    def test_contains(self):
        agent = Agent(agent_id=1)
        agents = AgentSet([agent])
        assert agent in agents
        assert Agent(agent_id=2) not in agents

    def test_select_sample_size(self):
        agents = AgentSet([Agent(agent_id=i) for i in range(100)])
        subset = agents.select(10)
        assert len(subset) == 10

    def test_groupby(self):
        agents = AgentSet()
        for i in range(6):
            a = Agent(agent_id=i, agent_type="Firm" if i < 3 else "Household")
            agents.add(a)

        groups = agents.groupby(lambda a: a.agent_type)
        assert "Firm" in groups
        assert "Household" in groups
        assert len(groups["Firm"]) == 3
        assert len(groups["Household"]) == 3

    def test_map(self):
        agents = AgentSet([Agent(agent_id=i) for i in range(5)])
        ids = agents.map(lambda a: a.id)
        assert ids == [0, 1, 2, 3, 4]

    def test_count(self):
        agents = AgentSet()
        for i in range(10):
            a = Agent(agent_id=i)
            a.alive = i < 7
            agents.add(a)

        assert agents.count() == 10
        assert agents.count(lambda a: a.alive) == 7

    def test_first(self):
        agents = AgentSet()
        assert agents.first() is None
        agent = Agent(agent_id=1)
        agents.add(agent)
        assert agents.first() is agent

    def test_do_method_dispatch(self):
        # Agent uses __slots__, so we can't dynamically add methods.
        # Instead, test do() with a method that already exists.
        agents = AgentSet()
        for i in range(5):
            a = Agent(agent_id=i)
            a.alive = False  # We'll call a method that flips this
            agents.add(a)

        # do() calls the named method on each agent
        # The Agent class doesn't have a built-in method we can use,
        # so we test the dispatch mechanism by verifying it iterates correctly.
        # Create a subclass that has a test method
        class TestAgent(Agent):
            __slots__ = ()
            def mark(self):
                self.alive = True

        agents2 = AgentSet()
        for i in range(5):
            a = TestAgent(agent_id=i + 100)
            a.alive = False
            agents2.add(a)

        agents2.do("mark")
        assert all(a.alive for a in agents2)
