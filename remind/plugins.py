"""Plugin system for Remind (MVP placeholder)."""

from abc import ABC, abstractmethod
from typing import Any


class RemindPlugin(ABC):
    """Base class for Remind plugins."""

    name: str = "base_plugin"
    version: str = "0.1.0"

    @abstractmethod
    def initialize(self, config: dict[str, Any]) -> None:
        """Initialize plugin with configuration."""
        pass

    @abstractmethod
    def on_reminder_due(self, reminder_text: str, reminder_id: int) -> None:
        """Called when a reminder is due."""
        pass

    def on_reminder_done(self, reminder_id: int) -> None:
        """Called when a reminder is marked done."""
        pass


class PluginManager:
    """Manages plugin discovery and execution."""

    def __init__(self):
        """Initialize plugin manager."""
        self.plugins: dict[str, RemindPlugin] = {}

    def register_plugin(self, plugin: RemindPlugin) -> None:
        """Register a plugin."""
        self.plugins[plugin.name] = plugin

    def get_plugin(self, name: str) -> RemindPlugin | None:
        """Get a plugin by name."""
        return self.plugins.get(name)

    def notify_reminder_due(self, reminder_text: str, reminder_id: int) -> None:
        """Notify all plugins that a reminder is due."""
        for plugin in self.plugins.values():
            try:
                plugin.on_reminder_due(reminder_text, reminder_id)
            except Exception as e:
                print(f"Error in plugin {plugin.name}: {e}")

    def notify_reminder_done(self, reminder_id: int) -> None:
        """Notify all plugins that a reminder is marked done."""
        for plugin in self.plugins.values():
            try:
                plugin.on_reminder_done(reminder_id)
            except Exception as e:
                print(f"Error in plugin {plugin.name}: {e}")
