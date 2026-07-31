"""WS 客户端：手搓 E2A 信封直连 twinkle AgentServer。

发 E2AEnvelope(method="chat.send", params={"query":...})，读帧到 e2a.complete，
返回 body.result.content。镜像 twinkle/tests/test_agentserver_handler.py 的连接范式。
不 import twinkle。
"""
from __future__ import annotations

import asyncio
import json
import uuid

from websockets.asyncio.client import connect

PROTOCOL_VERSION = "1.0"


class TwinkleError(Exception):
    """AgentServer 返回 e2a.error / e2a.ask，或连接失败。"""


class TwinkleClient:
    def __init__(self, url: str = "ws://127.0.0.1:18000", timeout: float = 300.0):
        self.url = url
        self.timeout = timeout

    async def ask(self, query: str, session_id: str | None = None) -> str:
        """发一条 query，流式读到 final，返回答案文本。"""
        request_id = uuid.uuid4().hex
        envelope = {
            "protocol_version": PROTOCOL_VERSION,
            "request_id": request_id,
            "channel": "web",
            "session_id": session_id or request_id,
            "method": "chat.send",
            "params": {"query": query},
            "timestamp": 0.0,
        }
        text = ""
        try:
            async with connect(self.url) as ws:
                await ws.recv()  # connection.ack
                await ws.send(json.dumps(envelope, ensure_ascii=False))
                while True:
                    raw = await asyncio.wait_for(ws.recv(), timeout=self.timeout)
                    frame = json.loads(raw)
                    kind = frame.get("response_kind")
                    body = frame.get("body") or {}
                    if kind == "e2a.chunk":
                        text += (body.get("result") or {}).get("content", "") or ""
                    elif kind == "e2a.complete":
                        final = (body.get("result") or {}).get("content", "")
                        return final or text
                    elif kind == "e2a.error":
                        raise TwinkleError(body.get("error", "unknown error"))
                    elif kind == "e2a.ask":
                        raise TwinkleError(
                            "agent requested approval (e2a.ask); unattended mode cannot respond — "
                            "check twinkle permissions.enabled=false"
                        )
                    # 其余帧（todo_update 等）忽略
        except TwinkleError:
            raise
        except Exception as exc:
            raise TwinkleError(f"twinkle connection/run failed: {exc}") from exc
