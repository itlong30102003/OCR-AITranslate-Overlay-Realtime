"""
Configuration file for translation system
"""

import os
from typing import Dict, Any


class TranslationConfig:
    """Configuration class for translation system"""
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or 'config.env'
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables, config file, and defaults"""
        config = {}
        
        # Load from config file if exists
        if os.path.exists(self.config_file):
            config.update(self._load_from_file(self.config_file))
        
        # Override with environment variables
        config.update({
            # API Keys
            'gemini_api_key': os.getenv('GEMINI_API_KEY', config.get('gemini_api_key')),
            
            # Model Settings
            'nllb_model_size': os.getenv('NLLB_MODEL_SIZE', config.get('nllb_model_size', '600M')),
            'm2m_model_size': os.getenv('M2M_MODEL_SIZE', config.get('m2m_model_size', '418M')),
            
            # Translation Settings
            'default_target_lang': os.getenv('DEFAULT_TARGET_LANG', config.get('default_target_lang', 'vi')),
            'min_confidence': float(os.getenv('MIN_CONFIDENCE', config.get('min_confidence', '0.7'))),
            'max_text_length': int(os.getenv('MAX_TEXT_LENGTH', config.get('max_text_length', '1000'))),
            
            # Performance Settings
            'use_gpu': os.getenv('USE_GPU', config.get('use_gpu', 'true')).lower() == 'true',
            'cache_translations': os.getenv('CACHE_TRANSLATIONS', config.get('cache_translations', 'true')).lower() == 'true',
            'cache_size': int(os.getenv('CACHE_SIZE', config.get('cache_size', '1000'))),
            
            # Logging
            'log_level': os.getenv('LOG_LEVEL', config.get('log_level', 'INFO')),
            'log_translations': os.getenv('LOG_TRANSLATIONS', config.get('log_translations', 'false')).lower() == 'true',
        })
        
        return config
    
    def _load_from_file(self, filename: str) -> Dict[str, Any]:
        """Load configuration from file"""
        config = {}
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip().lower()
                        value = value.strip()
                        config[key] = value
        except Exception as e:
            print(f"Warning: Could not load config file {filename}: {e}")
        
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        self.config[key] = value
    
    def get_api_key(self, service: str) -> str:
        """Get API key for a service"""
        return self.config.get(f'{service}_api_key')
    
    def is_service_enabled(self, service: str) -> bool:
        """Check if a service is enabled"""
        return self.config.get(f'enable_{service}', True)
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get model configuration"""
        return {
            'nllb_model_size': self.config.get('nllb_model_size', '600M'),
            'm2m_model_size': self.config.get('m2m_model_size', '418M'),
            'use_gpu': self.config.get('use_gpu', True),
        }
    
    def get_translation_config(self) -> Dict[str, Any]:
        """Get translation configuration"""
        return {
            'default_target_lang': self.config.get('default_target_lang', 'vi'),
            'min_confidence': self.config.get('min_confidence', 0.7),
            'max_text_length': self.config.get('max_text_length', 1000),
        }
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration"""
        return {
            'cache_translations': self.config.get('cache_translations', True),
            'cache_size': self.config.get('cache_size', 1000),
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return self.config.copy()
    
    def update(self, new_config: Dict[str, Any]):
        """Update configuration with new values"""
        self.config.update(new_config)
    
    def save_to_env(self):
        """Save configuration to environment variables"""
        for key, value in self.config.items():
            if value is not None:
                os.environ[key.upper()] = str(value)


# Default configuration instance
default_config = TranslationConfig()
