import asyncio
import json

from gaia_twinkle.twinkle_client import TwinkleClient, TwinkleError


def _frame(kind, content="", error=""):
    body = {"result": {"content": content}} if kind == "e2a.complete" else (
        {"error": error} if kind == "e2a.error" else {"result": {"content": content}}
    )
    return {
        "protocol_version": "1.0", "request_id": "r", "sequence": 0,
        "is_final": kind in ("e2a.complete", "e2a.error"),
        "status": "succeeded" if kind == "e2a.complete" else "in_progress",
        "response_kind": kind, "body": body, "is_stream": True,
    }


def test_ask_returns_complete_content(make_fake_agentserver):
    async def run():
        port, received, server = await make_fake_agentserver([_frame("e2a.complete", "Paris")])
        try:
            client = TwinkleClient(f"ws://127.0.0.1:{port}", timeout=5)
            ans = await client.ask("capital of France?", session_id="s1")
            assert ans == "Paris"
            assert received[0]["method"] == "chat.send"
            assert received[0]["params"]["query"] == "capital of France?"
            assert received[0]["session_id"] == "s1"
        finally:
            server.close()
            await server.wait_closed()
    asyncio.run(run())


def test_ask_accumulates_chunks(make_fake_agentserver):
    async def run():
        frames = [_frame("e2a.chunk", "Par"), _frame("e2a.chunk", "is"),
                  _frame("e2a.complete", "Paris")]
        port, _, server = await make_fake_agentserver(frames)
        try:
            client = TwinkleClient(f"ws://127.0.0.1:{port}", timeout=5)
            ans = await client.ask("q")
            assert ans == "Paris"
        finally:
            server.close()
            await server.wait_closed()
    asyncio.run(run())


def test_ask_raises_on_error(make_fake_agentserver):
    async def run():
        port, _, server = await make_fake_agentserver([_frame("e2a.error", error="boom")])
        try:
            client = TwinkleClient(f"ws://127.0.0.1:{port}", timeout=5)
            try:
                await client.ask("q")
            except TwinkleError as e:
                assert "boom" in str(e)
            else:
                raise AssertionError("expected TwinkleError")
        finally:
            server.close()
            await server.wait_closed()
    asyncio.run(run())


def test_ask_raises_on_approval_ask(make_fake_agentserver):
    async def run():
        port, _, server = await make_fake_agentserver([_frame("e2a.ask")])
        try:
            client = TwinkleClient(f"ws://127.0.0.1:{port}", timeout=5)
            try:
                await client.ask("q")
            except TwinkleError as e:
                assert "approval" in str(e).lower() or "ask" in str(e).lower()
            else:
                raise AssertionError("expected TwinkleError on e2a.ask")
        finally:
            server.close()
            await server.wait_closed()
    asyncio.run(run())


def test_ask_raises_on_refused_connection():
    async def run():
        client = TwinkleClient("ws://127.0.0.1:1", timeout=2)  # 端口 1 基本必拒
        try:
            await client.ask("q")
        except (TwinkleError, ConnectionError, OSError):
            return
        raise AssertionError("expected connection failure")
    asyncio.run(run())
