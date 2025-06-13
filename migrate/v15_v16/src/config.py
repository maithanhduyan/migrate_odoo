"""
Configuration loader for Odoo Migration v15 to v16
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, List
from pydantic import BaseModel, Field


class ProjectConfig(BaseModel):
    name: str
    version: str
    workspace_root: str


class EnvironmentConfig(BaseModel):
    docker_network: str
    health_check_timeout: int
    web_request_timeout: int
    log_level: str


class DatabaseConfig(BaseModel):
    container_name: str
    docker_compose_path: str
    data_path: str
    config_path: str
    host: str
    port: int
    database: str
    user: str
    password: str
    admin_user: str
    admin_password: str


class OdooConfig(BaseModel):
    container_name: str
    docker_compose_path: str
    config_path: str
    addons_path: str
    data_path: str
    log_path: str
    image: str
    web_port: int
    longpolling_port: int
    web_url: str
    database_selector_url: str
    config: Dict[str, Any]  # Add this field for the config section


class MigrationConfig(BaseModel):
    demo_database_v15: str
    demo_database_v16: str
    backup_path: str
    migration_phases: List[str]
    required_ports: List[int]


class Config(BaseModel):
    project: ProjectConfig
    environment: EnvironmentConfig
    postgresql: DatabaseConfig
    odoo_v15: OdooConfig
    odoo_v16: OdooConfig
    migration: MigrationConfig

    @classmethod
    def load_from_file(cls, config_path: str = "config.json") -> "Config":
        """Load configuration from JSON file"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        return cls(**config_data)

    @property
    def workspace_path(self) -> Path:
        """Get absolute workspace path"""
        return Path(os.path.abspath(self.project.workspace_root))

    def get_docker_compose_path(self, service: str) -> Path:
        """Get absolute docker-compose path for service"""
        if service == "postgresql":
            return self.workspace_path / self.postgresql.docker_compose_path
        elif service == "odoo_v15":
            return self.workspace_path / self.odoo_v15.docker_compose_path
        elif service == "odoo_v16":
            return self.workspace_path / self.odoo_v16.docker_compose_path
        else:
            raise ValueError(f"Unknown service: {service}")

    def get_config_path(self, service: str) -> Path:
        """Get absolute config path for service"""
        if service == "postgresql":
            return self.workspace_path / self.postgresql.config_path
        elif service == "odoo_v15":
            return self.workspace_path / self.odoo_v15.config_path
        elif service == "odoo_v16":
            return self.workspace_path / self.odoo_v16.config_path
        else:
            raise ValueError(f"Unknown service: {service}")


# Global config instance
_config: Config = None


def get_config() -> Config:
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = Config.load_from_file()
    return _config


def reload_config():
    """Reload configuration from file"""
    global _config
    _config = None
    return get_config()
