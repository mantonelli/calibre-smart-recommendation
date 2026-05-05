#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Widget de Configuração do Plugin
"""

try:
    # Calibre 8.x usa PyQt6
    from PyQt6.Qt import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
                          QSpinBox, QPushButton, QGroupBox, QFormLayout, QMessageBox,
                          QLineEdit)
    StandardButton = QMessageBox.StandardButton
except ImportError:
    # Fallback para PyQt5
    from PyQt5.Qt import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox,
                          QSpinBox, QPushButton, QGroupBox, QFormLayout, QMessageBox,
                          QLineEdit)
    StandardButton = QMessageBox

from calibre.utils.config import JSONConfig

try:
    _
except NameError:
    _ = lambda x: x


class ConfigWidget(QWidget):
    """Widget de configuração do plugin."""

    def __init__(self):
        QWidget.__init__(self)
        self.prefs = JSONConfig('plugins/recommender')
        self.prefs.defaults['min_similarity'] = 0.1
        self.prefs.defaults['default_top_n'] = 20
        self.prefs.defaults['filter_unread'] = False
        self.prefs.defaults['read_column'] = ''

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Grupo: Algoritmo
        algo_group = QGroupBox(_('Configurações do Algoritmo'))
        algo_layout = QFormLayout()
        algo_group.setLayout(algo_layout)

        self.top_n_spinbox = QSpinBox()
        self.top_n_spinbox.setMinimum(5)
        self.top_n_spinbox.setMaximum(50)
        self.top_n_spinbox.setSingleStep(5)
        self.top_n_spinbox.setToolTip(_('Número de recomendações a exibir'))
        algo_layout.addRow(_('Número de recomendações:'), self.top_n_spinbox)

        self.min_sim_spinbox = QSpinBox()
        self.min_sim_spinbox.setMinimum(0)
        self.min_sim_spinbox.setMaximum(100)
        self.min_sim_spinbox.setSingleStep(5)
        self.min_sim_spinbox.setSuffix('%')
        self.min_sim_spinbox.setToolTip(_('Similaridade mínima para exibir recomendação (0-100%)'))
        algo_layout.addRow(_('Similaridade mínima:'), self.min_sim_spinbox)

        layout.addWidget(algo_group)

        # Grupo: Filtro de Leitura
        filter_group = QGroupBox(_('Filtro de Leitura'))
        filter_layout = QFormLayout()
        filter_group.setLayout(filter_layout)

        self.filter_unread_checkbox = QCheckBox()
        self.filter_unread_checkbox.setToolTip(_(
            'Quando ativado, as recomendações incluirão apenas\n'
            'livros ainda não marcados como lidos.'
        ))
        self.filter_unread_checkbox.toggled.connect(self._on_filter_toggled)
        filter_layout.addRow(_('Sugerir apenas livros não lidos:'), self.filter_unread_checkbox)

        self.read_column_label = QLabel(_('Coluna de leitura:'))
        self.read_column_input = QLineEdit()
        self.read_column_input.setPlaceholderText(_('ex: read, lido, ja_li'))
        self.read_column_input.setToolTip(_(
            'Nome da coluna booleana personalizada que indica se o livro foi lido.\n'
            'Use apenas o rótulo da coluna, sem o prefixo "#".\n'
            'Exemplo: se a coluna se chama "#read", informe apenas "read".'
        ))
        filter_layout.addRow(self.read_column_label, self.read_column_input)

        layout.addWidget(filter_group)

        # Grupo: Cache
        cache_group = QGroupBox(_('Gerenciamento de Cache'))
        cache_layout = QVBoxLayout()
        cache_group.setLayout(cache_layout)

        cache_info = QLabel(_(
            'O plugin mantém um índice da sua biblioteca para buscas rápidas.\n'
            'O índice é invalidado automaticamente quando a biblioteca é modificada.\n'
            'Use o botão abaixo caso queira forçar uma reindexação completa na\n'
            'próxima vez que abrir as recomendações.'
        ))
        cache_info.setWordWrap(True)
        cache_layout.addWidget(cache_info)

        rebuild_button = QPushButton(_('Limpar Cache do Índice'))
        rebuild_button.setToolTip(_(
            'Remove o cache do índice. O índice será reconstruído automaticamente\n'
            'na próxima pesquisa de recomendações (pode levar alguns minutos).'
        ))
        rebuild_button.clicked.connect(self._clear_index_cache)
        cache_layout.addWidget(rebuild_button)

        layout.addWidget(cache_group)

        # Grupo: Informações
        info_group = QGroupBox(_('Informações'))
        info_layout = QVBoxLayout()
        info_group.setLayout(info_layout)

        info_text = QLabel(_(
            '<b>Como funciona:</b><br/>'
            'O plugin analisa tags, autores, séries, editoras e anos de publicação '
            'para encontrar livros similares em sua biblioteca.<br/><br/>'
            '<b>Dicas para melhores resultados:</b><br/>'
            '• Mantenha tags organizadas e consistentes<br/>'
            '• Preencha metadados (autor, série, editora)<br/>'
            '• Use tags descritivas (gênero, tópicos, etc.)'
        ))
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)

        layout.addWidget(info_group)

        layout.addStretch()

    def _on_filter_toggled(self, checked):
        self.read_column_label.setEnabled(checked)
        self.read_column_input.setEnabled(checked)

    def _load_settings(self):
        self.top_n_spinbox.setValue(self.prefs.get('default_top_n', 20))
        self.min_sim_spinbox.setValue(int(self.prefs.get('min_similarity', 0.1) * 100))
        filter_unread = self.prefs.get('filter_unread', False)
        self.filter_unread_checkbox.setChecked(filter_unread)
        self.read_column_input.setText(self.prefs.get('read_column', ''))
        self._on_filter_toggled(filter_unread)

    def save_settings(self):
        self.prefs['default_top_n'] = self.top_n_spinbox.value()
        self.prefs['min_similarity'] = self.min_sim_spinbox.value() / 100.0
        self.prefs['filter_unread'] = self.filter_unread_checkbox.isChecked()
        self.prefs['read_column'] = self.read_column_input.text().strip()

    def _clear_index_cache(self):
        reply = QMessageBox.question(
            self,
            _('Limpar Cache do Índice'),
            _('O cache do índice será removido.\n\n'
              'O índice será reconstruído automaticamente na próxima pesquisa de '
              'recomendações. Para bibliotecas grandes isso pode levar alguns minutos.\n\n'
              'Continuar?'),
            StandardButton.Yes | StandardButton.No,
            StandardButton.No
        )

        if reply == StandardButton.Yes:
            import os
            import glob
            from calibre.utils.config import config_dir
            cache_dir = os.path.join(config_dir, 'plugins', 'recommender_cache')

            # Remove caches de todas as bibliotecas (metadata_index_*.json)
            # e também o formato antigo sem hash para retrocompatibilidade
            patterns = [
                os.path.join(cache_dir, 'metadata_index_*.json'),
                os.path.join(cache_dir, 'metadata_index.json'),
            ]
            files = []
            for pattern in patterns:
                files.extend(glob.glob(pattern))

            removed = False
            for f in files:
                try:
                    os.remove(f)
                    removed = True
                except OSError:
                    pass

            msg = (
                _('Cache removido com sucesso.\n\n'
                  'O índice será reconstruído automaticamente na próxima pesquisa.')
                if removed else
                _('Nenhum cache encontrado. O índice já será gerado na próxima pesquisa.')
            )
            QMessageBox.information(self, _('Cache Limpo'), msg)
