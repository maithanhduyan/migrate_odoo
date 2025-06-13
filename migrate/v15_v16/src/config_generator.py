"""
Odoo Configuration Generator
Generates optimized odoo.conf files from config.json settings
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any
import click
from rich.console import Console
from rich.panel import Panel

# Add src to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from config import get_config
from utils import setup_logging


class OdooConfigGenerator:
    """Generator for Odoo configuration files"""
    
    def __init__(self, config):
        self.config = config
        self.console = Console()
        self.logger = setup_logging(config.environment.log_level)
    
    def generate_odoo_v15_config(self) -> str:
        """Generate optimized Odoo v15 configuration"""
        v15_config = self.config.odoo_v15.config
        db_config = self.config.postgresql
        
        config_content = f"""[options]
# ========================================
# Odoo v15 Configuration (Auto-generated)
# ========================================

# Addons Configuration
addons_path = {v15_config['addons_path']}

# Database Configuration  
db_host = {db_config.host}
db_port = {db_config.port}
db_user = {db_config.user}
db_password = {db_config.password}
db_name = 
db_maxconn = 64
db_sslmode = prefer
db_template = template0

# Server Configuration
http_enable = True
http_interface = 
http_port = {v15_config['http_port']}
longpolling_port = {v15_config['longpolling_port']}
proxy_mode = {str(v15_config['proxy_mode']).lower()}

# Performance Configuration
workers = {v15_config['workers']}
max_cron_threads = {v15_config['max_cron_threads']}
limit_memory_hard = {v15_config['limit_memory_hard']}
limit_memory_soft = {v15_config['limit_memory_soft']}
limit_request = {v15_config['limit_request']}
limit_time_cpu = {v15_config['limit_time_cpu']}
limit_time_real = {v15_config['limit_time_real']}
limit_time_real_cron = {v15_config['limit_time_real_cron']}

# Logging Configuration
log_level = {v15_config['log_level']}
log_handler = {v15_config['log_handler']}
logfile = {v15_config['logfile']}
log_db = False
log_db_level = warning

# Data Configuration
data_dir = {v15_config['data_dir']}
csv_internal_sep = ,

# Security Configuration
admin_passwd = $pbkdf2-sha512$600000$Ruids3YOYaxVqpVyTglhjA$1nMppBRqU464.rSo4NhtOkWbIEtvh0uWHI/w.nt3g5ckmlZG24OXVdn7XRWVQeUeY6houab7uU81uRX9upb.Eg

# Database Management
list_db = {str(v15_config['list_db']).lower()}
dbfilter = 

# Server Wide Modules
server_wide_modules = {v15_config['server_wide_modules']}

# Email Configuration
email_from = False
smtp_server = localhost
smtp_port = 25
smtp_ssl = False
smtp_password = False

# Misc Configuration
demo = {{}}
import_partial = 
osv_memory_age_limit = False
osv_memory_count_limit = False
reportgz = False
"""
        return config_content.strip()
    
    def generate_odoo_v16_config(self) -> str:
        """Generate optimized Odoo v16 configuration"""
        v16_config = self.config.odoo_v16.config
        db_config = self.config.postgresql
        
        config_content = f"""[options]
# ========================================
# Odoo v16 Configuration (Auto-generated)
# ========================================

# Addons Configuration
addons_path = {v16_config['addons_path']}

# Database Configuration
db_host = {db_config.host}
db_port = {db_config.port}
db_user = {db_config.user}
db_password = {db_config.password}
db_name = 
db_maxconn = 64
db_sslmode = prefer
db_template = template0

# Server Configuration
http_enable = True
http_interface = 
http_port = {v16_config['http_port']}
longpolling_port = {v16_config['longpolling_port']}
proxy_mode = {str(v16_config['proxy_mode']).lower()}

# Performance Configuration
workers = {v16_config['workers']}
max_cron_threads = {v16_config['max_cron_threads']}
limit_memory_hard = {v16_config['limit_memory_hard']}
limit_memory_soft = {v16_config['limit_memory_soft']}
limit_request = {v16_config['limit_request']}
limit_time_cpu = {v16_config['limit_time_cpu']}
limit_time_real = {v16_config['limit_time_real']}
limit_time_real_cron = {v16_config['limit_time_real_cron']}

# Logging Configuration
log_level = {v16_config['log_level']}
log_handler = {v16_config['log_handler']}
logfile = {v16_config['logfile']}
log_db = False
log_db_level = warn

# Data Configuration
data_dir = {v16_config['data_dir']}
csv_internal_sep = ,

# Security Configuration (v16 enhanced)
admin_passwd = $pbkdf2-sha512$600000$CuFcay3lPCeEMCakNEaIMQ$3O5IF486YA41FGlaubRSzrvJpVu59iTvBzHpyzG/PL9BBfzXc3Lb4DdZfJ2TV6/YVHuyFMg/T5bFBoB3Sf/sOg
session_cookie_secure = {str(v16_config['session_cookie_secure']).lower()}
session_cookie_httponly = {str(v16_config['session_cookie_httponly']).lower()}

# Database Management
list_db = {str(v16_config['list_db']).lower()}
dbfilter = 

# Server Wide Modules
server_wide_modules = {v16_config['server_wide_modules']}

# Email Configuration
email_from = False
smtp_server = localhost
smtp_port = 25
smtp_ssl = False
smtp_password = False

# Misc Configuration
demo = {{}}
import_partial = 
osv_memory_age_limit = False
osv_memory_count_limit = False
reportgz = False
"""
        return config_content.strip()
    
    def backup_existing_config(self, config_path: Path) -> Path:
        """Backup existing configuration file"""
        if config_path.exists():
            backup_path = config_path.with_suffix('.conf.backup')
            config_path.rename(backup_path)
            self.logger.info(f"Backed up existing config to: {backup_path}")
            return backup_path
        return None
    
    def write_config_file(self, config_content: str, config_path: Path, service_name: str):
        """Write configuration content to file"""
        try:
            # Ensure directory exists
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Backup existing file
            self.backup_existing_config(config_path)
            
            # Write new configuration
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(config_content)
            
            self.console.print(f"✅ Generated {service_name} config: {config_path}", style="green")
            self.logger.info(f"Generated {service_name} configuration at {config_path}")
            
        except Exception as e:
            self.console.print(f"❌ Failed to write {service_name} config: {e}", style="red")
            self.logger.error(f"Failed to write {service_name} config: {e}")
            raise
    
    def generate_all_configs(self):
        """Generate all Odoo configuration files"""
        self.console.print(Panel(
            "Generating optimized Odoo configuration files from config.json",
            title="🔧 Config Generator",
            border_style="cyan"
        ))
        
        # Generate Odoo v15 config
        v15_content = self.generate_odoo_v15_config()
        v15_path = self.config.get_config_path('odoo_v15')
        self.write_config_file(v15_content, v15_path, "Odoo v15")
        
        # Generate Odoo v16 config
        v16_content = self.generate_odoo_v16_config()
        v16_path = self.config.get_config_path('odoo_v16')
        self.write_config_file(v16_content, v16_path, "Odoo v16")
        
        # Show summary
        self.show_config_summary()
    
    def show_config_summary(self):
        """Show configuration generation summary"""
        v15_config = self.config.odoo_v15.config
        v16_config = self.config.odoo_v16.config
        
        self.console.print("\n📊 Configuration Summary:", style="bold cyan")
        
        # Key differences
        differences = []
        if v15_config['limit_time_real_cron'] != v16_config['limit_time_real_cron']:
            differences.append(f"Cron timeout: v15={v15_config['limit_time_real_cron']}, v16={v16_config['limit_time_real_cron']}")
        
        if 'session_cookie_secure' in v16_config:
            differences.append("v16 includes enhanced security settings (session cookies)")
        
        if differences:
            self.console.print("🔍 Key differences between v15 and v16:")
            for diff in differences:
                self.console.print(f"  • {diff}", style="yellow")
        
        self.console.print("\n✅ Configuration files generated successfully!", style="bold green")
        self.console.print("💡 Restart containers to apply new configurations", style="blue")
    
    def validate_generated_configs(self):
        """Validate generated configuration files"""
        self.console.print("\n🔍 Validating generated configurations...", style="cyan")
        
        configs_to_check = [
            ("Odoo v15", self.config.get_config_path('odoo_v15')),
            ("Odoo v16", self.config.get_config_path('odoo_v16'))
        ]
        
        for name, path in configs_to_check:
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Basic validation
                    required_sections = ['[options]']
                    required_keys = ['db_host', 'db_user', 'addons_path', 'data_dir']
                    
                    missing = []
                    for section in required_sections:
                        if section not in content:
                            missing.append(section)
                    
                    for key in required_keys:
                        if f"{key} =" not in content:
                            missing.append(key)
                    
                    if missing:
                        self.console.print(f"⚠️ {name}: Missing {missing}", style="yellow")
                    else:
                        self.console.print(f"✅ {name}: Valid", style="green")
                        
                except Exception as e:
                    self.console.print(f"❌ {name}: Validation error - {e}", style="red")
            else:
                self.console.print(f"❌ {name}: File not found", style="red")


@click.command()
@click.option('--validate', '-v', is_flag=True, help='Validate generated configurations')
@click.option('--backup', '-b', is_flag=True, default=True, help='Backup existing configs (default: True)')
def main(validate, backup):
    """
    Generate optimized Odoo configuration files from config.json
    
    This command:
    - Reads settings from config.json
    - Generates clean, optimized odoo.conf files
    - Backs up existing configurations
    - Validates generated files
    """
    try:
        # Load configuration
        config = get_config()
        
        # Generate configurations
        generator = OdooConfigGenerator(config)
        generator.generate_all_configs()
        
        # Validate if requested
        if validate:
            generator.validate_generated_configs()
            
    except Exception as e:
        console = Console()
        console.print(f"❌ Configuration generation failed: {e}", style="bold red")
        sys.exit(1)


if __name__ == "__main__":
    main()
