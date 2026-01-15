from __future__ import annotations

import os
from pathlib import Path
from typing import Any, BinaryIO

from dotenv import load_dotenv
from transmission_rpc import Client, Torrent, from_url
from transmission_rpc.error import (
    TransmissionAuthError,
    TransmissionConnectError,
    TransmissionError,
    TransmissionTimeoutError,
)

TorrentID = int | str


def _parse_id(id_or_hash: str) -> TorrentID:
    """Parse torrent ID from string (int ID or hash string)."""
    try:
        return int(id_or_hash)
    except ValueError:
        return id_or_hash


def _format_eta(eta) -> str | None:
    """Convert eta to formatted string or seconds.

    Returns:
    - 'not available' if eta is -1
    - 'unknown' if eta is -2
    - Formatted string as '<days> <hours>:<minutes>:<seconds>' for positive values
    - None for None input
    """
    if eta is None:
        return None

    # Handle special cases
    if eta == -1:
        return "not available"
    if eta == -2:
        return "unknown"

    # Handle timedelta objects
    if hasattr(eta, "total_seconds"):
        total_seconds = int(eta.total_seconds())
        if total_seconds < 0:
            return None
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        if days > 0:
            return f"{days} {hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    # Handle numeric values (seconds)
    try:
        total_seconds = int(eta)
        if total_seconds < 0:
            return None
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        if days > 0:
            return f"{days} {hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    except (ValueError, TypeError):
        return None


def _format_datetime(dt) -> str | None:
    """Convert datetime to ISO string."""
    return dt.isoformat() if dt else None


class TransmissionClient:
    """Client for interacting with the Transmission RPC API."""

    def __init__(
        self,
        url: str | None = None,
        timeout: float = 30.0,
    ):
        """Initialize the Transmission client.

        Args:
            url: Transmission RPC URL (e.g., http://localhost:9091/transmission/rpc)
                 Falls back to TRANSMISSION_URL env var or default localhost:9091
            timeout: Request timeout in seconds
        """
        load_dotenv()

        if url is None:
            url = os.getenv("TRANSMISSION_URL", "http://localhost:9091")

        if not url.startswith(("http://", "https://", "http+unix://")):
            url = f"http://{url}"

        username: str | None = os.getenv("TRANSMISSION_USER")
        password: str | None = os.getenv("TRANSMISSION_PASS")

        self._url = url
        self._username = username
        self._password = password
        self._timeout = timeout
        self._client: Client | None = None

    def _get_client(self) -> Client:
        """Get or create the Transmission RPC client with lazy initialization."""
        if self._client is not None:
            return self._client

        url = self._url
        if self._username and self._password:
            scheme_end = url.find("://")
            if scheme_end != -1:
                scheme = url[: scheme_end + 3]
                rest = url[scheme_end + 3 :]
                url = f"{scheme}{self._username}:{self._password}@{rest}"

        self._client = from_url(url, timeout=self._timeout)
        return self._client

    def _execute(self, func, *args, **kwargs) -> Any:
        """Execute a function with error handling, returning error string on failure."""
        try:
            return func(*args, **kwargs)
        except TransmissionAuthError as e:
            return f"Authentication error: {e}"
        except TransmissionTimeoutError as e:
            return f"Timeout error: {e}"
        except TransmissionConnectError as e:
            return f"Connection error: {e}"
        except TransmissionError as e:
            return f"Transmission error: {e}"
        except KeyError as e:
            return f"Torrent not found: {e}"
        except Exception as e:
            return f"Error: {e}"

    async def close(self) -> None:
        """Close the client connection."""
        self._client = None

    async def __aenter__(self) -> TransmissionClient:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    # -------------------------------------------------------------------------
    # Session Methods
    # -------------------------------------------------------------------------

    async def get_session(self) -> dict[str, Any] | str:
        """Get session configuration and information."""

        def _get():
            session = self._get_client().get_session()
            return {
                "version": session.version,
                "rpcVersion": session.rpc_version,
                "downloadDir": session.download_dir,
                "incompleteDir": session.incomplete_dir,
                "incompleteDirEnabled": session.incomplete_dir_enabled,
                "speedLimitDown": session.speed_limit_down,
                "speedLimitDownEnabled": session.speed_limit_down_enabled,
                "speedLimitUp": session.speed_limit_up,
                "speedLimitUpEnabled": session.speed_limit_up_enabled,
                "altSpeedDown": session.alt_speed_down,
                "altSpeedUp": session.alt_speed_up,
                "altSpeedEnabled": session.alt_speed_enabled,
                "peerPort": session.peer_port,
                "peerLimitGlobal": session.peer_limit_global,
                "peerLimitPerTorrent": session.peer_limit_per_torrent,
                "encryption": session.encryption,
                "dhtEnabled": session.dht_enabled,
                "pexEnabled": session.pex_enabled,
                "lpdEnabled": session.lpd_enabled,
                "utpEnabled": session.utp_enabled,
                "portForwardingEnabled": session.port_forwarding_enabled,
            }

        return self._execute(_get)

    async def get_session_stats(self) -> dict[str, Any] | str:
        """Get session statistics."""

        def _get():
            stats = self._get_client().session_stats()
            return {
                "activeTorrentCount": stats.active_torrent_count,
                "pausedTorrentCount": stats.paused_torrent_count,
                "torrentCount": stats.torrent_count,
                "downloadSpeed": stats.download_speed,
                "uploadSpeed": stats.upload_speed,
                "currentStats": {
                    "uploadedBytes": stats.current_stats.uploaded_bytes,
                    "downloadedBytes": stats.current_stats.downloaded_bytes,
                    "filesAdded": stats.current_stats.files_added,
                    "sessionCount": stats.current_stats.session_count,
                    "secondsActive": stats.current_stats.seconds_active,
                },
                "cumulativeStats": {
                    "uploadedBytes": stats.cumulative_stats.uploaded_bytes,
                    "downloadedBytes": stats.cumulative_stats.downloaded_bytes,
                    "filesAdded": stats.cumulative_stats.files_added,
                    "sessionCount": stats.cumulative_stats.session_count,
                    "secondsActive": stats.cumulative_stats.seconds_active,
                },
            }

        return self._execute(_get)

    async def set_session(self, **kwargs) -> None | str:
        """Update session settings.

        Supported kwargs (snake_case, will be converted):
            download_dir, incomplete_dir, incomplete_dir_enabled,
            speed_limit_down, speed_limit_down_enabled,
            speed_limit_up, speed_limit_up_enabled,
            alt_speed_down, alt_speed_up, alt_speed_enabled,
            peer_port, peer_limit_global, peer_limit_per_torrent,
            encryption, dht_enabled, pex_enabled, lpd_enabled, utp_enabled,
            port_forwarding_enabled, seed_ratio_limit, seed_ratio_limited,
            idle_seeding_limit, idle_seeding_limit_enabled, and more.
        """

        def _set():
            self._get_client().set_session(**kwargs)
            return None

        return self._execute(_set)

    async def free_space(self, path: str) -> int | str:
        """Get free space in bytes at the specified path."""

        def _get():
            return self._get_client().free_space(path)

        return self._execute(_get)

    async def port_test(self) -> bool | str:
        """Test if the incoming peer port is accessible."""

        def _test():
            return self._get_client().port_test()

        return self._execute(_test)

    async def blocklist_update(self) -> int | str:
        """Update the blocklist and return the new size."""

        def _update():
            return self._get_client().blocklist_update()

        return self._execute(_update)

    # -------------------------------------------------------------------------
    # Torrent List/Get Methods
    # -------------------------------------------------------------------------

    async def list_torrents(self) -> list[dict[str, Any]] | str:
        """List all torrents with basic info."""

        def _list():
            return [self._torrent_to_dict(t) for t in self._get_client().get_torrents()]

        return self._execute(_list)

    async def get_torrent(self, id_or_hash: str) -> dict[str, Any] | str:
        """Get detailed info for a specific torrent by ID or hash."""

        def _get():
            torrent = self._get_client().get_torrent(_parse_id(id_or_hash))
            return self._torrent_to_dict(torrent)

        return self._execute(_get)

    async def get_torrents(self, ids: list[str]) -> list[dict[str, Any]] | str:
        """Get info for multiple torrents by IDs or hashes."""

        def _get():
            parsed_ids = [_parse_id(i) for i in ids]
            return [
                self._torrent_to_dict(t)
                for t in self._get_client().get_torrents(parsed_ids)
            ]

        return self._execute(_get)

    async def get_recently_active(
        self,
    ) -> dict[str, list[dict[str, Any]] | list[int]] | str:
        """Get recently active torrents and IDs of recently removed torrents."""

        def _get():
            active, removed = self._get_client().get_recently_active_torrents()
            return {
                "active": [self._torrent_to_dict(t) for t in active],
                "removed": list(removed),
            }

        return self._execute(_get)

    # -------------------------------------------------------------------------
    # Torrent Add Methods
    # -------------------------------------------------------------------------

    async def add_torrent(
        self,
        torrent: str | bytes | BinaryIO | Path,
        download_dir: str | None = None,
        paused: bool = False,
        labels: list[str] | None = None,
        bandwidth_priority: int | None = None,
        cookies: str | None = None,
        files_unwanted: list[int] | None = None,
        files_wanted: list[int] | None = None,
        peer_limit: int | None = None,
        priority_high: list[int] | None = None,
        priority_low: list[int] | None = None,
        priority_normal: list[int] | None = None,
    ) -> dict[str, Any] | str:
        """Add a torrent from magnet link, URL, file path, or content.

        Args:
            torrent: Magnet link, HTTP(S) URL, file path, bytes, or file object
            download_dir: Directory to save files (optional)
            paused: Start paused if True
            labels: Optional list of labels (RPC 17+)
            bandwidth_priority: Priority for this transfer (-1 to 1)
            cookies: HTTP cookie(s) for URL-based torrents
            files_unwanted: List of file IDs that shouldn't be downloaded
            files_wanted: List of file IDs that should be downloaded
            peer_limit: Maximum number of peers allowed
            priority_high: List of file IDs that should have high priority
            priority_low: List of file IDs that should have low priority
            priority_normal: List of file IDs that should have normal priority
        """

        def _add():
            client = self._get_client()

            def _do_add(t: str | bytes | BinaryIO | Path):
                kwargs = {}
                if download_dir is not None:
                    kwargs["download_dir"] = download_dir
                if paused:
                    kwargs["paused"] = paused
                if labels is not None:
                    kwargs["labels"] = labels
                if bandwidth_priority is not None:
                    kwargs["bandwidth_priority"] = bandwidth_priority
                if cookies is not None:
                    kwargs["cookies"] = cookies
                if files_unwanted is not None:
                    kwargs["files_unwanted"] = files_unwanted
                if files_wanted is not None:
                    kwargs["files_wanted"] = files_wanted
                if peer_limit is not None:
                    kwargs["peer_limit"] = peer_limit
                if priority_high is not None:
                    kwargs["priority_high"] = priority_high
                if priority_low is not None:
                    kwargs["priority_low"] = priority_low
                if priority_normal is not None:
                    kwargs["priority_normal"] = priority_normal

                return client.add_torrent(t, **kwargs)

            if isinstance(torrent, (bytes, BinaryIO, Path)):
                result = _do_add(torrent)
            elif isinstance(torrent, str):
                if torrent.startswith(("magnet:", "http://", "https://")):
                    result = _do_add(torrent)
                elif os.path.isfile(torrent):
                    result = _do_add(Path(torrent))
                else:
                    raise ValueError(f"Invalid torrent source: {torrent}")
            else:
                raise ValueError(f"Unsupported torrent type: {type(torrent)}")

            return result

        # Execute the add operation
        result = self._execute(_add)

        # If result is a string error, return it as-is
        if isinstance(result, str):
            return result

        # Convert the torrent to dict, handling any potential errors
        try:
            return self._torrent_to_dict(result) if result else "Error: Add failed"
        except Exception as e:
            return f"Error converting torrent: {e}"

    # -------------------------------------------------------------------------
    # Torrent Control Methods
    # -------------------------------------------------------------------------

    async def start_torrent(self, id_or_hash: str) -> None | str:
        """Start (resume) a torrent."""

        def _start():
            self._get_client().start_torrent(_parse_id(id_or_hash))
            return None

        return self._execute(_start)

    async def start_torrents(self, ids: list[str]) -> None | str:
        """Start multiple torrents."""

        def _start():
            self._get_client().start_torrent([_parse_id(i) for i in ids])
            return None

        return self._execute(_start)

    async def start_all(self) -> None | str:
        """Start all torrents respecting queue order."""

        def _start():
            self._get_client().start_all()
            return None

        return self._execute(_start)

    async def stop_torrent(self, id_or_hash: str) -> None | str:
        """Stop (pause) a torrent."""

        def _stop():
            self._get_client().stop_torrent(_parse_id(id_or_hash))
            return None

        return self._execute(_stop)

    async def stop_torrents(self, ids: list[str]) -> None | str:
        """Stop multiple torrents."""

        def _stop():
            self._get_client().stop_torrent([_parse_id(i) for i in ids])
            return None

        return self._execute(_stop)

    async def verify_torrent(self, id_or_hash: str) -> None | str:
        """Verify torrent data integrity."""

        def _verify():
            self._get_client().verify_torrent(_parse_id(id_or_hash))
            return None

        return self._execute(_verify)

    async def reannounce_torrent(self, id_or_hash: str) -> None | str:
        """Reannounce torrent to trackers."""

        def _reannounce():
            self._get_client().reannounce_torrent(_parse_id(id_or_hash))
            return None

        return self._execute(_reannounce)

    async def remove_torrent(
        self, id_or_hash: str, delete_data: bool = False
    ) -> None | str:
        """Remove a torrent, optionally deleting downloaded data."""

        def _remove():
            self._get_client().remove_torrent(
                _parse_id(id_or_hash), delete_data=delete_data
            )
            return None

        return self._execute(_remove)

    async def remove_torrents(
        self, ids: list[str], delete_data: bool = False
    ) -> None | str:
        """Remove multiple torrents."""

        def _remove():
            self._get_client().remove_torrent(
                [_parse_id(i) for i in ids], delete_data=delete_data
            )
            return None

        return self._execute(_remove)

    # -------------------------------------------------------------------------
    # Torrent Modification Methods
    # -------------------------------------------------------------------------

    async def change_torrent(self, id_or_hash: str, **kwargs) -> None | str:
        """Change torrent settings.

        Supported kwargs:
            download_limit, download_limited, upload_limit, upload_limited,
            bandwidth_priority, honors_session_limits, peer_limit, queue_position,
            seed_ratio_limit, seed_ratio_mode, seed_idle_limit, seed_idle_mode,
            files_wanted, files_unwanted, priority_high, priority_low, priority_normal,
            labels (RPC 16+), tracker_list (RPC 17+), group (RPC 17+), and more.
        """

        def _change():
            self._get_client().change_torrent(_parse_id(id_or_hash), **kwargs)
            return None

        return self._execute(_change)

    async def move_torrent_data(
        self, id_or_hash: str, location: str, move: bool = True
    ) -> None | str:
        """Move torrent data to a new location."""

        def _move():
            self._get_client().move_torrent_data(
                _parse_id(id_or_hash), location, move=move
            )
            return None

        return self._execute(_move)

    async def rename_torrent_path(
        self, id_or_hash: str, path: str, name: str
    ) -> dict[str, str] | str:
        """Rename a file or directory within a torrent."""

        def _rename():
            result = self._get_client().rename_torrent_path(
                _parse_id(id_or_hash), path, name
            )
            return (
                {"path": result[0], "name": result[1]}
                if result
                else {"path": path, "name": name}
            )

        return self._execute(_rename)

    # -------------------------------------------------------------------------
    # Queue Methods
    # -------------------------------------------------------------------------

    async def queue_top(self, id_or_hash: str) -> None | str:
        """Move torrent to top of queue."""

        def _move():
            self._get_client().queue_top(_parse_id(id_or_hash))
            return None

        return self._execute(_move)

    async def queue_bottom(self, id_or_hash: str) -> None | str:
        """Move torrent to bottom of queue."""

        def _move():
            self._get_client().queue_bottom(_parse_id(id_or_hash))
            return None

        return self._execute(_move)

    async def queue_up(self, id_or_hash: str) -> None | str:
        """Move torrent up in queue."""

        def _move():
            self._get_client().queue_up(_parse_id(id_or_hash))
            return None

        return self._execute(_move)

    async def queue_down(self, id_or_hash: str) -> None | str:
        """Move torrent down in queue."""

        def _move():
            self._get_client().queue_down(_parse_id(id_or_hash))
            return None

        return self._execute(_move)

    # -------------------------------------------------------------------------
    # Bandwidth Groups
    # -------------------------------------------------------------------------

    async def set_group(
        self,
        name: str,
        honors_session_limits: bool = True,
        speed_limit_down_enabled: bool = False,
        speed_limit_down: int = 0,
        speed_limit_up_enabled: bool = False,
        speed_limit_up: int = 0,
    ) -> None | str:
        """Create or update a bandwidth group."""

        def _set():
            self._get_client().set_group(
                name=name,
                honors_session_limits=honors_session_limits,
                speed_limit_down_enabled=speed_limit_down_enabled,
                speed_limit_down=speed_limit_down,
                speed_limit_up_enabled=speed_limit_up_enabled,
                speed_limit_up=speed_limit_up,
            )
            return None

        return self._execute(_set)

    # -------------------------------------------------------------------------
    # Conversion Helpers
    # -------------------------------------------------------------------------

    def _torrent_to_dict(self, torrent: Torrent) -> dict[str, Any]:
        """Convert Torrent object to dictionary with all relevant fields."""

        # Use a helper function to safely get attributes
        def safe_get(attr, default=None):
            try:
                value = getattr(torrent, attr, default)
                return default if value is None else value
            except (AttributeError, KeyError):
                return default

        files = []
        file_stats = []
        try:
            for f in torrent.get_files():
                files.append(
                    {
                        "id": f.id,
                        "name": f.name,
                        "size": f.size,
                        "completed": f.completed,
                        "priority": f.priority,
                        "selected": f.selected,
                    }
                )
        except Exception:
            pass

        try:
            if hasattr(torrent, "file_stats") and torrent.file_stats:
                for i, f in enumerate(torrent.file_stats):
                    file_stats.append(
                        {
                            "index": i,
                            "bytesCompleted": f.bytesCompleted,
                            "priority": f.priority,
                            "wanted": f.wanted,
                        }
                    )
        except Exception:
            pass

        trackers = []
        try:
            if hasattr(torrent, "trackers") and torrent.trackers:
                for t in torrent.trackers:
                    trackers.append(
                        {
                            "id": t.id,
                            "tier": t.tier,
                            "announce": t.announce,
                            "scrape": t.scrape,
                        }
                    )
        except Exception:
            pass

        tracker_stats = []
        try:
            if hasattr(torrent, "tracker_stats") and torrent.tracker_stats:
                for t in torrent.tracker_stats:
                    tracker_stats.append(
                        {
                            "id": t.id,
                            "announce": t.announce,
                            "announceState": t.announce_state,
                            "downloadCount": t.download_count,
                            "hasAnnounced": t.has_announced,
                            "hasScraped": t.has_scraped,
                            "host": t.host,
                            "isBackup": t.is_backup,
                            "lastAnnouncePeerCount": t.last_announce_peer_count,
                            "lastAnnounceResult": t.last_announce_result,
                            "lastAnnounceStartTime": _format_datetime(
                                t.last_announce_start_time
                            ),
                            "lastAnnounceSucceeded": t.last_announce_succeeded,
                            "lastAnnounceTime": _format_datetime(t.last_announce_time),
                            "lastAnnounceTimedOut": t.last_announce_timed_out,
                            "lastScrapeResult": t.last_scrape_result,
                            "lastScrapeStartTime": _format_datetime(
                                t.last_scrape_start_time
                            ),
                            "lastScrapeSucceeded": t.last_scrape_succeeded,
                            "lastScrapeTime": _format_datetime(t.last_scrape_time),
                            "lastScrapeTimedOut": t.last_scrape_timed_out,
                            "leecherCount": t.leecher_count,
                            "nextAnnounceTime": _format_datetime(t.next_announce_time),
                            "nextScrapeTime": _format_datetime(t.next_scrape_time),
                            "scrapeState": t.scrape_state,
                            "scrape": t.scrape,
                            "seederCount": t.seeder_count,
                            "siteName": t.site_name,
                            "tier": t.tier,
                        }
                    )
        except Exception:
            pass

        # Handle status specially
        status = None
        try:
            status_val = safe_get("status")
            if status_val is not None:
                status = str(status_val)
        except Exception:
            pass

        # Handle peers_from if available
        peers_from = None
        try:
            if hasattr(torrent, "peers_from"):
                peers_from = {
                    "fromCache": safe_get("peers_from", {}).get("fromCache", 0),
                    "fromDht": safe_get("peers_from", {}).get("fromDht", 0),
                    "fromIncoming": safe_get("peers_from", {}).get("fromIncoming", 0),
                    "fromLpd": safe_get("peers_from", {}).get("fromLpd", 0),
                    "fromLtep": safe_get("peers_from", {}).get("fromLtep", 0),
                    "fromPex": safe_get("peers_from", {}).get("fromPex", 0),
                    "fromTracker": safe_get("peers_from", {}).get("fromTracker", 0),
                }
        except Exception:
            peers_from = None

        return {
            "id": safe_get("id"),
            "name": safe_get("name"),
            "hashString": safe_get("hash_string"),
            "infoHash": safe_get("info_hash"),
            "status": status,
            "error": safe_get("error"),
            "errorString": safe_get("error_string"),
            "percentDone": safe_get("percent_done", 0),
            "percentComplete": safe_get("percent_complete", 0),
            "metadataPercentComplete": safe_get("metadata_percent_complete", 0),
            "totalSize": safe_get("total_size", 0),
            "sizeWhenDone": safe_get("size_when_done", 0),
            "leftUntilDone": safe_get("left_until_done", 0),
            "downloadedEver": safe_get("downloaded_ever", 0),
            "uploadedEver": safe_get("uploaded_ever", 0),
            "uploadRatio": safe_get("upload_ratio", 0),
            "ratio": safe_get("ratio", 0),
            "rateDownload": safe_get("rate_download", 0),
            "rateUpload": safe_get("rate_upload", 0),
            "eta": _format_eta(safe_get("eta")),
            "peersSendingToUs": safe_get("peers_sending_to_us", 0),
            "peersGettingFromUs": safe_get("peers_getting_from_us", 0),
            "peersConnected": safe_get("peers_connected", 0),
            "peerLimit": safe_get("peer_limit", 0),
            "peersFrom": peers_from,
            "downloadDir": safe_get("download_dir"),
            "isFinished": safe_get("is_finished", False),
            "isStalled": safe_get("is_stalled", False),
            "isPrivate": safe_get("is_private", False),
            "priority": safe_get("priority", 0),
            "queuePosition": safe_get("queue_position", 0),
            "labels": list(safe_get("labels", [])) if safe_get("labels") else [],
            "addedDate": _format_datetime(safe_get("added_date")),
            "doneDate": _format_datetime(safe_get("done_date")),
            "startDate": _format_datetime(safe_get("start_date")),
            "activityDate": _format_datetime(safe_get("activity_date")),
            "editDate": _format_datetime(safe_get("edit_date")),
            "available": safe_get("available", 0),
            "bandwidthPriority": safe_get("bandwidth_priority", 0),
            "corruptEver": safe_get("corrupt_ever", 0),
            "desiredAvailable": safe_get("desired_available", 0),
            "haveUnchecked": safe_get("have_unchecked", 0),
            "haveValid": safe_get("have_valid", 0),
            "honorsSessionLimits": safe_get("honors_session_limits", False),
            "seedIdleMode": safe_get("seed_idle_mode"),
            "seedRatioLimit": safe_get("seed_ratio_limit", 0),
            "seedRatioMode": safe_get("seed_ratio_mode"),
            "webseedsSendingToUs": safe_get("webseeds_sending_to_us", 0),
            "sequentialDownload": safe_get("sequential_download", False),
            "trackers": trackers,
            "trackerStats": tracker_stats,
            "files": files,
            "fileStats": file_stats,
        }
