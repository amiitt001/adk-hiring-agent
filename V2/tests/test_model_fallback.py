"""Exercise ADK model routing with synthetic responses and credentials."""

import asyncio
import unittest
from unittest.mock import patch

from google.adk.models.google_llm import Gemini
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types
from google.genai.errors import ClientError, ServerError

from model_fallback import build_model


class ModelFallbackTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.router = build_model("gemini-test", {
            "GOOGLE_API_KEY": "primary", "GEMINI_FALLBACK_KEYS": "primary,backup,backup",
            "MODEL_TIMEOUT_SECONDS": "0.05",
        })
        self.request = LlmRequest(contents=[types.Content(role="user", parts=[types.Part(text="sample")])])

    async def run_router(self):
        return [r async for r in self.router.generate_content_async(self.request)]

    def test_configuration(self):
        self.assertEqual(build_model("gemini-test", {}), "gemini-test")
        self.assertEqual(len(self.router.providers), 2)
        with patch("model_fallback.Client") as client:
            self.router.providers[1].api_client
            client.assert_called_once_with(api_key="backup", vertexai=False)
        self.assertNotIn("backup", self.router.model_dump_json())

    async def test_stalled_primary_times_out_and_backup_receives_original_request(self):
        attempts = []

        async def generate(provider, request, stream):
            attempts.append(request.contents[0].parts[0].text)
            if provider is self.router.providers[0]:
                request.contents.clear()
                await asyncio.sleep(60)
            yield LlmResponse()

        with patch.object(Gemini, "generate_content_async", generate):
            self.assertEqual(len(await self.run_router()), 1)
        self.assertEqual(attempts, ["sample", "sample"])

    async def test_primary_success_and_client_errors_do_not_use_backup(self):
        attempts = []

        async def generate(provider, request, stream):
            attempts.append(provider)
            if len(attempts) == 2:
                raise ClientError(400, {})
            yield LlmResponse()

        with patch.object(Gemini, "generate_content_async", generate):
            await self.run_router()
            with self.assertRaises(ClientError):
                await self.run_router()
        self.assertEqual(attempts, [self.router.providers[0]] * 2)

    async def test_rate_limit_then_outage_reports_final_failure(self):
        attempts = []

        async def generate(provider, request, stream):
            attempts.append(provider)
            if len(attempts) == 1:
                raise ClientError(429, {})
            raise ServerError(503, {})
            yield

        with patch.object(Gemini, "generate_content_async", generate):
            with self.assertRaises(ServerError):
                await self.run_router()
        self.assertEqual(attempts, list(self.router.providers))

    async def test_partial_stream_failure_does_not_replay(self):
        attempts = []

        async def generate(provider, request, stream):
            attempts.append(provider)
            yield LlmResponse(partial=True)
            raise ConnectionError()

        with patch.object(Gemini, "generate_content_async", generate):
            responses = self.router.generate_content_async(self.request, stream=True)
            self.assertTrue((await anext(responses)).partial)
            with self.assertRaises(ConnectionError):
                await anext(responses)
        self.assertEqual(attempts, [self.router.providers[0]])

    async def test_secondary_provider_receives_tool_calls_and_results(self):
        from google.adk.models.lite_llm import LiteLLMClient
        from litellm import ModelResponse

        router = build_model("gemini-test", {"MODEL_FALLBACKS": "openai/gpt-4.1-mini"})
        request = self.request
        request.contents += [
            types.Content(role="model", parts=[types.Part.from_function_call(name="review", args={})]),
            types.Content(role="user", parts=[types.Part.from_function_response(name="review", response={"ok": True})]),
        ]

        async def outage(provider, request, stream):
            raise ServerError(503, {})
            yield

        reply = ModelResponse(choices=[{"message": {"role": "assistant", "content": "Reviewed"}}])
        with patch.object(Gemini, "generate_content_async", outage), \
                patch.object(LiteLLMClient, "acompletion", return_value=reply) as completion:
            responses = [r async for r in router.generate_content_async(request)]
        args = completion.await_args.kwargs
        self.assertEqual(args["model"], "openai/gpt-4.1-mini")
        call_id = args["messages"][1]["tool_calls"][0]["id"]
        self.assertTrue(call_id)
        self.assertEqual(args["messages"][2]["tool_call_id"], call_id)
        self.assertEqual(responses[0].content.parts[0].text, "Reviewed")
        self.assertIsNone(request.contents[1].parts[0].function_call.id)
