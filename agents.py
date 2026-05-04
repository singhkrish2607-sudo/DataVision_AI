import asyncio
import json
import os
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

import openai
from pydantic import BaseModel

T = TypeVar("T")

class RunConfig(BaseModel):
    trace_metadata: Dict[str, Any] = {}

@dataclass
class CodeInterpreterTool:
    tool_config: Dict[str, Any]

@dataclass
class RunContextWrapper(Generic[T]):
    context: T

class TResponseInputItem(BaseModel):
    role: str
    content: List[Dict[str, Any]]

    def to_input_item(self) -> Dict[str, Any]:
        return {"role": self.role, "content": self.content}

class ModelSettings(BaseModel):
    temperature: float = 0.0
    top_p: float = 1.0
    max_tokens: int = 1024
    store: bool = False

@dataclass
class Agent(Generic[T]):
    name: str
    instructions: Any
    model: str = "gpt-4o"
    tools: List[Any] = field(default_factory=list)
    model_settings: Optional[ModelSettings] = None
    output_type: Optional[Type[BaseModel]] = None

class AgentRunResult:
    def __init__(self, new_items: List[TResponseInputItem], final_output: Any):
        self.new_items = new_items
        self.final_output = final_output

    def final_output_as(self, output_type: Type[T]) -> T:
        if output_type is str:
            if isinstance(self.final_output, str):
                return self.final_output
            if isinstance(self.final_output, BaseModel):
                return self.final_output.json()
            return str(self.final_output)
        return self.final_output

@contextmanager
def trace(name: str):
    yield

class Runner:
    @staticmethod
    async def run(agent: Agent, input: List[Any], run_config: RunConfig, context: Any) -> AgentRunResult:
        messages: List[Dict[str, str]] = []

        for item in input:
            if isinstance(item, TResponseInputItem):
                role = item.role
                content = item.content
            elif isinstance(item, dict):
                role = item.get("role", "user")
                content = item.get("content", [])
            else:
                continue

            if isinstance(content, str):
                message_text = content
            else:
                texts: List[str] = []
                for part in content:
                    if isinstance(part, dict):
                        if part.get("type") == "input_text":
                            texts.append(str(part.get("text", "")))
                        else:
                            texts.append(str(part.get("text", "")))
                    else:
                        texts.append(str(part))
                message_text = "\n".join([t for t in texts if t])

            messages.append({"role": role, "content": message_text})

        system_message = agent.instructions(RunContextWrapper(context), agent)
        messages.insert(0, {"role": "system", "content": system_message})

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is required for agent execution.")

        client = None
        if hasattr(openai, "OpenAI"):
            client = openai.OpenAI(api_key=api_key)
        else:
            openai.api_key = api_key

        model_settings = agent.model_settings or ModelSettings()

        def create_completion():
            if client is not None:
                return client.chat.completions.create(
                    model=agent.model,
                    messages=messages,
                    temperature=model_settings.temperature,
                    top_p=model_settings.top_p,
                    max_tokens=model_settings.max_tokens,
                )
            if hasattr(openai, "ChatCompletion"):
                return openai.ChatCompletion.create(
                    model=agent.model,
                    messages=messages,
                    temperature=model_settings.temperature,
                    top_p=model_settings.top_p,
                    max_tokens=model_settings.max_tokens,
                )
            raise RuntimeError("OpenAI client does not support ChatCompletion")

        try:
            response = await asyncio.wait_for(asyncio.to_thread(create_completion), timeout=60)
        except asyncio.TimeoutError as exc:
            raise RuntimeError("OpenAI request timed out after 60 seconds") from exc
        except KeyboardInterrupt as exc:
            raise RuntimeError("OpenAI request was interrupted") from exc

        def get_content(resp: Any) -> str:
            if isinstance(resp, dict):
                return resp["choices"][0]["message"]["content"]
            if hasattr(resp, "choices"):
                choices = getattr(resp, "choices")
                if choices:
                    first = choices[0]
                    if hasattr(first, "message"):
                        message = getattr(first, "message")
                        if hasattr(message, "content"):
                            return getattr(message, "content")
                        if isinstance(message, dict):
                            return message.get("content", "")
                    if isinstance(first, dict):
                        return first.get("message", {}).get("content", "")
            if hasattr(resp, "text"):
                return getattr(resp, "text")
            return str(resp)

        output_text = str(get_content(response)).strip()
        new_item = TResponseInputItem(role="assistant", content=[{"type": "output_text", "text": output_text}])

        final_output: Any = output_text
        if agent.output_type is not None:
            parsed_data: Dict[str, Any]
            try:
                parsed_data = json.loads(output_text)
            except Exception:
                parsed_data = {"charts": output_text}

            try:
                final_output = agent.output_type.model_validate(parsed_data)
            except Exception:
                try:
                    final_output = agent.output_type(**parsed_data)
                except Exception:
                    final_output = agent.output_type(charts=output_text)

        return AgentRunResult(new_items=[new_item], final_output=final_output)
