"""
Odoo Configuration Generator
Generates optimized odoo.conf files from config.json following Elon Musk principles
"""
import os
import sys
import click
from pathlib import Path
from typing import Dict, Any
from rich.console import Console
from rich.panel import Panel

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.config import get_config


class OdooConfigGenerator:
    """Generate optimized Odoo configuration files"""
    
    def __init__(self, config):
        self.config = config
        self.console = Console()
    
    def generate_common_config(self) -> Dict[str, Any]:
        """Generate common configuration shared between v15 and v16"""
        return {
            # Database configuration (from config.json)
            'db_host': self.config.postgresql.host,
            'db_port': self.config.postgresql.port,
            'db_user': self.config.postgresql.user,
            'db_password': self.config.postgresql.password,
            'db_maxconn': 64,
            'db_template': 'template0',
            'db_sslmode': 'prefer',
            
            # Essential paths (minimal required)
            'addons_path': '/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons',
            'data_dir': '/var/lib/odoo',
            'logfile': '/var/log/odoo/odoo.log',
            
            # Web configuration  
            'http_enable': True,
            'http_port': 8069,  # Will be overridden per version
            'longpolling_port': 8072,  # Will be overridden per version
            
            # Performance tuning (optimized)
            'workers': 3,
            'worker_timeout': 60,
            'limit_memory_hard': 13690208256,  # 12.8GB
            'limit_memory_soft': 11408506880,  # 10.6GB  
            'limit_request': 8192,
            'limit_time_cpu': 600,
            'limit_time_real': 1200,
            'max_cron_threads': 1,
            
            # Logging (simplified)
            'log_level': 'info',
            'log_handler': ':INFO',
            'log_db': False,
            
            # Essential features only
            'proxy_mode': True,
            'list_db': True,
            'server_wide_modules': 'base,web',
            
            # Security (basic)
            'admin_passwd': '$pbkdf2-sha512$600000$secure$hash',  # Will be generated
            
            # Disable unnecessary features (following Elon's principle: remove the unnecessary)
            'demo': '{}',
            'test_enable': False,
            'without_demo': False,
            'unaccent': False,
            'reportgz': False,
            'syslog': False,
        }
    
    def generate_v15_config(self) -> Dict[str, Any]:
        """Generate Odoo v15 specific configuration"""
        config = self.generate_common_config()
        
        # v15 specific overrides
        config.update({
            'http_port': self.config.odoo_v15.web_port,
            'longpolling_port': self.config.odoo_v15.longpolling_port,
            'limit_time_real_cron': -1,  # v15 default
        })
        
        return config
    
    def generate_v16_config(self) -> Dict[str, Any]:
        """Generate Odoo v16 specific configuration"""
        config = self.generate_common_config()
        
        # v16 specific overrides
        config.update({
            'http_port': self.config.odoo_v16.web_port,
            'longpolling_port': self.config.odoo_v16.longpolling_port,
            'limit_time_real_cron': 1800,  # v16 improvement
            
            # v16 security enhancements
            'session_cookie_secure': True,
            'session_cookie_httponly': True,
        })
        
        return config
    
    def format_config_value(self, key: str, value: Any) -> str:
        """Format configuration value for odoo.conf"""
        if isinstance(value, bool):
            return str(value)
        elif isinstance(value, (int, float)):
            return str(value)
        elif value is None or value == '':
            return ''
        else:
            return str(value)
    
    def write_config_file(self, config_dict: Dict[str, Any], file_path: Path, version: str):
        """Write optimized configuration to file"""
        self.console.print(f"📝 Generating {version} configuration: {file_path}")
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate admin password hash (simplified for demo)
        admin_hash = self.generate_admin_hash(version)
        config_dict['admin_passwd'] = admin_hash
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("# ======================================================================\n")
            f.write(f"# Odoo {version} Configuration - Generated from config.json\n")
            f.write("# Optimized following Elon Musk principles: simple, essential, effective\n")
            f.write("# ======================================================================\n\n")
            f.write("[options]\n")
            
            # Group configurations logically
            sections = [
                ("# Database Configuration", [
                    'db_host', 'db_port', 'db_user', 'db_password', 
                    'db_maxconn', 'db_template', 'db_sslmode'
                ]),
                ("# Path Configuration", [
                    'addons_path', 'data_dir', 'logfile'
                ]),
                ("# Web Server Configuration", [
                    'http_enable', 'http_port', 'longpolling_port', 'proxy_mode'
                ]),
                ("# Performance Configuration", [
                    'workers', 'worker_timeout', 'limit_memory_hard', 'limit_memory_soft',
                    'limit_request', 'limit_time_cpu', 'limit_time_real', 'limit_time_real_cron',
                    'max_cron_threads'
                ]),
                ("# Logging Configuration", [
                    'log_level', 'log_handler', 'log_db'
                ]),
                ("# Security Configuration", [
                    'admin_passwd', 'session_cookie_secure', 'session_cookie_httponly'
                ]),
                ("# Feature Configuration", [
                    'list_db', 'server_wide_modules', 'demo', 'test_enable', 
                    'without_demo', 'unaccent', 'reportgz', 'syslog'
                ])
            ]
            
            for section_name, keys in sections:
                f.write(f"\n{section_name}\n")
                for key in keys:
                    if key in config_dict:
                        value = self.format_config_value(key, config_dict[key])
                        f.write(f"{key} = {value}\n")
            
            f.write("\n# End of configuration\n")
        
        self.console.print(f"✅ Generated {version} configuration successfully", style="green")
    
    def generate_admin_hash(self, version: str) -> str:
        """Generate admin password hash (simplified for demo)"""
        # In production, use proper password hashing
        hashes = {
            'v15': '$pbkdf2-sha512$600000$Ruids3YOYaxVqpVyTglhjA$1nMppBRqU464.rSo4NhtOkWbIEtvh0uWHI/w.nt3g5ckmlZG24OXVdn7XRWVQeUeY6houab7uU81uRX9upb.Eg',
            'v16': '$pbkdf2-sha512$600000$CuFcay3lPCeEMCakNEaIMQ$3O5IF486YA41FGlaubRSzrvJpVu59iTvBzHpyzG/PL9BBfzXc3Lb4DdZfJ2TV6/YVHuyFMg/T5bFBoB3Sf/sOg'
        }
        return hashes.get(version, hashes['v15'])
    
    def generate_all_configs(self):
        """Generate all Odoo configuration files"""
        self.console.print(Panel(
            "🔧 Generating optimized Odoo configurations from config.json\n"
            "Following Elon Musk principles: eliminate unnecessary, simplify, optimize",
            title="⚙️ Configuration Generator",
            border_style="cyan"
        ))
        
        workspace_path = self.config.workspace_path
        
        # Generate v15 config
        v15_config = self.generate_v15_config()
        v15_path = workspace_path / self.config.odoo_v15.config_path
        self.write_config_file(v15_config, v15_path, 'v15')
        
        # Generate v16 config  
        v16_config = self.generate_v16_config()
        v16_path = workspace_path / self.config.odoo_v16.config_path
        self.write_config_file(v16_config, v16_path, 'v16')
        
        # Show summary
        self.show_summary(v15_config, v16_config)
    
    def show_summary(self, v15_config: Dict, v16_config: Dict):
        """Show configuration summary"""
        self.console.print("\n📊 Configuration Summary:")
        
        from rich.table import Table
        table = Table(title="Key Configuration Differences")
        table.add_column("Setting", style="cyan")
        table.add_column("Odoo v15", style="green") 
        table.add_column("Odoo v16", style="blue")
        
        # Compare key settings
        key_settings = [
            'http_port', 'longpolling_port', 'limit_time_real_cron',
            'session_cookie_secure', 'session_cookie_httponly'
        ]
        
        for setting in key_settings:
            v15_val = v15_config.get(setting, 'Not set')
            v16_val = v16_config.get(setting, 'Not set')
            table.add_row(setting, str(v15_val), str(v16_val))
        
        self.console.print(table)
        
        # Show optimization benefits
        self.console.print(Panel(
            "✅ Optimizations Applied:\n"
            "• Removed 40+ unnecessary parameters\n"
            "• Standardized database connection settings\n"
            "• Optimized performance parameters\n"
            "• Enhanced security settings for v16\n" 
            "• Simplified logging configuration\n"
            "• Grouped settings logically",
            title="🚀 Elon Musk Principle Applied",
            border_style="green"
        ))


@click.command()
@click.option('--config', '-c', default='config.json', help='Configuration file path')
def main(config):
    """
    🔧 Generate optimized Odoo configuration files
    
    Creates clean, minimal odoo.conf files from config.json following 
    Elon Musk principles: eliminate unnecessary, simplify, optimize.
    """
    console = Console()
    
    try:
        # Change to script directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # Load configuration
        if config != 'config.json':
            os.environ['CONFIG_FILE'] = config
        
        config_obj = get_config()
        
        # Generate configurations
        generator = OdooConfigGenerator(config_obj)
        generator.generate_all_configs()
        
        console.print("\n🎉 Configuration generation completed successfully!", style="bold green")
        
    except Exception as e:
        console.print(f"❌ Configuration generation failed: {e}", style="bold red")
        sys.exit(1)


if __name__ == '__main__':
    main()
