from abc import ABC
from typing import Optional, Type

from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_core.output_parsers import PydanticOutputParser
from langgraph.prebuilt import create_react_agent


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

        # Optional structured output parser
        self._output_parser: Optional[PydanticOutputParser] = (
            PydanticOutputParser(pydantic_object=output_structure)
            if output_structure
            else None
        )

        # If we have a structured output parser, add its format instructions
        # to the system prompt so the model knows how to respond.
        self.system_prompt = system_prompt
        if self._output_parser:
            self.system_prompt += f"\n\n{self._output_parser.get_format_instructions()}"

        # LangGraph-based agent (only if tools are provided)
        self.tools = tools
        self.agent = None
        if tools:
            # Try to use create_react_agent with the state_modifier (modern)
            # if that fails, we fallback to prepending the system message in the model or endpoint
            try:
                self.agent = create_react_agent(
                    model=self.llm,
                    state_modifier=self.system_prompt,
                    tools=tools,
                )
            except Exception as e:
                print(f"DEBUG: create_react_agent with state_modifier failed: {e}")
                # Fallback: Just create without state_modifier 
                # (The LLM will have to rely on its training or we prepend system msg manually in invoke)
                self.agent = create_react_agent(
                    model=self.llm,
                    tools=tools,
                )
                self._fallback_system_prompt = True
            else:
                self._fallback_system_prompt = False

    def invoke(self, user_input: str):
        if self.agent:
            # Prepend system prompt if fallback is active
            final_input = user_input
            if getattr(self, "_fallback_system_prompt", False):
                final_input = f"{self.system_prompt}\n\nUSER INPUT: {user_input}"

            result = self.agent.invoke(
                {
                    "messages": [
                        HumanMessage(content=final_input)
                    ]
                }
            )
            last_message = result["messages"][-1]
            final_output = last_message.content
        else:
            # Simple LLM call for tool-less agents
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_input)
            ]
            response = self.llm.invoke(messages)
            final_output = response.content

        return self._post_process(final_output)

    async def ainvoke(self, user_input: str):
        if self.agent:
            # Prepend system prompt if fallback is active
            final_input = user_input
            if getattr(self, "_fallback_system_prompt", False):
                final_input = f"{self.system_prompt}\n\nUSER INPUT: {user_input}"

            result = await self.agent.ainvoke(
                {
                    "messages": [
                        HumanMessage(content=final_input)
                    ]
                }
            )
            last_message = result["messages"][-1]
            final_output = last_message.content
        else:
            # Simple LLM call for tool-less agents
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=user_input)
            ]
            response = await self.llm.ainvoke(messages)
            final_output = response.content

        return self._post_process(final_output)

    def _post_process(self, final_output):
        # Handle list-based content (common with some Gemini versions/multimodal)
        if isinstance(final_output, list):
            final_output = "".join([
                item.get("text", "") if isinstance(item, dict) else str(item)
                for item in final_output
            ])

        if self._output_parser:
            if not isinstance(final_output, str) or not final_output.strip():
                print(f"DEBUG - Final output: {final_output}")
                raise ValueError(
                    "Agent did not return a text response suitable "
                    "for structured parsing."
                )
            
            try:
                return self._output_parser.parse(final_output)
            except Exception as e:
                print(f"DEBUG - Parsing failed for output: {final_output}")
                print(f"DEBUG - Error: {e}")
                # Try simple cleaning: remove ```json and ``` if present
                cleaned_output = final_output.strip()
                if cleaned_output.startswith("```json"):
                    cleaned_output = cleaned_output[7:]
                if cleaned_output.endswith("```"):
                    cleaned_output = cleaned_output[:-3]
                try:
                    return self._output_parser.parse(cleaned_output.strip())
                except:
                    raise e # Re-raise original error if cleaning fails

        return final_output
