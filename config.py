#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Widget de Configuração do Plugin
"""

try:
    # Calibre 8.x usa PyQt6
    from PyQt6.Qt import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, 
                          QSpinBox, QPushButton, QGroupBox, QFormLayout, QMessageBox)
    StandardButton = QMessageBox.StandardButton
except ImportError:
    # Fallback para PyQt5
    from PyQt5.Qt import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox, 
                          QSpinBox, QPushButton, QGroupBox, QFormLayout, QMessageBox)
    StandardButton = QMessageBox

from calibre.utils.config import JSONConfig


class ConfigWidget(QWidget):
    """
    Widget de configuração do plugin
    """
    
    def __init__(self):
        QWidget.__init__(self)
        self.prefs = JSONConfig('plugins/recommender')
        self.prefs.defaults['use_tfidf'] = False
        self.prefs.defaults['min_similarity'] = 0.1
        self.prefs.defaults['default_top_n'] = 20
        
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        """Configura interface"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Grupo: Algoritmo
        algo_group = QGroupBox('Configurações do Algoritmo')
        algo_layout = QFormLayout()
        algo_group.setLayout(algo_layout)
        
        # Checkbox TF-IDF
        self.tfidf_checkbox = QCheckBox()
        self.tfidf_checkbox.setToolTip(
            'Usa análise textual (TF-IDF) para melhorar recomendações.\n'
            'Requer scikit-learn instalado.\n'
            'Pode tornar a primeira busca mais lenta.'
        )
        algo_layout.addRow('Usar análise textual (TF-IDF):', self.tfidf_checkbox)
        
        # Número de recomendações
        self.top_n_spinbox = QSpinBox()
        self.top_n_spinbox.setMinimum(5)
        self.top_n_spinbox.setMaximum(50)
        self.top_n_spinbox.setSingleStep(5)
        self.top_n_spinbox.setToolTip('Número de recomendações a exibir')
        algo_layout.addRow('Número de recomendações:', self.top_n_spinbox)
        
        # Similaridade mínima
        self.min_sim_spinbox = QSpinBox()
        self.min_sim_spinbox.setMinimum(0)
        self.min_sim_spinbox.setMaximum(100)
        self.min_sim_spinbox.setSingleStep(5)
        self.min_sim_spinbox.setSuffix('%')
        self.min_sim_spinbox.setToolTip('Similaridade mínima para exibir recomendação (0-100%)')
        algo_layout.addRow('Similaridade mínima:', self.min_sim_spinbox)
        
        layout.addWidget(algo_group)
        
        # Grupo: Cache
        cache_group = QGroupBox('Gerenciamento de Cache')
        cache_layout = QVBoxLayout()
        cache_group.setLayout(cache_layout)
        
        cache_info = QLabel(
            'O plugin mantém um índice da sua biblioteca para busca rápida.\n'
            'Este índice é atualizado automaticamente quando a biblioteca muda.'
        )
        cache_info.setWordWrap(True)
        cache_layout.addWidget(cache_info)
        
        rebuild_button = QPushButton('Reconstruir Índice Agora')
        rebuild_button.setToolTip('Força reconstrução do índice de metadados')
        rebuild_button.clicked.connect(self._rebuild_index)
        cache_layout.addWidget(rebuild_button)
        
        layout.addWidget(cache_group)
        
        # Informações
        info_group = QGroupBox('Informações')
        info_layout = QVBoxLayout()
        info_group.setLayout(info_layout)
        
        info_text = QLabel(
            '<b>Como funciona:</b><br/>'
            'O plugin analisa tags, autores, séries, editoras e anos de publicação '
            'para encontrar livros similares em sua biblioteca.<br/><br/>'
            '<b>Dicas para melhores resultados:</b><br/>'
            '• Mantenha tags organizadas e consistentes<br/>'
            '• Preencha metadados (autor, série, editora)<br/>'
            '• Use tags descritivas (gênero, tópicos, etc.)'
        )
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
        layout.addStretch()
    
    def _load_settings(self):
        """Carrega configurações salvas"""
        self.tfidf_checkbox.setChecked(self.prefs.get('use_tfidf', False))
        self.top_n_spinbox.setValue(self.prefs.get('default_top_n', 20))
        self.min_sim_spinbox.setValue(int(self.prefs.get('min_similarity', 0.1) * 100))
    
    def save_settings(self):
        """Salva configurações"""
        self.prefs['use_tfidf'] = self.tfidf_checkbox.isChecked()
        self.prefs['default_top_n'] = self.top_n_spinbox.value()
        self.prefs['min_similarity'] = self.min_sim_spinbox.value() / 100.0
    
    def _rebuild_index(self):
        """Força reconstrução do índice"""
        reply = QMessageBox.question(
            self, 
            'Reconstruir Índice',
            'Isso irá reconstruir o índice completo da biblioteca.\n'
            'Pode levar alguns minutos. Continuar?',
            StandardButton.Yes | StandardButton.No,
            StandardButton.No
        )
        
        if reply == StandardButton.Yes:
            # Deleta cache existente
            import os
            from calibre.utils.config import config_dir
            cache_dir = os.path.join(config_dir, 'plugins', 'recommender_cache')
            cache_file = os.path.join(cache_dir, 'metadata_index.pkl')
            
            if os.path.exists(cache_file):
                os.remove(cache_file)
            
            QMessageBox.information(
                self,
                'Índice Removido',
                'O índice será reconstruído na próxima vez que você usar o plugin.'
            )
