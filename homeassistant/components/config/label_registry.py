"""HTTP views to interact with the label registry."""
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.components.websocket_api.connection import ActiveConnection
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.label_registry import LabelEntry, async_get


async def async_setup(hass: HomeAssistant) -> bool:
    """Enable the Label Registry views."""
    websocket_api.async_register_command(hass, websocket_list_labels)
    websocket_api.async_register_command(hass, websocket_create_label)
    websocket_api.async_register_command(hass, websocket_delete_label)
    websocket_api.async_register_command(hass, websocket_update_label)
    return True


@websocket_api.websocket_command(
    {
        vol.Required("type"): "config/label_registry/list",
        vol.Optional("label_id"): str,
    }
)
@callback
def websocket_list_labels(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Handle list labels command."""
    registry = async_get(hass)
    connection.send_result(
        msg["id"],
        [_entry_dict(entry) for entry in registry.async_list_labels()],
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): "config/label_registry/create",
        vol.Required("name"): str,
        vol.Optional("color"): vol.Any(str, None),
        vol.Optional("description"): vol.Any(str, None),
        vol.Optional("icon"): vol.Any(str, None),
    }
)
@websocket_api.require_admin
@callback
def websocket_create_label(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Create label command."""
    registry = async_get(hass)

    data = dict(msg)
    data.pop("type")
    data.pop("id")

    try:
        entry = registry.async_create(**data)
    except ValueError as err:
        connection.send_error(msg["id"], "invalid_info", str(err))
    else:
        connection.send_result(msg["id"], _entry_dict(entry))


@websocket_api.websocket_command(
    {
        vol.Required("type"): "config/label_registry/delete",
        vol.Required("label_id"): str,
    }
)
@websocket_api.require_admin
@callback
def websocket_delete_label(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Delete label command."""
    registry = async_get(hass)

    try:
        registry.async_delete(msg["label_id"])
    except KeyError:
        connection.send_error(msg["id"], "invalid_info", "Label ID doesn't exist")
    else:
        connection.send_message(websocket_api.result_message(msg["id"], "success"))


@websocket_api.websocket_command(
    {
        vol.Required("type"): "config/label_registry/update",
        vol.Required("label_id"): str,
        vol.Optional("color"): vol.Any(str, None),
        vol.Optional("description"): vol.Any(str, None),
        vol.Optional("icon"): vol.Any(str, None),
        vol.Optional("name"): str,
    }
)
@websocket_api.require_admin
@callback
def websocket_update_label(
    hass: HomeAssistant, connection: ActiveConnection, msg: dict[str, Any]
) -> None:
    """Handle update label websocket command."""
    registry = async_get(hass)

    data = dict(msg)
    data.pop("type")
    data.pop("id")

    try:
        entry = registry.async_update(**data)
    except ValueError as err:
        connection.send_error(msg["id"], "invalid_info", str(err))
    else:
        connection.send_result(msg["id"], _entry_dict(entry))


@callback
def _entry_dict(entry: LabelEntry) -> dict[str, Any]:
    """Convert entry to API format."""
    return {
        "color": entry.color,
        "description": entry.description,
        "icon": entry.icon,
        "label_id": entry.label_id,
        "name": entry.name,
    }