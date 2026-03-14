"""Hot-reload registry — tracks dynamically loaded handler modules.

When SelfUpgradeEngine writes a new handler file, this registry:
1. Imports the module
2. Extracts its Router
3. Includes it in the running aiogram Dispatcher

This means new /commands are available immediately without restarting.
The Telegram connection stays alive throughout.
"""
from __future__ import annotations

import importlib
import importlib.util
import logging
import sys
from pathlib import Path
from typing import Dict, Optional, Set

logger = logging.getLogger(__name__)


class HotReloadRegistry:
    """Manages dynamic loading of aiogram Router modules."""

    def __init__(self, dp=None):  # dp: aiogram.Dispatcher
        self._dp = dp
        self._loaded: Dict[str, object] = {}   # module_name -> Router
        self._module_paths: Dict[str, str] = {}  # module_name -> file path

    def set_dispatcher(self, dp) -> None:
        self._dp = dp

    async def load_handler(
        self,
        file_path: str,
        bot_root: Path = Path("."),
    ) -> bool:
        """Dynamically load a handler file and register its Router."""
        path = bot_root / file_path
        if not path.exists():
            logger.error("Handler file not found: %s", path)
            return False

        module_name = file_path.replace("/", ".").replace("\\", ".").removesuffix(".py")

        try:
            if module_name in sys.modules:
                # Reload existing module
                old_mod = sys.modules[module_name]
                mod = importlib.reload(old_mod)
                logger.info("Reloaded module: %s", module_name)
            else:
                # Fresh import
                spec = importlib.util.spec_from_file_location(module_name, path)
                mod = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = mod
                spec.loader.exec_module(mod)
                logger.info("Loaded new module: %s", module_name)

            # Register Router if present
            if hasattr(mod, "router") and self._dp:
                self._dp.include_router(mod.router)
                self._loaded[module_name] = mod.router
                self._module_paths[module_name] = file_path
                logger.info("Registered router from: %s", module_name)

            return True

        except Exception as e:
            logger.error("Failed to load handler %s: %s", module_name, e)
            return False

    def get_loaded_modules(self) -> Dict[str, str]:
        """Return {module_name: file_path} for all dynamically loaded modules."""
        return dict(self._module_paths)

    @property
    def loaded_count(self) -> int:
        return len(self._loaded)


# Global singleton — set dp reference in main.py on_startup
_registry = HotReloadRegistry()


def get_registry() -> HotReloadRegistry:
    return _registry
