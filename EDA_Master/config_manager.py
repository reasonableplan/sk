# config_manager.py
"""
사용자 설정 관리 모듈
설정을 JSON 파일로 저장/로드
"""
import json
import os
from pathlib import Path

class ConfigManager:
    """설정 관리 클래스"""
    
    DEFAULT_CONFIG = {
        'window': {
            'width': 1200,
            'height': 800,
            'maximized': True
        },
        'data': {
            'last_file': '',
            'auto_load_last': False,
            'sample_threshold': 10000
        },
        'ai': {
            'timeout': 30,
            'use_cache': True,
            'preferred_model': 'gemini-2.0-flash-exp'
        },
        'ml': {
            'default_model': 'xgboost',
            'test_size': 0.2,
            'random_state': 42,
            'use_cv': False,
            'cv_folds': 5
        },
        'ui': {
            'theme': 'light',
            'font_size': 14,
            'show_tooltips': True
        }
    }
    
    def __init__(self, config_path=None):
        """
        Parameters:
        -----------
        config_path : str, optional
            설정 파일 경로. None이면 기본 경로 사용
        """
        if config_path is None:
            # 사용자 홈 디렉토리에 설정 파일 저장
            home = Path.home()
            config_dir = home / '.eda_master'
            config_dir.mkdir(exist_ok=True)
            self.config_path = config_dir / 'config.json'
        else:
            self.config_path = Path(config_path)
        
        self.config = self.load()
    
    def load(self):
        """설정 파일 로드"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                # 기본 설정과 병합 (새로운 설정 항목 추가를 위해)
                return self._merge_configs(self.DEFAULT_CONFIG, loaded_config)
            except Exception as e:
                print(f"설정 로드 실패: {e}")
                return self.DEFAULT_CONFIG.copy()
        else:
            return self.DEFAULT_CONFIG.copy()
    
    def save(self):
        """설정 파일 저장"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"설정 저장 실패: {e}")
            return False
    
    def get(self, key, default=None):
        """설정값 가져오기 (점 표기법 지원: 'window.width')"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def set(self, key, value):
        """설정값 설정하기 (점 표기법 지원)"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
    
    def reset(self):
        """설정 초기화"""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save()
    
    def _merge_configs(self, default, loaded):
        """기본 설정과 로드된 설정 병합"""
        merged = default.copy()
        for key, value in loaded.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        return merged
