"""Ordered, per-request fallback for the hiring agent's model calls."""

import logging
from collections import defaultdict, deque
from contextlib import aclosing
from copy import deepcopy
from functools import cached_property

import anyio
import httpx
from aiohttp import ClientConnectionError
from google.adk.models.base_llm import BaseLlm
from google.adk.models.google_llm import Gemini
from google.genai import Client
from pydantic import Field, SecretStr

logger = logging.getLogger(__name__)


class KeyedGemini(Gemini):
    api_key: SecretStr = Field(exclude=True, repr=False)

    @cached_property
    def api_client(self):
        return Client(api_key=self.api_key.get_secret_value(), vertexai=False)


def is_unavailable(error):
    if isinstance(error, (TimeoutError, ConnectionError, httpx.TransportError, ClientConnectionError)):
        return True
    status = getattr(error, "status_code", None) or getattr(error, "code", None)
    return isinstance(status, int) and (status in (408, 429) or 500 <= status < 600)


def prepare_tool_history(contents, provider):
    # Gemini may omit call IDs. Chat-completions providers require matching
    # IDs on calls and results, including parallel calls to the same tool.
    pending = defaultdict(deque)
    for message_index, message in enumerate(contents):
        parts = message.parts or []
        if isinstance(provider, Gemini):
            # Gemini's documented placeholder for imported tool-call history.
            first_call = next((part for part in parts if part.function_call), None)
            if first_call and first_call.function_call.id and not first_call.thought_signature:
                first_call.thought_signature = b"skip_thought_signature_validator"
            continue
        for part_index, part in enumerate(parts):
            call, result = part.function_call, part.function_response
            if call and not call.id:
                call.id = f"call_{message_index}_{part_index}"
                pending[call.name].append(call.id)
            if result and not result.id and pending[result.name]:
                result.id = pending[result.name].popleft()
            # Thought signatures are provider-specific metadata.
            if part.thought_signature and not part.thought:
                part.thought_signature = None


class FallbackModel(BaseLlm):
    providers: tuple[BaseLlm, ...] = Field(exclude=True, repr=False)
    first_response_timeout: float = Field(default=30, gt=0, allow_inf_nan=False)

    async def generate_content_async(self, llm_request, stream=False):
        for index, provider in enumerate(self.providers):
            # Both adapters modify the request. Keep messages/config isolated and
            # retain the original ADK tool instances (which may own live clients).
            attempt = llm_request.model_copy(update={
                "model": provider.model,
                "contents": deepcopy(llm_request.contents),
                "config": llm_request.config.model_copy(deep=True),
            })
            prepare_tool_history(attempt.contents, provider)
            responses = provider.generate_content_async(attempt, stream=stream)
            async with aclosing(responses):
                try:
                    with anyio.fail_after(self.first_response_timeout):
                        first = await anext(responses)
                except Exception as error:
                    if not is_unavailable(error) or index + 1 == len(self.providers):
                        raise
                    logger.warning("Model endpoint %d unavailable, trying endpoint %d", index + 1, index + 2)
                    continue
                # Once anything has been emitted, replay could duplicate tool calls.
                yield first
                async for response in responses:
                    yield response
                return


def build_model(model_name, env):
    primary_key = env.get("GOOGLE_API_KEY") or env.get("GEMINI_API_KEY")
    keys = dict.fromkeys(k.strip() for k in env.get("GEMINI_FALLBACK_KEYS", "").split(",") if k.strip())
    keys.pop(primary_key, None)
    models = dict.fromkeys(m.strip() for m in env.get("MODEL_FALLBACKS", "").split(",") if m.strip())
    if not keys and not models:
        return model_name

    providers = [Gemini(model=model_name)]
    providers.extend(KeyedGemini(model=model_name, api_key=SecretStr(key)) for key in keys)
    if models:
        from google.adk.models.lite_llm import LiteLlm

        providers.extend(LiteLlm(model=name, num_retries=0) for name in models)
    return FallbackModel(
        model=model_name,
        providers=tuple(providers),
        first_response_timeout=float(env.get("MODEL_TIMEOUT_SECONDS", "30")),
    )
