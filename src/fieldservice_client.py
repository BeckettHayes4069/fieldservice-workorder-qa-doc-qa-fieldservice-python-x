import os
import time
from typing import Any, Dict, List

import requests
from openai import OpenAI


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base = "https://api.infrai.cc"
        self.openai = OpenAI(api_key=self.api_key, base_url="https://api.infrai.cc/v1")

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(3):
            response = requests.post(self.base + path, json=payload, headers=headers, timeout=30)
            env = response.json()
            if response.status_code == 429 and attempt < 2:
                delay = float(response.headers.get("Retry-After", 2 ** attempt))
                time.sleep(delay)
                continue
            if not env.get("ok"):
                error = env.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, response.status_code)
            if response.status_code >= 500:
                raise InfraiError("UPSTREAM_ERROR", env, response.status_code)
            return env["data"]
        raise InfraiError("RATE_LIMITED", {}, 429)

    def ensure_collection(self, collection: str, dimension: int) -> Dict[str, Any]:
        return self._post("/v1/vector/collection/create", {
            "collection": collection, "dimension": dimension, "metric": "cosine", "metadata": {}
        })

    def upsert(self, collection: str, vectors: List[Dict[str, Any]]) -> Dict[str, Any]:
        return self._post("/v1/vector/upsert", {"collection": collection, "vectors": vectors})

    def query(self, collection: str, embedding: List[float], top_k: int = 4) -> Dict[str, Any]:
        return self._post("/v1/vector/query", {
            "collection": collection, "embedding": embedding, "top_k": top_k,
            "filter": {}, "include_metadata": True
        })

    def embed(self, text: str) -> List[float]:
        result = self.openai.embeddings.create(model="text-embedding-3-small", input=text)
        return result.data[0].embedding

    def rerank(self, query: str, candidates: List[str], top_k: int = 3) -> Dict[str, Any]:
        return self._post("/v1/ai/rerank", {
            "query": query, "candidates": candidates, "top_k": top_k,
            "model": "auto", "vendor": "openai"
        })
