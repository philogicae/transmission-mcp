import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from .wrapper import TransmissionClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TransmissionAPI")

app = FastAPI(
    title="Transmission API",
    description="REST API for Transmission torrent client",
    version="1.0.0",
)

client = TransmissionClient()


def _check(result: Any) -> Any:
    if isinstance(result, str):
        logger.error(f"Error: {result}")
        raise HTTPException(status_code=400, detail=result)
    return result


# Request models
class AddTorrentRequest(BaseModel):
    torrent: str
    download_dir: str | None = None
    paused: bool = False
    labels: list[str] | None = None


class ChangeTorrentRequest(BaseModel):
    download_limit: int | None = None
    download_limited: bool | None = None
    upload_limit: int | None = None
    upload_limited: bool | None = None
    bandwidth_priority: int | None = None
    honors_session_limits: bool | None = None
    labels: list[str] | None = None


class SetSessionRequest(BaseModel):
    download_dir: str | None = None
    speed_limit_down: int | None = None
    speed_limit_down_enabled: bool | None = None
    speed_limit_up: int | None = None
    speed_limit_up_enabled: bool | None = None
    alt_speed_down: int | None = None
    alt_speed_up: int | None = None
    alt_speed_enabled: bool | None = None


class MoveDataRequest(BaseModel):
    location: str
    move: bool = True


class RenamePathRequest(BaseModel):
    path: str
    name: str


@app.get("/session", tags=["Session"])
async def get_session() -> dict[str, Any]:
    """Get session configuration."""
    logger.info("Getting session info")
    return _check(await client.get_session())


@app.get("/session/stats", tags=["Session"])
async def get_session_stats() -> dict[str, Any]:
    """Get session statistics (instance stats)."""
    logger.info("Getting session stats")
    return _check(await client.get_session_stats())


@app.patch("/session", tags=["Session"])
async def set_session(request: SetSessionRequest) -> dict[str, Any]:
    """Update session settings."""
    logger.info("Updating session settings")
    kwargs = {k: v for k, v in request.model_dump().items() if v is not None}
    _check(await client.set_session(**kwargs))
    return {"status": "ok"}


@app.get("/session/free-space", tags=["Session"])
async def get_free_space(path: str = Query(...)) -> dict[str, Any]:
    """Get free space at path."""
    logger.info(f"Getting free space at: {path}")
    return {"path": path, "freeSpace": _check(await client.free_space(path))}


@app.get("/session/port-test", tags=["Session"])
async def port_test() -> dict[str, Any]:
    """Test if peer port is accessible."""
    logger.info("Testing peer port")
    return {"portOpen": _check(await client.port_test())}


@app.post("/session/blocklist-update", tags=["Session"])
async def blocklist_update() -> dict[str, Any]:
    """Update blocklist."""
    logger.info("Updating blocklist")
    return {"size": _check(await client.blocklist_update())}


@app.get("/torrents", tags=["Torrents"])
async def list_torrents() -> list[dict[str, Any]]:
    """List all torrents with their details."""
    logger.info("Listing all torrents")
    return _check(await client.list_torrents())


@app.get("/torrents/recent", tags=["Torrents"])
async def get_recently_active() -> dict[str, Any]:
    """Get recently active torrents."""
    logger.info("Getting recently active torrents")
    return _check(await client.get_recently_active())


@app.get("/torrents/{torrent_id}", tags=["Torrents"])
async def get_torrent_details(torrent_id: str) -> dict[str, Any]:
    """Get detailed info for a specific torrent by its ID or hash."""
    logger.info(f"Getting details for torrent: {torrent_id}")
    return _check(await client.get_torrent(torrent_id))


@app.get("/torrents/{torrent_id}/stats", tags=["Torrents"])
async def get_torrent_stats(torrent_id: str) -> dict[str, Any]:
    """Get stats and status for a specific torrent by its ID or hash."""
    logger.info(f"Getting stats for torrent: {torrent_id}")
    return _check(await client.get_torrent(torrent_id))


@app.post("/torrents", tags=["Torrents"])
async def add_torrent(request: AddTorrentRequest) -> dict[str, Any]:
    """Add a torrent from magnet link, URL, or file path."""
    logger.info(f"Adding torrent: {request.torrent}")
    return _check(
        await client.add_torrent(
            request.torrent,
            download_dir=request.download_dir,
            paused=request.paused,
            labels=request.labels,
        )
    )


@app.delete("/torrents/{torrent_id}", tags=["Torrents"])
async def remove_torrent(
    torrent_id: str,
    delete_data: bool = Query(False, description="Also delete files"),
) -> dict[str, Any]:
    """Remove a torrent."""
    logger.info(f"Removing torrent: {torrent_id} (delete_data={delete_data})")
    _check(await client.remove_torrent(torrent_id, delete_data=delete_data))
    return {"status": "ok", "id": torrent_id}


@app.post("/torrents/{torrent_id}/start", tags=["Control"])
async def start_torrent(torrent_id: str) -> dict[str, Any]:
    """Start a torrent."""
    logger.info(f"Starting torrent: {torrent_id}")
    _check(await client.start_torrent(torrent_id))
    return {"status": "ok", "id": torrent_id}


@app.post("/torrents/{torrent_id}/stop", tags=["Control"])
async def stop_torrent(torrent_id: str) -> dict[str, Any]:
    """Stop a torrent."""
    logger.info(f"Stopping torrent: {torrent_id}")
    _check(await client.stop_torrent(torrent_id))
    return {"status": "ok", "id": torrent_id}


@app.post("/torrents/{torrent_id}/verify", tags=["Control"])
async def verify_torrent(torrent_id: str) -> dict[str, Any]:
    """Verify torrent data."""
    logger.info(f"Verifying torrent: {torrent_id}")
    _check(await client.verify_torrent(torrent_id))
    return {"status": "ok", "id": torrent_id}


@app.post("/torrents/{torrent_id}/reannounce", tags=["Control"])
async def reannounce_torrent(torrent_id: str) -> dict[str, Any]:
    """Reannounce torrent to trackers."""
    logger.info(f"Reannouncing torrent: {torrent_id}")
    _check(await client.reannounce_torrent(torrent_id))
    return {"status": "ok", "id": torrent_id}


@app.post("/torrents/start-all", tags=["Control"])
async def start_all() -> dict[str, Any]:
    """Start all torrents."""
    logger.info("Starting all torrents")
    _check(await client.start_all())
    return {"status": "ok"}


@app.patch("/torrents/{torrent_id}", tags=["Modify"])
async def change_torrent(
    torrent_id: str, request: ChangeTorrentRequest
) -> dict[str, Any]:
    """Change torrent settings."""
    logger.info(f"Changing settings for torrent: {torrent_id}")
    kwargs = {k: v for k, v in request.model_dump().items() if v is not None}
    _check(await client.change_torrent(torrent_id, **kwargs))
    return {"status": "ok", "id": torrent_id}


@app.post("/torrents/{torrent_id}/move", tags=["Modify"])
async def move_torrent_data(
    torrent_id: str, request: MoveDataRequest
) -> dict[str, Any]:
    """Move torrent data to new location."""
    logger.info(f"Moving torrent {torrent_id} to: {request.location}")
    _check(await client.move_torrent_data(torrent_id, request.location, request.move))
    return {"status": "ok", "id": torrent_id}


@app.post("/torrents/{torrent_id}/rename", tags=["Modify"])
async def rename_torrent_path(
    torrent_id: str, request: RenamePathRequest
) -> dict[str, Any]:
    """Rename a file or directory in torrent."""
    logger.info(
        f"Renaming path in torrent {torrent_id}: {request.path} -> {request.name}"
    )
    return _check(
        await client.rename_torrent_path(torrent_id, request.path, request.name)
    )


@app.post("/torrents/{torrent_id}/queue/top", tags=["Queue"])
async def queue_top(torrent_id: str) -> dict[str, Any]:
    """Move torrent to top of queue."""
    logger.info(f"Moving torrent {torrent_id} to top of queue")
    _check(await client.queue_top(torrent_id))
    return {"status": "ok", "id": torrent_id}


@app.post("/torrents/{torrent_id}/queue/bottom", tags=["Queue"])
async def queue_bottom(torrent_id: str) -> dict[str, Any]:
    """Move torrent to bottom of queue."""
    logger.info(f"Moving torrent {torrent_id} to bottom of queue")
    _check(await client.queue_bottom(torrent_id))
    return {"status": "ok", "id": torrent_id}


@app.post("/torrents/{torrent_id}/queue/up", tags=["Queue"])
async def queue_up(torrent_id: str) -> dict[str, Any]:
    """Move torrent up in queue."""
    logger.info(f"Moving torrent {torrent_id} up in queue")
    _check(await client.queue_up(torrent_id))
    return {"status": "ok", "id": torrent_id}


@app.post("/torrents/{torrent_id}/queue/down", tags=["Queue"])
async def queue_down(torrent_id: str) -> dict[str, Any]:
    """Move torrent down in queue."""
    logger.info(f"Moving torrent {torrent_id} down in queue")
    _check(await client.queue_down(torrent_id))
    return {"status": "ok", "id": torrent_id}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
