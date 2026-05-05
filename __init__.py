#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Plugin de Recomendações Inteligentes para Calibre
Recomenda livros similares baseado em metadados e análise textual opcional
"""

from calibre.customize import InterfaceActionBase
try:
    from calibre.utils.localization import load_translations
    load_translations()
except ImportError:
    pass

__license__ = 'GPL v3'
__copyright__ = '2024'
__docformat__ = 'restructuredtext en'

class RecommenderPlugin(InterfaceActionBase):
    """
    Plugin principal que adiciona ação de recomendação na interface do Calibre
    """
    
    name = 'Smart Book Recommender'
    description = 'Recomenda livros similares da sua biblioteca baseado em metadados e conteúdo'
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'Calibre Community'
    version = (1, 3, 2)
    minimum_calibre_version = (5, 0, 0)
    
    actual_plugin = 'calibre_plugins.recommender.ui:RecommenderAction'
    
    def is_customizable(self):
        """Plugin possui configurações customizáveis"""
        return True
    
    def config_widget(self):
        """Retorna widget de configuração"""
        from calibre_plugins.recommender.config import ConfigWidget
        return ConfigWidget()
    
    def save_settings(self, config_widget):
        """Salva configurações do plugin"""
        config_widget.save_settings()
