"""Custom types for integration_blueprint."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import ArednNodeApiClient
    from .coordinator import ArednNodeDataUpdateCoordinator


type ArednNodeConfigEntry = ConfigEntry[ArednNodeData]


@dataclass
class ArednNodeData:
    """Data for the AREDN Node integration."""

    client: ArednNodeApiClient
    coordinator: ArednNodeDataUpdateCoordinator
    integration: Integration
