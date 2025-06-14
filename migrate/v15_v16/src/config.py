"""
Configuration loader for Odoo Migration v15 to v16 (no pydantic)
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """Load configuration from JSON file as dict"""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = json.load(f)
    return config_data


_config: Optional[Dict[str, Any]] = None


def get_config() -> Dict[str, Any]:
    """Get global configuration as dict"""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config() -> Dict[str, Any]:
    """Reload configuration from file"""
    global _config
    _config = None
    return get_config()


# Helper functions for path resolution
def get_workspace_path(config: Dict[str, Any]) -> Path:
    return Path(os.path.abspath(config["project"]["workspace_root"]))


def get_docker_compose_path(config: Dict[str, Any], service: str) -> Path:
    workspace = get_workspace_path(config)
    if service == "postgresql":
        return workspace / config["postgresql"]["docker_compose_path"]
    elif service == "odoo_v15":
        return workspace / config["odoo_v15"]["docker_compose_path"]
    elif service == "odoo_v16":
        return workspace / config["odoo_v16"]["docker_compose_path"]
    else:
        raise ValueError(f"Unknown service: {service}")


def get_config_path(config: Dict[str, Any], service: str) -> Path:
    workspace = get_workspace_path(config)
    if service == "postgresql":
        return workspace / config["postgresql"]["config_path"]
    elif service == "odoo_v15":
        return workspace / config["odoo_v15"]["config_path"]
    elif service == "odoo_v16":
        return workspace / config["odoo_v16"]["config_path"]
    else:
        raise ValueError(f"Unknown service: {service}")
