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
        self.prefs.defaults['quality_min_score'] = 50

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Grupo: Algoritmo
        algo_group = QGroupBox(_('Algorithm Settings'))
        algo_layout = QFormLayout()
        algo_group.setLayout(algo_layout)

        self.top_n_spinbox = QSpinBox()
        self.top_n_spinbox.setMinimum(5)
        self.top_n_spinbox.setMaximum(50)
        self.top_n_spinbox.setSingleStep(5)
        self.top_n_spinbox.setToolTip(_('Number of recommendations to display'))
        algo_layout.addRow(_('Number of recommendations:'), self.top_n_spinbox)

        self.min_sim_spinbox = QSpinBox()
        self.min_sim_spinbox.setMinimum(0)
        self.min_sim_spinbox.setMaximum(100)
        self.min_sim_spinbox.setSingleStep(5)
        self.min_sim_spinbox.setSuffix('%')
        self.min_sim_spinbox.setToolTip(_('Minimum similarity to display a recommendation (0-100%)'))
        algo_layout.addRow(_('Minimum similarity:'), self.min_sim_spinbox)

        self.quality_score_spinbox = QSpinBox()
        self.quality_score_spinbox.setMinimum(0)
        self.quality_score_spinbox.setMaximum(100)
        self.quality_score_spinbox.setSingleStep(5)
        self.quality_score_spinbox.setSuffix('%')
        self.quality_score_spinbox.setToolTip(_(
            'Books with a quality score below this value appear in\n'
            'the incomplete metadata report (0–100%).'
        ))
        algo_layout.addRow(_('Quality alert below:'), self.quality_score_spinbox)

        layout.addWidget(algo_group)

        # Grupo: Filtro de Leitura
        filter_group = QGroupBox(_('Read Filter'))
        filter_layout = QFormLayout()
        filter_group.setLayout(filter_layout)

        self.filter_unread_checkbox = QCheckBox()
        self.filter_unread_checkbox.setToolTip(_(
            'When enabled, recommendations will only include\n'
            'books not yet marked as read.'
        ))
        self.filter_unread_checkbox.toggled.connect(self._on_filter_toggled)
        filter_layout.addRow(_('Suggest only unread books:'), self.filter_unread_checkbox)

        self.read_column_label = QLabel(_('Read column:'))
        self.read_column_input = QLineEdit()
        self.read_column_input.setPlaceholderText(_('e.g. read, finished, done'))
        self.read_column_input.setToolTip(_(
            'Name of the custom boolean column that indicates whether a book has been read.\n'
            'Use only the column label without the "#" prefix.\n'
            'Example: if the column is called "#read", enter "read".'
        ))
        filter_layout.addRow(self.read_column_label, self.read_column_input)

        layout.addWidget(filter_group)

        # Grupo: Cache
        cache_group = QGroupBox(_('Cache Management'))
        cache_layout = QVBoxLayout()
        cache_group.setLayout(cache_layout)

        cache_info = QLabel(_(
            'The plugin maintains an index of your library for fast searches.\n'
            'The index is invalidated automatically when the library is modified.\n'
            'Use the button below to force a full re-index the\n'
            'next time you open recommendations.'
        ))
        cache_info.setWordWrap(True)
        cache_layout.addWidget(cache_info)

        rebuild_button = QPushButton(_('Clear Index Cache'))
        rebuild_button.setToolTip(_(
            'Removes the index cache. The index will be rebuilt automatically\n'
            'on the next recommendation search (may take a few minutes).'
        ))
        rebuild_button.clicked.connect(self._clear_index_cache)
        cache_layout.addWidget(rebuild_button)

        layout.addWidget(cache_group)

        # Grupo: Informações
        info_group = QGroupBox(_('Information'))
        info_layout = QVBoxLayout()
        info_group.setLayout(info_layout)

        info_text = QLabel(_(
            '<b>How it works:</b><br/>'
            'The plugin analyses tags, authors, series, publishers, and publication years '
            'to find similar books in your library.<br/><br/>'
            '<b>Tips for better results:</b><br/>'
            '• Keep tags organised and consistent<br/>'
            '• Fill in metadata (author, series, publisher)<br/>'
            '• Use descriptive tags (genre, topics, etc.)'
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
        self.quality_score_spinbox.setValue(self.prefs.get('quality_min_score', 50))
        filter_unread = self.prefs.get('filter_unread', False)
        self.filter_unread_checkbox.setChecked(filter_unread)
        self.read_column_input.setText(self.prefs.get('read_column', ''))
        self._on_filter_toggled(filter_unread)

    def save_settings(self):
        self.prefs['default_top_n'] = self.top_n_spinbox.value()
        self.prefs['min_similarity'] = self.min_sim_spinbox.value() / 100.0
        self.prefs['quality_min_score'] = self.quality_score_spinbox.value()
        self.prefs['filter_unread'] = self.filter_unread_checkbox.isChecked()
        self.prefs['read_column'] = self.read_column_input.text().strip()

    def _clear_index_cache(self):
        reply = QMessageBox.question(
            self,
            _('Clear Index Cache'),
            _('The index cache will be removed.\n\n'
              'The index will be rebuilt automatically on the next recommendation search. '
              'For large libraries this may take a few minutes.\n\n'
              'Continue?'),
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
                _('Cache cleared successfully.\n\n'
                  'The index will be rebuilt automatically on the next search.')
                if removed else
                _('No cache found. The index will be generated on the next search.')
            )
            QMessageBox.information(self, _('Cache Cleared'), msg)
