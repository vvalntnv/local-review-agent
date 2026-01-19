from ollama_api_client import OllamaApiClient


class CodingAgent:
    def __init__(self, api_client: OllamaApiClient) -> None:
        self.client = api_client
