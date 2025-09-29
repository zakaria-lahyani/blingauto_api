"""
Système de découverte automatique des features
"""
import importlib
import pkgutil
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from fastapi import APIRouter

logger = logging.getLogger(__name__)


class FeatureInfo:
    """Informations sur une feature"""
    
    def __init__(self, name: str, module_path: str):
        self.name = name
        self.module_path = module_path
        self._module = None
        self._router = None
        self._config = None
    
    @property
    def module(self):
        """Charge le module de la feature"""
        if self._module is None:
            try:
                self._module = importlib.import_module(self.module_path)
            except ImportError as e:
                logger.error(f"Cannot import feature {self.name}: {e}")
                raise
        return self._module
    
    def get_router(self) -> Optional[APIRouter]:
        """Récupère le router de la feature"""
        if self._router is None:
            try:
                if hasattr(self.module, 'get_router'):
                    self._router = self.module.get_router()
                elif hasattr(self.module, 'router'):
                    self._router = self.module.router
                else:
                    logger.warning(f"Feature {self.name} has no router")
                    return None
            except Exception as e:
                logger.error(f"Error getting router for feature {self.name}: {e}")
                return None
        return self._router
    
    def get_config(self) -> Optional[Any]:
        """Récupère la config de la feature"""
        if self._config is None:
            try:
                if hasattr(self.module, 'get_config'):
                    self._config = self.module.get_config()
                elif hasattr(self.module, 'config'):
                    self._config = self.module.config
                else:
                    logger.debug(f"Feature {self.name} has no config")
                    return None
            except Exception as e:
                logger.error(f"Error getting config for feature {self.name}: {e}")
                return None
        return self._config
    
    def is_enabled(self) -> bool:
        """Vérifie si la feature est activée"""
        from .simple_config import get_config
        app_config = get_config()
        return app_config.is_feature_enabled(self.name)
    
    async def initialize(self):
        """Initialise la feature si elle a une méthode d'initialisation"""
        try:
            if hasattr(self.module, 'initialize'):
                await self.module.initialize()
                logger.info(f"Feature {self.name} initialized")
            elif hasattr(self.module, 'init'):
                await self.module.init()
                logger.info(f"Feature {self.name} initialized")
        except Exception as e:
            logger.error(f"Error initializing feature {self.name}: {e}")
            raise
    
    async def shutdown(self):
        """Nettoie la feature si elle a une méthode de nettoyage"""
        try:
            if hasattr(self.module, 'shutdown'):
                await self.module.shutdown()
                logger.info(f"Feature {self.name} shutdown")
            elif hasattr(self.module, 'cleanup'):
                await self.module.cleanup()
                logger.info(f"Feature {self.name} shutdown")
        except Exception as e:
            logger.error(f"Error shutting down feature {self.name}: {e}")


class FeatureDiscovery:
    """Découvre automatiquement les features"""
    
    def __init__(self, features_path: str = "src.features"):
        self.features_path = features_path
        self._features: Dict[str, FeatureInfo] = {}
    
    def discover(self) -> List[FeatureInfo]:
        """Découvre toutes les features disponibles"""
        self._features.clear()
        
        try:
            # Import du package features
            features_module = importlib.import_module(self.features_path)
            features_dir = Path(features_module.__path__[0])
            
            # Parcourir tous les sous-dossiers
            for item in features_dir.iterdir():
                if item.is_dir() and not item.name.startswith('_'):
                    feature_name = item.name
                    module_path = f"{self.features_path}.{feature_name}"
                    
                    # Vérifier si le module a un __init__.py
                    init_file = item / "__init__.py"
                    if init_file.exists():
                        feature = FeatureInfo(feature_name, module_path)
                        self._features[feature_name] = feature
                        logger.debug(f"Discovered feature: {feature_name}")
        
        except ImportError as e:
            logger.error(f"Cannot import features package: {e}")
        except Exception as e:
            logger.error(f"Error discovering features: {e}")
        
        logger.info(f"Discovered {len(self._features)} features")
        return list(self._features.values())
    
    def get_enabled_features(self) -> List[FeatureInfo]:
        """Récupère uniquement les features activées"""
        if not self._features:
            self.discover()
        
        enabled = [feature for feature in self._features.values() if feature.is_enabled()]
        logger.info(f"Enabled features: {[f.name for f in enabled]}")
        return enabled
    
    def get_feature(self, name: str) -> Optional[FeatureInfo]:
        """Récupère une feature spécifique"""
        return self._features.get(name)
    
    def list_features(self) -> List[str]:
        """Liste les noms de toutes les features découvertes"""
        return list(self._features.keys())


# Instance globale
_discovery: Optional[FeatureDiscovery] = None


def get_feature_discovery() -> FeatureDiscovery:
    """Récupère l'instance de découverte des features"""
    global _discovery
    if _discovery is None:
        _discovery = FeatureDiscovery()
    return _discovery


def discover_features() -> List[FeatureInfo]:
    """Raccourci pour découvrir toutes les features"""
    return get_feature_discovery().discover()


def get_enabled_features() -> List[FeatureInfo]:
    """Raccourci pour récupérer les features activées"""
    return get_feature_discovery().get_enabled_features()