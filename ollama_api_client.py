import json
from typing import AsyncGenerator
import httpx

from ollama_response import OllamaResponse


class OllamaApiClient:
    def __init__(self, address: str, model: str) -> None:
        self.endpoint = f"http://{address}"
        self.model = model

    async def generate_response(
        self,
        request: str,
        context: list[int] | None = None,
    ) -> AsyncGenerator[OllamaResponse, OllamaResponse]:
        async with httpx.AsyncClient(timeout=60) as http:
            payload = {
                "model": self.model,
                "prompt": request,
                "context": context,
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
