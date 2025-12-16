"""Sensor platform for AREDN Node integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfFrequency, UnitOfInformation
from homeassistant.helpers.entity import EntityCategory

from .entity import ArednNodeEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import ArednNodeDataUpdateCoordinator
    from .data import ArednNodeConfigEntry


@dataclass(frozen=True, kw_only=True)
class ArednNodeSensorEntityDescription(SensorEntityDescription):
    """Describes AREDN Node sensor entity."""

    value_fn: Callable[[dict[str, Any]], str | int | None]
    attr_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


def _get_sysinfo_value(key: str) -> Callable[[dict[str, Any]], str | int | None]:
    """Get a value from the sysinfo dict."""
    return lambda data: data.get("sysinfo", {}).get(key)


def _get_meshrf_value(key: str) -> Callable[[dict[str, Any]], str | int | None]:
    """Get a value from the meshrf dict."""
    return lambda data: data.get("meshrf", {}).get(key)


ENTITY_DESCRIPTIONS: tuple[ArednNodeSensorEntityDescription, ...] = (
    ArednNodeSensorEntityDescription(
        key="uptime",
        name="Uptime",
        icon="mdi:timer-sand",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_get_sysinfo_value("uptime"),
    ),
    ArednNodeSensorEntityDescription(
        key="freememory",
        name="Free Memory",
        native_unit_of_measurement=UnitOfInformation.KILOBYTES,
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_get_sysinfo_value("freememory"),
    ),
    ArednNodeSensorEntityDescription(
        key="load_1m",
        name="Load (1m)",
        icon="mdi:chart-line",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("sysinfo", {}).get("loads", [None])[0],
    ),
    ArednNodeSensorEntityDescription(
        key="load_5m",
        name="Load (5m)",
        icon="mdi:chart-line",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("sysinfo", {}).get("loads", [None, None])[1],
    ),
    ArednNodeSensorEntityDescription(
        key="load_15m",
        name="Load (15m)",
        icon="mdi:chart-line",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("sysinfo", {}).get("loads", [None, None, None])[
            2
        ],
    ),
    ArednNodeSensorEntityDescription(
        key="meshrf_status",
        name="Mesh RF Status",
        icon="mdi:wifi",
        value_fn=_get_meshrf_value("status"),
    ),
    ArednNodeSensorEntityDescription(
        key="meshrf_ssid",
        name="Mesh RF SSID",
        icon="mdi:wifi-settings",
        value_fn=_get_meshrf_value("ssid"),
    ),
    ArednNodeSensorEntityDescription(
        key="meshrf_freq",
        name="Mesh RF Frequency",
        native_unit_of_measurement=UnitOfFrequency.MEGAHERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:radio-tower",
        value_fn=_get_meshrf_value("freq"),
    ),
    ArednNodeSensorEntityDescription(
        key="meshrf_chanbw",
        name="Mesh RF Channel Bandwidth",
        native_unit_of_measurement=UnitOfFrequency.MEGAHERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:arrow-expand-horizontal",
        value_fn=_get_meshrf_value("chanbw"),
    ),
    ArednNodeSensorEntityDescription(
        key="link_info",
        name="Linked Nodes",
        icon="mdi:lan-connect",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: len(data.get("link_info", {})),
        attr_fn=lambda data: {
            "links": [v.get("hostname") for v in data.get("link_info", {}).values()]
        },
    ),
    ArednNodeSensorEntityDescription(
        key="nodes",
        name="Mesh Nodes",
        icon="mdi:lan",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: len(data.get("nodes", [])),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: ArednNodeConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = entry.runtime_data.coordinator

    entities: list[ArednNodeSensor] = [
        ArednNodeSensor(
            coordinator=coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    ]

    # Create sensors for each interface, disabled by default
    if coordinator.data and "interfaces" in coordinator.data:
        for interface in coordinator.data["interfaces"]:
            if "ip" in interface:
                entities.append(
                    ArednNodeInterfaceSensor(
                        coordinator=coordinator,
                        interface_name=interface["name"],
                    )
                )

    async_add_entities(entities)


class ArednNodeSensor(ArednNodeEntity, SensorEntity):
    """AREDN Node sensor class."""

    entity_description: ArednNodeSensorEntityDescription

    def __init__(
        self,
        coordinator: ArednNodeDataUpdateCoordinator,
        entity_description: ArednNodeSensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}-{entity_description.key}"
        )

    @property
    def native_value(self) -> str | int | None:
        """Return the native value of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the state attributes."""
        if self.entity_description.attr_fn:
            return self.entity_description.attr_fn(self.coordinator.data)
        return None


class ArednNodeInterfaceSensor(ArednNodeEntity, SensorEntity):
    """AREDN Node interface sensor class."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: ArednNodeDataUpdateCoordinator,
        interface_name: str,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self._interface_name = interface_name
        self._attr_name = f"Interface {interface_name}"
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}-iface-{interface_name}"
        )

    @property
    def native_value(self) -> str | None:
        """Return the native value of the sensor."""
        for interface in self.coordinator.data.get("interfaces", []):
            if interface.get("name") == self._interface_name:
                return interface.get("ip")
        return None
