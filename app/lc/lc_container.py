# app/component/lc_container.py
from .lc_agent import BasicAgent,MathToolAgent,AgentFactory, TavilyWebSearchAgent
from .lc_model_provider import ModelProvider
from .lc_tools import tool_math, tool_tavily

class LCContainer:
    def __init__(self):
        model_provider = ModelProvider("gpt-5-nano")
        factory = AgentFactory(model_provider.get())

        self.basic_agent = BasicAgent(factory)
        self.math_agent = MathToolAgent(factory, tools=[tool_math])
        self.tavily_agent = TavilyWebSearchAgent(factory, tools=[tool_tavily])
        
        

        # placeholders for future agents
        # self.rag_agent = RagAgent(...)
        # self.sql_agent = SqlAgent(...)
