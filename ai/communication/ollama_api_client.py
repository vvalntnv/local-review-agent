import json
from typing import AsyncGenerator, Self, List, Optional
import httpx

from ai.ollama_response import Message, OllamaChatResponse, OllamaResponse
from ai.base_model import BaseAIModel


class OllamaApiClient(BaseAIModel):
    def __init__(self, address: str, model: str) -> None:
        self.endpoint = f"http://{address}"
        self.model = model

    def __enter__(self) -> Self:
        self.load_model_into_computers_memory()
        print("LOADING MODEL INTO MEMORY")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> Self:
        if exc_val:
            raise exc_val

        self.unload_model_from_memory()
        print("UNLOADED MODEL FROM MEMORY")
        return self

    def load_model_into_computers_memory(self) -> None:
        response = httpx.post(
            f"{self.endpoint}/api/generate",
            json={"model": self.model},
        )
        assert response.json()["done"] == True, "Could not load the model"

    def unload_model_from_memory(self) -> None:
        response = httpx.post(
            f"{self.endpoint}/api/generate",
            json={"model": self.model, "keep_alive": 0},
        )

        assert response.json()["done"] == True, "Model couldn't be offloaded"

    async def chat(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
    ) -> AsyncGenerator[OllamaChatResponse, None]:
        async with httpx.AsyncClient() as http:
            payload = {"model": self.model, "messages": messages}

            async with http.stream(
                "POST",
                f"{self.endpoint}/api/chat",
                json=payload,
            ) as stream:
                if stream.status_code != httpx.codes.OK:
                    raise Exception("error: " + str(stream.status_code))

                async for line in stream.aiter_lines():
                    if line.strip():
                        yield OllamaChatResponse(**json.loads(line))

    async def generate(
        self,
        prompt: str,
        context: Optional[List[int]] = None,
    ) -> AsyncGenerator[OllamaResponse, None]:
        async with httpx.AsyncClient(timeout=60) as http:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "context": context,
                "options": {
                    "seed": None,  # Used for deterministic answers
                },
            }

            async with http.stream(
                "POST",
                f"{self.endpoint}/api/generate",
                json=payload,
            ) as stream:
                async for line in stream.aiter_lines():
                    if line.strip():
                        response = OllamaResponse(**json.loads(line))
                        yield response
