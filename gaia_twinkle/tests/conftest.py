import json
import pathlib
import socket
import sys

# 保证 data-sets 根在 sys.path，无论何种 pytest 调用方式。
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

import pytest
from websockets.asyncio.server import serve


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def free_port():
    return _free_port()


@pytest.fixture
def make_fake_agentserver():
    """工厂：传入"应答帧序列"，返回 (port, 收到的 envelope 列表, server)。

    用法：port, received, server = await make_fake_agentserver(frames)
    frames: list[dict]，收到 client envelope 后依次发送。
    """

    async def _factory(frames):
        port = _free_port()
        received: list[dict] = []

        async def handler(ws):
            # 先发 connection.ack（twinkle AgentServer 行为）
            await ws.send(json.dumps({
                "type": "event", "event": "connection.ack", "payload": {"status": "ready"}
            }))
            received.append(json.loads(await ws.recv()))  # 收 client 发来的 envelope
            for fr in frames:
                await ws.send(json.dumps(fr, ensure_ascii=False))

        server = await serve(handler, "127.0.0.1", port)
        return port, received, server

    return _factory
