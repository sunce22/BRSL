# tests/test_ws_server.py
import asyncio
import json
import pytest
import websockets


@pytest.mark.asyncio
async def test_server_broadcasts_hero_message():
    from hero_detector import DetectorServer
    server = DetectorServer(port=17182)
    server.start()
    await asyncio.sleep(0.15)

    received = []
    async with websockets.connect("ws://localhost:17182") as ws:
        server.push({"type": "hero", "id": "abbess"})
        await asyncio.sleep(0.15)
        msg = await asyncio.wait_for(ws.recv(), timeout=1.0)
        received.append(json.loads(msg))

    server.stop()
    assert received == [{"type": "hero", "id": "abbess"}]


@pytest.mark.asyncio
async def test_server_broadcasts_to_multiple_clients():
    from hero_detector import DetectorServer
    server = DetectorServer(port=17183)
    server.start()
    await asyncio.sleep(0.15)

    async with websockets.connect("ws://localhost:17183") as ws1, \
               websockets.connect("ws://localhost:17183") as ws2:
        server.push({"type": "hero", "id": "kael"})
        await asyncio.sleep(0.15)
        msg1 = await asyncio.wait_for(ws1.recv(), timeout=1.0)
        msg2 = await asyncio.wait_for(ws2.recv(), timeout=1.0)

    server.stop()
    assert json.loads(msg1)["id"] == "kael"
    assert json.loads(msg2)["id"] == "kael"
