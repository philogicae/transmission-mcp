import logging
from json import dumps
from typing import Any

from fastmcp import FastMCP

from .wrapper import TransmissionClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TransmissionMCP")

mcp: FastMCP[Any] = FastMCP("Transmission")
client = TransmissionClient()


@mcp.tool()
async def get_session() -> str:
    """Get Transmission session configuration and version info."""
    logger.info("Getting session info")
    result = await client.get_session()
    if isinstance(result, str):
        logger.error(f"Error getting session: {result}")
        return f"Error getting session: {result}"
    return dumps(result)


@mcp.tool()
async def get_session_stats() -> str:
    """Get session statistics (speeds, torrent counts, cumulative stats)."""
    logger.info("Getting session stats")
    result = await client.get_session_stats()
    if isinstance(result, str):
        logger.error(f"Error getting session stats: {result}")
        return f"Error getting session stats: {result}"
    return dumps(result)


@mcp.tool()
async def free_space(path: str) -> str:
    """Get free disk space in bytes at the specified path."""
    logger.info(f"Getting free space at: {path}")
    result = await client.free_space(path)
    if isinstance(result, str):
        logger.error(f"Error getting free space: {result}")
        return f"Error getting free space: {result}"
    return dumps({"path": path, "freeSpace": result})


@mcp.tool()
async def list_torrents() -> str:
    """List all torrents with their details."""
    logger.info("Listing all torrents")
    result = await client.list_torrents()
    if isinstance(result, str):
        logger.error(f"Error listing torrents: {result}")
        return f"Error listing torrents: {result}"
    return dumps(result)


@mcp.tool()
async def get_torrent_details(torrent_id: str) -> str:
    """Get detailed info for a specific torrent by its ID or hash."""
    logger.info(f"Getting details for torrent: {torrent_id}")
    result = await client.get_torrent(torrent_id)
    if isinstance(result, str):
        logger.error(f"Error getting torrent details {torrent_id}: {result}")
        return f"Error getting torrent details {torrent_id}: {result}"
    return dumps(result)


@mcp.tool()
async def get_torrent_stats(torrent_id: str) -> str:
    """Get stats and status for a specific torrent by its ID or hash."""
    logger.info(f"Getting stats for torrent: {torrent_id}")
    result = await client.get_torrent(torrent_id)
    if isinstance(result, str):
        logger.error(f"Error getting torrent stats {torrent_id}: {result}")
        return f"Error getting torrent stats {torrent_id}: {result}"
    return dumps(result)


@mcp.tool()
async def get_recently_active() -> str:
    """Get recently active torrents and IDs of recently removed ones."""
    logger.info("Getting recently active torrents")
    result = await client.get_recently_active()
    if isinstance(result, str):
        logger.error(f"Error getting recently active: {result}")
        return f"Error getting recently active: {result}"
    return dumps(result)


@mcp.tool()
async def add_torrent(
    torrent: str, download_dir: str | None = None, paused: bool = False
) -> str:
    """Add a torrent from magnet link, HTTP URL, or local file path."""
    logger.info(f"Adding torrent: {torrent}")
    result = await client.add_torrent(torrent, download_dir=download_dir, paused=paused)
    if isinstance(result, str):
        logger.error(f"Error adding torrent: {result}")
        return f"Error adding torrent: {result}"
    return dumps(result)


@mcp.tool()
async def remove_torrent(torrent_id: str, delete_data: bool = False) -> str:
    """Remove a torrent. Set delete_data=True to also delete downloaded files."""
    logger.info(f"Removing torrent: {torrent_id} (delete_data={delete_data})")
    result = await client.remove_torrent(torrent_id, delete_data=delete_data)
    if isinstance(result, str):
        logger.error(f"Error removing torrent {torrent_id}: {result}")
        return f"Error removing torrent {torrent_id}: {result}"
    return f"Successfully removed torrent {torrent_id}"


@mcp.tool()
async def start_torrent(torrent_id: str) -> str:
    """Start (resume) a torrent."""
    logger.info(f"Starting torrent: {torrent_id}")
    result = await client.start_torrent(torrent_id)
    if isinstance(result, str):
        logger.error(f"Error starting torrent {torrent_id}: {result}")
        return f"Error starting torrent {torrent_id}: {result}"
    return f"Successfully started torrent {torrent_id}"


@mcp.tool()
async def stop_torrent(torrent_id: str) -> str:
    """Stop (pause) a torrent."""
    logger.info(f"Stopping torrent: {torrent_id}")
    result = await client.stop_torrent(torrent_id)
    if isinstance(result, str):
        logger.error(f"Error stopping torrent {torrent_id}: {result}")
        return f"Error stopping torrent {torrent_id}: {result}"
    return f"Successfully stopped torrent {torrent_id}"


@mcp.tool()
async def verify_torrent(torrent_id: str) -> str:
    """Verify torrent data integrity."""
    logger.info(f"Verifying torrent: {torrent_id}")
    result = await client.verify_torrent(torrent_id)
    if isinstance(result, str):
        logger.error(f"Error verifying torrent {torrent_id}: {result}")
        return f"Error verifying torrent {torrent_id}: {result}"
    return f"Successfully started verification for torrent {torrent_id}"


@mcp.tool()
async def reannounce_torrent(torrent_id: str) -> str:
    """Reannounce torrent to trackers."""
    logger.info(f"Reannouncing torrent: {torrent_id}")
    result = await client.reannounce_torrent(torrent_id)
    if isinstance(result, str):
        logger.error(f"Error reannouncing torrent {torrent_id}: {result}")
        return f"Error reannouncing torrent {torrent_id}: {result}"
    return f"Successfully reannounced torrent {torrent_id}"


@mcp.tool()
async def move_torrent(torrent_id: str, location: str, move: bool = True) -> str:
    """Move torrent data to a new location."""
    logger.info(f"Moving torrent {torrent_id} to: {location}")
    result = await client.move_torrent_data(torrent_id, location, move)
    if isinstance(result, str):
        logger.error(f"Error moving torrent {torrent_id}: {result}")
        return f"Error moving torrent {torrent_id}: {result}"
    return f"Successfully moved torrent {torrent_id}"


@mcp.tool()
async def set_torrent_labels(torrent_id: str, labels: list[str]) -> str:
    """Set labels for a torrent."""
    logger.info(f"Setting labels for torrent {torrent_id}: {labels}")
    result = await client.change_torrent(torrent_id, labels=labels)
    if isinstance(result, str):
        logger.error(f"Error setting labels for torrent {torrent_id}: {result}")
        return f"Error setting labels for torrent {torrent_id}: {result}"
    return f"Successfully updated labels for torrent {torrent_id}"


@mcp.tool()
async def download_torrent(magnet_link_or_url_or_path: str) -> str:
    """Download a torrent from a magnet link, HTTP URL, or local file."""
    logger.info(f"Downloading torrent from: {magnet_link_or_url_or_path}")
    result = await client.add_torrent(magnet_link_or_url_or_path)
    if isinstance(result, str):
        logger.error(f"Error downloading torrent: {result}")
        return f"Error downloading torrent: {result}"
    return dumps(result)


@mcp.tool()
async def pause_torrent(torrent_id: str) -> str:
    """Pause a torrent."""
    logger.info(f"Pausing torrent: {torrent_id}")
    result = await client.stop_torrent(torrent_id)
    if isinstance(result, str):
        logger.error(f"Error pausing torrent {torrent_id}: {result}")
        return f"Error pausing torrent {torrent_id}: {result}"
    return f"Successfully paused torrent {torrent_id}"


@mcp.tool()
async def delete_torrent(torrent_id: str) -> str:
    """Delete a torrent and its files."""
    logger.info(f"Deleting torrent: {torrent_id}")
    result = await client.remove_torrent(torrent_id, delete_data=True)
    if isinstance(result, str):
        logger.error(f"Error deleting torrent {torrent_id}: {result}")
        return f"Error deleting torrent {torrent_id}: {result}"
    return f"Successfully deleted torrent {torrent_id}"


@mcp.tool()
async def forget_torrent(torrent_id: str) -> str:
    """Forget a torrent, keeping the files."""
    logger.info(f"Forgetting torrent: {torrent_id}")
    result = await client.remove_torrent(torrent_id, delete_data=False)
    if isinstance(result, str):
        logger.error(f"Error forgetting torrent {torrent_id}: {result}")
        return f"Error forgetting torrent {torrent_id}: {result}"
    return f"Successfully forgot torrent {torrent_id}"
