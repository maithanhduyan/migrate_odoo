"""
Simple Config Generator for Odoo Migration v15 to v16
Generate clean odoo.conf files from config.json
"""
import json
import os
from pathlib import Path
from typing import Dict, Any


def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """Load configuration from JSON file"""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_odoo_config(version: str, config_data: Dict[str, Any]) -> str:
    """
    Generate odoo.conf content for specified version

    Args:
        version: 'v15' or 'v16'
        config_data: Configuration data from config.json

    Returns:
        Configuration file content as string
    """
    odoo_config = config_data[f'odoo_{version}']['config']
    db_config = config_data['postgresql']

    config_content = f"""[options]
# ========================================
# Odoo {version.upper()} Configuration (Auto-generated)
# ========================================

# Addons Configuration
addons_path = {odoo_config['addons_path']}

# Database Configuration
db_host = {db_config['host']}
db_port = {db_config['port']}
db_user = {db_config['user']}
db_password = {db_config['password']}
db_name =
db_maxconn = 64
db_sslmode = prefer

# Server Configuration
http_enable = True
http_interface =
http_port = {odoo_config['http_port']}
longpolling_port = {odoo_config['longpolling_port']}
proxy_mode = {str(odoo_config['proxy_mode']).lower()}

# Performance Configuration
workers = {odoo_config['workers']}
max_cron_threads = {odoo_config['max_cron_threads']}
limit_memory_hard = {odoo_config['limit_memory_hard']}
limit_memory_soft = {odoo_config['limit_memory_soft']}
limit_request = {odoo_config['limit_request']}
limit_time_cpu = {odoo_config['limit_time_cpu']}
limit_time_real = {odoo_config['limit_time_real']}
limit_time_real_cron = {odoo_config['limit_time_real_cron']}

# Logging Configuration
log_level = {odoo_config['log_level']}
log_handler = {odoo_config['log_handler']}
logfile = {odoo_config['logfile']}
log_db = False

# Data Configuration
data_dir = {odoo_config['data_dir']}

# Security Configuration
admin_passwd = $pbkdf2-sha512$600000$YourHashHere
list_db = {str(odoo_config['list_db']).lower()}

# Server Wide Modules
server_wide_modules = {odoo_config['server_wide_modules']}

# Email Configuration
email_from = False
smtp_server = localhost
smtp_port = 25
"""

    # Add version-specific configurations
    if version == 'v16':
        config_content += f"""
# Enhanced Security (v16)
session_cookie_secure = {str(odoo_config.get('session_cookie_secure', False)).lower()}
session_cookie_httponly = {str(odoo_config.get('session_cookie_httponly', True)).lower()}
"""

    return config_content.strip()


def write_config_file(content: str, file_path: str) -> bool:
    """
    Write configuration content to file

    Args:
        content: Configuration file content
        file_path: Path to write the file

    Returns:
        True if successful
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Backup existing file
        if os.path.exists(file_path):
            backup_path = file_path + '.backup'
            if os.path.exists(backup_path):
                os.remove(backup_path)
            os.rename(file_path, backup_path)
            print(f"✅ Backed up existing config to: {backup_path}")

        # Write new configuration
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ Generated config: {file_path}")
        return True

    except Exception as e:
        print(f"❌ Failed to write config {file_path}: {e}")
        return False


def generate_all_configs(config_path: str = "config.json") -> bool:
    """
    Generate all Odoo configuration files

    Args:
        config_path: Path to config.json

    Returns:
        True if all configs generated successfully
    """
    try:
        print("🔧 Generating Odoo configuration files...")

        # Load configuration
        config_data = load_config(config_path)

        # Get workspace root
        workspace_root = config_data['project']['workspace_root']

        # Generate v15 config
        v15_content = generate_odoo_config('v15', config_data)
        v15_path = os.path.join(
            workspace_root, config_data['odoo_v15']['config_path'])
        success_v15 = write_config_file(v15_content, v15_path)

        # Generate v16 config
        v16_content = generate_odoo_config('v16', config_data)
        v16_path = os.path.join(
            workspace_root, config_data['odoo_v16']['config_path'])
        success_v16 = write_config_file(v16_content, v16_path)

        if success_v15 and success_v16:
            print("\n✅ All configuration files generated successfully!")
            print("💡 Restart containers to apply new configurations")
            return True
        else:
            print("\n⚠️ Some configuration files failed to generate")
            return False

    except Exception as e:
        print(f"❌ Error generating configs: {e}")
        return False


if __name__ == "__main__":
    generate_all_configs()
