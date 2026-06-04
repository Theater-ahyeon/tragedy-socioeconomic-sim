"""Configuration management endpoints — CRUD for simulation configs."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml
from fastapi import APIRouter, HTTPException

from tragedy.api.schemas import ConfigCreate, ConfigResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/configs", tags=["configs"])

CONFIGS_DIR = Path("configs")


@router.get("")
async def list_configs() -> list[ConfigResponse]:
    """List all available configuration files."""
    configs = []
    if CONFIGS_DIR.exists():
        for path in sorted(CONFIGS_DIR.glob("*.yaml")):
            name = path.stem
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                content = {"error": "Invalid YAML"}
            configs.append(ConfigResponse(name=name, content=content))
    return configs


@router.post("")
async def create_config(request: ConfigCreate) -> ConfigResponse:
    """Create a new configuration file.

    The config is saved as {name}.yaml in the configs directory.
    """
    path = CONFIGS_DIR / f"{request.name}.yaml"
    if path.exists():
        raise HTTPException(status_code=409, detail=f"Config '{request.name}' already exists")

    CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(request.content, f, default_flow_style=False, allow_unicode=True)

    logger.info("Created config: %s", request.name)
    return ConfigResponse(name=request.name, content=request.content)


@router.get("/{name}")
async def get_config(name: str) -> ConfigResponse:
    """Get a specific configuration."""
    path = CONFIGS_DIR / f"{name}.yaml"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Config '{name}' not found")

    with open(path, "r", encoding="utf-8") as f:
        content = yaml.safe_load(f) or {}

    return ConfigResponse(name=name, content=content)


@router.put("/{name}")
async def update_config(name: str, request: ConfigCreate) -> ConfigResponse:
    """Update an existing configuration."""
    path = CONFIGS_DIR / f"{name}.yaml"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Config '{name}' not found")

    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(request.content, f, default_flow_style=False, allow_unicode=True)

    logger.info("Updated config: %s", name)
    return ConfigResponse(name=name, content=request.content)


@router.delete("/{name}")
async def delete_config(name: str) -> dict[str, str]:
    """Delete a configuration file."""
    path = CONFIGS_DIR / f"{name}.yaml"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Config '{name}' not found")

    path.unlink()
    logger.info("Deleted config: %s", name)
    return {"status": "deleted", "name": name}
