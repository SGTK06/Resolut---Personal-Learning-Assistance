from abc import ABC, abstractmethod

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain.agents import create_agent


class BaseAgent(ABC):

    def __init__(self, gemini_model, gemini_api_key, requests_per_min, system_prompt, tools):
        rate_limiter = InMemoryRateLimiter(
            requests_per_second=requests_per_min/60
        )

        self.llm = ChatGoogleGenerativeAI(
            model=gemini_model,
            google_api_key=gemini_api_key,
            temperature=0,
            rate_limiter=rate_limiter
        )

        self.agent = create_agent(
            model=self.llm,
            system_prompt=SystemMessage(content=system_prompt),
            tools=tools
        )

    @abstractmethod
    def invoke(self):
        pass
