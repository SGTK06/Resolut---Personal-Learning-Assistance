from abc import ABC
from typing import Optional, Type

from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain.agents import create_agent
from langchain_core.output_parsers import PydanticOutputParser


class BaseAgent(ABC):

    def __init__(
        self,
        gemini_model: str,
        gemini_api_key: str,
        system_prompt: str,
        requests_per_min: int = 15,
        tools: Optional[list] = None,
        output_structure: Optional[Type[BaseModel]] = None,
    ) -> None:

        rate_limiter = InMemoryRateLimiter(
            requests_per_second=requests_per_min / 60
        )

        self.llm = ChatGoogleGenerativeAI(
            model=gemini_model,
            google_api_key=gemini_api_key,
            temperature=0,
            rate_limiter=rate_limiter,
        )

        # LangGraph-based agent
        self.agent = create_agent(
            model=self.llm,
            system_prompt=SystemMessage(content=system_prompt),
            tools=tools,
        )

        # Optional structured output parser
        self._output_parser: Optional[PydanticOutputParser] = (
            PydanticOutputParser(pydantic_object=output_structure)
            if output_structure
            else None
        )

    def invoke(self, user_input: str):
        result = self.agent.invoke(
            {
                "messages": [
                    HumanMessage(content=user_input)
                ]
            }
        )

        final_output = result["messages"][-1].content

        if self._output_parser:
            if not isinstance(final_output, str):
                raise ValueError(
                    "Agent did not return a text response suitable "
                    "for structured parsing."
                )
            return self._output_parser.parse(final_output)

        return final_output
