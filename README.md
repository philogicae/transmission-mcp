# Python API Wrapper & MCP Server for Transmission

[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://docs.astral.sh/uv/getting-started/installation/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![PyPI](https://badge.fury.io/py/transmission-mcp.svg?cache-control=no-cache)](https://badge.fury.io/py/transmission-mcp)
[![Actions status](https://github.com/philogicae/transmission-mcp/actions/workflows/python-package-ci.yml/badge.svg?cache-control=no-cache)](https://github.com/philogicae/transmission-mcp/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/philogicae/transmission-mcp)

This repository provides a Python API wrapper and an MCP (Model Context Protocol) server for the [Transmission](https://transmissionbt.com/) torrent client using the [transmission-rpc](https://github.com/Trim21/transmission-rpc) library. It allows for easy integration into other applications or services.

<a href="https://glama.ai/mcp/servers/@philogicae/transmission-mcp">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@philogicae/transmission-mcp/badge?cache-control=no-cache" alt="Transmission MCP server" />
</a>

## Table of Contents

- [Features](#features)
- [Setup](#setup)
  - [Prerequisites](#prerequisites)
  - [Configuration](#configuration)
  - [Installation](#installation)
    - [Install from PyPI (Recommended)](#install-from-pypi-recommended)
    - [For Local Development](#for-local-development)
    - [For Docker](#for-docker)
- [Usage](#usage)
  - [As Python API Wrapper](#as-python-api-wrapper)
  - [As MCP Server](#as-mcp-server)
  - [Via MCP Clients](#via-mcp-clients)
    - [Example with Windsurf](#example-with-windsurf)
- [Contributing](#contributing)
  - [Development](#development)
- [Changelog](#changelog)
- [License](#license)

## Features

- API wrapper for the `Transmission` torrent client using the official `transmission-rpc` library.
- MCP server interface for standardized communication (stdio, sse, streamable-http).
- Tools:
  - `get_session`: Get Transmission session configuration and version info.
  - `get_session_stats`: Get session statistics (speeds, torrent counts, cumulative stats).
  - `free_space`: Get free disk space in bytes at the specified path.
  - `list_torrents`: List all torrents and their details.
  - `get_torrent_details`: Get detailed information about a specific torrent.
  - `get_torrent_stats`: Get stats/status of a specific torrent.
  - `get_recently_active`: Get recently active torrents and IDs of recently removed ones.
  - `add_torrent`: Download a torrent from magnet link, HTTP URL, or local file.
  - `download_torrent`: Download a torrent from a magnet link, HTTP URL, or local file.
  - `start_torrent`: Start (resume) a torrent.
  - `stop_torrent`: Stop (pause) a torrent.
  - `pause_torrent`: Pause a torrent.
  - `verify_torrent`: Verify torrent data integrity.
  - `reannounce_torrent`: Reannounce torrent to trackers.
  - `move_torrent`: Move torrent data to a new location.
  - `set_torrent_labels`: Set labels for a torrent.
  - `remove_torrent`: Remove a torrent (optionally delete data).
  - `delete_torrent`: Delete a torrent and its files.
  - `forget_torrent`: Forget a torrent, keeping the files.

## Setup

### Prerequisites

- An running instance of [Transmission](https://transmissionbt.com/). (Included in docker compose)
- Python 3.10+ (required for PyPI install).
- [`uv`](https://github.com/astral-sh/uv) (for local development)

### Configuration

This application requires the URL of your `Transmission` instance.

**Set Environment Variable**: Copy `.env.example` to `.env` in your project's root directory and edit it with your settings. The application will automatically load variables from `.env`:

- MCP Server:
  - `TRANSMISSION_URL`: The URL of the Transmission instance (Default: `http://localhost:9091`).
  - `TRANSMISSION_USER`: The username for Transmission authentication (optional).
  - `TRANSMISSION_PASS`: The password for Transmission authentication (optional).
- Transmission Instance (for docker-compose setup):
  - `TRANSMISSION_DOWNLOAD_DIR`: The download directory for torrents (e.g., `/downloads`).
  - `TRANSMISSION_WATCH_DIR`: The watch directory for torrent files (e.g., `/watch`).
  - `TRANSMISSION_RPC_URL`: The RPC URL for the Transmission API (e.g., `http://localhost:9091/transmission/rpc`).
  - `TRANSMISSION_PEER_PORT`: The peer port for BitTorrent connections (e.g., `51413`).
  - `TRANSMISSION_SPEED_LIMIT_DOWN`: Download speed limit in KB/s (e.g., `100`).
  - `TRANSMISSION_SPEED_LIMIT_UP`: Upload speed limit in KB/s (e.g., `100`).
  - Check [Transmission](https://transmissionbt.com/) for other variables and more information.

### Installation

Choose one of the following installation methods.

#### Install from PyPI (Recommended)

This method is best for using the package as a library or running the server without modifying the code.

1.  Install the package from PyPI:

```bash
pip install transmission-mcp
```

2.  Create a `.env` file in the directory where you'll run the application and add your `Transmission` URL:

```env
TRANSMISSION_URL=http://localhost:9091
```

3.  Run the MCP server (default: stdio):

```bash
python -m transmission_client
```

#### For Local Development

This method is for contributors who want to modify the source code.
Using [`uv`](https://github.com/astral-sh/uv):

1.  Clone the repository:

```bash
git clone https://github.com/philogicae/transmission-mcp.git
cd transmission-mcp
```

2.  Install dependencies using `uv`:

```bash
uv sync --locked
```

3.  Create your configuration file by copying the example and add your settings:

```bash
cp .env.example .env
```

4.  Run the MCP server (default: stdio):

```bash
uv run -m transmission_client
```

#### For Docker

This method uses Docker to run the server in a container.
compose.yaml includes [Transmission](https://transmissionbt.com/) torrent client.

1.  Clone the repository (if you haven't already):

```bash
git clone https://github.com/philogicae/transmission-mcp.git
cd transmission-mcp
```

2.  Create your configuration file by copying the example and add your settings:

```bash
cp .env.example .env
```

3.  Build and run the container using Docker Compose (default port: 8000):

```bash
docker compose up --build -d
```

4.  Access container logs:

```bash
docker logs transmission-mcp -f
```

## Usage

### As Python API Wrapper

```python
import asyncio
from transmission_client import TransmissionClient

async def main():
    # Initialize client (reads TRANSMISSION_URL, TRANSMISSION_USER, and TRANSMISSION_PASS from env)
    client = TransmissionClient()

    # Use as context manager for automatic cleanup
    async with TransmissionClient() as client:
        # Get session info
        session = await client.get_session()
        print(f"Transmission version: {session['version']}")

        # Get session statistics
        stats = await client.get_session_stats()
        print(f"Download speed: {stats['downloadSpeed']} bytes/s")

        # Check free space
        free_space = await client.free_space("/downloads")
        print(f"Free space: {free_space} bytes")

    # List all torrents
    torrents = await client.list_torrents()

    # Add a torrent
    await client.add_torrent("magnet:?xt=urn:btih:...")

    # Get torrent details
        details = await client.get_torrent("1")  # Use ID or hash

    # Control torrents
        await client.stop_torrent("1")  # Pause
        await client.start_torrent("1")  # Resume

        # Verify torrent data
        await client.verify_torrent("1")

        # Move torrent data
        await client.move_torrent("1", "/new/location", move=True)

        # Set torrent labels
        await client.set_torrent_labels("1", ["movies", "4k"])

        # Remove torrent (keep files)
        await client.remove_torrent("1", delete_data=False)

        # Delete torrent and files
        await client.remove_torrent("1", delete_data=True)

if __name__ == "__main__":
    asyncio.run(main())
```

### As MCP Server

```python
from transmission_client import TransmissionMCP

TransmissionMCP.run(transport="sse") # 'stdio', 'sse', or 'streamable-http'
```

### Via MCP Clients

Usable with any MCP-compatible client. Available tools:

- `get_session`: Get Transmission session configuration and version info.
- `get_session_stats`: Get session statistics (speeds, torrent counts, cumulative stats).
- `free_space`: Get free disk space in bytes at the specified path.
- `list_torrents`: List all torrents and their details.
- `get_torrent_details`: Get details of a specific torrent by ID or hash.
- `get_torrent_stats`: Get stats/status of a specific torrent by ID or hash.
- `get_recently_active`: Get recently active torrents and IDs of recently removed ones.
- `add_torrent`: Add a torrent from magnet link, HTTP URL, or local file path.
- `download_torrent`: Download a torrent via magnet link, HTTP URL, or local file.
- `start_torrent`: Start (resume) a torrent by ID or hash.
- `stop_torrent`: Stop (pause) a torrent by ID or hash.
- `pause_torrent`: Pause a torrent by ID or hash.
- `verify_torrent`: Verify torrent data integrity by ID or hash.
- `reannounce_torrent`: Reannounce torrent to trackers by ID or hash.
- `move_torrent`: Move torrent data to a new location by ID or hash.
- `set_torrent_labels`: Set labels for a torrent by ID or hash.
- `remove_torrent`: Remove a torrent (optionally delete data) by ID or hash.
- `delete_torrent`: Delete a torrent and its files by ID or hash.
- `forget_torrent`: Forget a torrent, keeping the files, by ID or hash.

#### Example with Windsurf

Configuration:

```json
{
  "mcpServers": {
    ...
    # with stdio (only requires uv)
    "transmission-mcp": {
      "command": "uvx",
      "args": [ "transmission-mcp" ],
      "env": {
        "TRANSMISSION_URL": "http://localhost:9091", # (Optional) Default Transmission instance URL
        "TRANSMISSION_USER": "username", # (Optional) Transmission username
        "TRANSMISSION_PASS": "password" # (Optional) Transmission password
      }
    },
    # with docker (only requires docker)
    "transmission-mcp": {
      "command": "docker",
      "args": [ "run", "-i", "-p", "8000:8000", "-e", "TRANSMISSION_URL=http://localhost:9091", "-e", "TRANSMISSION_USER=username", "-e", "TRANSMISSION_PASS=password", "philogicae/transmission-mcp:latest", "transmission-mcp" ]
    },
    # with sse transport (requires installation)
    "transmission-mcp": {
      "serverUrl": "http://127.0.0.1:8000/sse"
    },
    # with streamable-http transport (requires installation)
    "transmission-mcp": {
      "serverUrl": "http://127.0.0.1:8000/mcp"
    },
    ...
  }
}
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a history of changes to this project.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
