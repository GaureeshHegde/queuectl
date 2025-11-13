"""
Configuration management for queuectl
Handles default settings and user-defined configuration
"""
import json
import os
from pathlib import Path

class Config:
    """Manages queuectl configuration"""
    
    # Default configuration
    DEFAULTS = {
        'max_retries': 3,
        'backoff_base': 2,
        'data_dir': 'data',
        'jobs_dir': 'data/jobs',
        'dlq_dir': 'data/dlq',
        'config_file': 'data/config/settings.json'
    }
    
    def __init__(self, config_file=None):
        """Initialize configuration"""
        self.config_file = config_file or self.DEFAULTS['config_file']
        self.settings = self.DEFAULTS.copy()
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file if it exists"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                    self.settings.update(user_config)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
    
    def _save_config(self):
        """Save current configuration to file"""
        # Ensure config directory exists
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        # Save only non-default settings
        user_settings = {
            k: v for k, v in self.settings.items() 
            if k in ['max_retries', 'backoff_base']
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(user_settings, f, indent=2)
    
    def get(self, key, default=None):
        """Get configuration value"""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """Set configuration value"""
        # Validate and convert value
        if key == 'max_retries':
            value = int(value)
            if value < 0:
                raise ValueError("max_retries must be non-negative")
        elif key == 'backoff_base':
            value = float(value)
            if value < 1:
                raise ValueError("backoff_base must be >= 1")
        else:
            raise ValueError(f"Unknown configuration key: {key}")
        
        self.settings[key] = value
        self._save_config()
    
    def get_all(self):
        """Get all configuration settings"""
        return self.settings.copy()
    
    def ensure_directories(self):
        """Ensure all required directories exist"""
        for key in ['data_dir', 'jobs_dir', 'dlq_dir']:
            path = self.settings[key]
            os.makedirs(path, exist_ok=True)
        
        # Ensure config directory exists
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

# Global config instance
_config = None

def get_config():
    """Get global configuration instance"""
    global _config
    if _config is None:
        _config = Config()
        _config.ensure_directories()
    return _config
