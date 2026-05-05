#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Interface do Usuário - Dialog de Recomendações
"""

import logging

try:
    # Calibre 8.x usa PyQt6
    from PyQt6.Qt import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                          QTableWidgetItem, QLabel, QProgressDialog, QHeaderView,
                          QAbstractItemView, Qt, QIcon, QMenu, QToolButton,
                          QDialogButtonBox, QSplitter, QScrollArea, QFrame,
                          QPixmap, QGridLayout, QWidget, QSizePolicy)
    from PyQt6.QtCore import QThread, pyqtSignal, QEventLoop
    PYQT6 = True
    SelectRows = QAbstractItemView.SelectionBehavior.SelectRows
    SingleSelection = QAbstractItemView.SelectionMode.SingleSelection
    UserRole = Qt.ItemDataRole.UserRole
    WindowModal = Qt.WindowModality.WindowModal
    PopupMode = QToolButton.ToolButtonPopupMode.MenuButtonPopup
    OkCancel = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    AlignRight  = Qt.AlignmentFlag.AlignRight
    AlignTop    = Qt.AlignmentFlag.AlignTop
    AlignCenter = Qt.AlignmentFlag.AlignCenter
    AlignHCenter = Qt.AlignmentFlag.AlignHCenter
    KeepAspectRatio   = Qt.AspectRatioMode.KeepAspectRatio
    SmoothTransform   = Qt.TransformationMode.SmoothTransformation
    Horizontal        = Qt.Orientation.Horizontal
except (ImportError, AttributeError):
    # Fallback para PyQt5 (versões antigas do Calibre)
    from PyQt5.Qt import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                          QTableWidgetItem, QLabel, QProgressDialog, QHeaderView,
                          QAbstractItemView, Qt, QIcon, QMenu, QToolButton,
                          QDialogButtonBox, QSplitter, QScrollArea, QFrame,
                          QPixmap, QGridLayout, QWidget, QSizePolicy)
    from PyQt5.QtCore import QThread, pyqtSignal, QEventLoop
    PYQT6 = False
    SelectRows = QAbstractItemView.SelectRows
    SingleSelection = QAbstractItemView.SingleSelection
    UserRole = Qt.UserRole
    WindowModal = Qt.WindowModal
    PopupMode = QToolButton.MenuButtonPopup
    OkCancel = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
    AlignRight  = Qt.AlignRight
    AlignTop    = Qt.AlignTop
    AlignCenter = Qt.AlignCenter
    AlignHCenter = Qt.AlignHCenter
    KeepAspectRatio = Qt.KeepAspectRatio
    SmoothTransform = Qt.SmoothTransformation
    Horizontal      = Qt.Horizontal

from calibre.gui2 import error_dialog, info_dialog
from calibre.gui2.actions import InterfaceAction

from calibre_plugins.recommender.engine import RecommendationEngine

log = logging.getLogger(__name__)


class IndexWorker(QThread):
    """Executa build_index em background para não bloquear a UI."""

    progress = pyqtSignal(int, int)  # (current, total)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, engine):
        QThread.__init__(self)
        self.engine = engine

    def run(self):
        try:
            self.engine.build_index(progress_callback=self.progress.emit)
            self.finished.emit()
        except Exception as e:
            import traceback
            self.error.emit(f"{e}\n\n{traceback.format_exc()}")


class BookDetailPanel(QWidget):
    """Painel lateral com capa e metadados do livro selecionado na tabela."""

    COVER_W = 180
    COVER_H = 260

    def __init__(self, gui, engine):
        QWidget.__init__(self)
        self.gui = gui
        self.engine = engine
        self._cover_cache = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)
        self.setLayout(layout)
        self.setMinimumWidth(220)

        # Capa
        self.cover_label = QLabel()
        self.cover_label.setAlignment(AlignHCenter | AlignTop)
        self.cover_label.setMinimumHeight(self.COVER_H)
        self.cover_label.setMaximumHeight(self.COVER_H)
        self.cover_label.setSizePolicy(QSizePolicy.Policy.Expanding if PYQT6
                                       else QSizePolicy.Expanding,
                                       QSizePolicy.Policy.Fixed if PYQT6
                                       else QSizePolicy.Fixed)
        layout.addWidget(self.cover_label)

        # Scroll com campos de metadados
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame if PYQT6 else QFrame.NoFrame)
        self._fields_widget = QWidget()
        self._fields_layout = QGridLayout()
        self._fields_layout.setColumnStretch(1, 1)
        self._fields_layout.setHorizontalSpacing(8)
        self._fields_layout.setVerticalSpacing(4)
        self._fields_widget.setLayout(self._fields_layout)
        scroll.setWidget(self._fields_widget)
        layout.addWidget(scroll, 1)

        self._clear()

    def _clear(self):
        self.cover_label.setText('<i>Selecione<br/>um livro</i>')
        self.cover_label.setAlignment(AlignCenter)
        while self._fields_layout.count():
            item = self._fields_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _add_row(self, row, label_text, value_text):
        lbl = QLabel(f'<span style="color:#888;">{label_text}</span>')
        lbl.setAlignment(AlignRight | AlignTop)
        val = QLabel(value_text)
        val.setWordWrap(True)
        val.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse if PYQT6
            else Qt.TextSelectableByMouse
        )
        self._fields_layout.addWidget(lbl, row, 0)
        self._fields_layout.addWidget(val, row, 1)

    def show_book(self, book_id):
        self._clear()
        book_info = self.engine.metadata_index['books'].get(book_id) if self.engine.metadata_index else None
        if not book_info:
            return

        self._load_cover(book_id)

        row = 0
        if book_info['authors']:
            self._add_row(row, 'Autores', ', '.join(book_info['authors']))
            row += 1

        if book_info['series']:
            series = book_info['series']
            if book_info.get('series_index'):
                series += f' #{int(book_info["series_index"])}'
            self._add_row(row, 'Série', series)
            row += 1

        if book_info['tags']:
            self._add_row(row, 'Tags', ', '.join(book_info['tags']))
            row += 1

        if book_info['rating']:
            filled = int(book_info['rating'] / 2)
            stars = '★' * filled + '☆' * (5 - filled)
            self._add_row(row, 'Avaliação', stars)
            row += 1

        if book_info['formats']:
            self._add_row(row, 'Formatos', ', '.join(book_info['formats']))
            row += 1

        if book_info['publisher']:
            self._add_row(row, 'Editora', book_info['publisher'])
            row += 1

        if book_info['pubdate'] and hasattr(book_info['pubdate'], 'year'):
            self._add_row(row, 'Ano', str(book_info['pubdate'].year))

    def _load_cover(self, book_id):
        if book_id in self._cover_cache:
            self.cover_label.setPixmap(self._cover_cache[book_id])
            return

        db = self.gui.current_db
        try:
            cover_data = (db.new_api.cover(book_id) if hasattr(db, 'new_api')
                          else db.cover(book_id, index_is_id=True))
            if cover_data:
                pixmap = QPixmap()
                pixmap.loadFromData(cover_data)
                scaled = pixmap.scaled(self.COVER_W, self.COVER_H,
                                       KeepAspectRatio, SmoothTransform)
                self._cover_cache[book_id] = scaled
                self.cover_label.setAlignment(AlignHCenter | AlignTop)
                self.cover_label.setPixmap(scaled)
                return
        except Exception:
            pass
        self.cover_label.setText('<i>(sem capa)</i>')
        self.cover_label.setAlignment(AlignCenter)


class RecommenderDialog(QDialog):
    """
    Dialog que exibe recomendações de livros
    """
    
    def __init__(self, gui, book_id, recommendations, engine):
        QDialog.__init__(self, gui)
        self.gui = gui
        self.book_id = book_id
        self.recommendations = recommendations
        self.engine = engine

        self.setWindowTitle('Recomendações de Livros Similares')
        self.setMinimumWidth(1050)
        self.setMinimumHeight(520)

        self._setup_ui()
        self._populate_table()

    def _setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Cabeçalho
        db = self.gui.current_db
        try:
            if hasattr(db, 'new_api'):
                title = db.new_api.field_for('title', self.book_id) or 'Sem título'
                authors = db.new_api.field_for('authors', self.book_id) or []
                authors_text = ', '.join(authors) if authors else 'Autor desconhecido'
            else:
                meta = db.get_metadata(self.book_id, index_is_id=True)
                title = meta.title
                authors_text = ', '.join(meta.authors) if meta.authors else 'Autor desconhecido'
        except Exception as e:
            log.warning("Erro ao obter metadados do livro %d: %s", self.book_id, e)
            title, authors_text = f'Livro ID {self.book_id}', 'Informação não disponível'

        layout.addWidget(QLabel(
            f'<h2>Recomendações baseadas em:</h2>'
            f'<p><b>{title}</b><br/>por {authors_text}</p>'
        ))

        # Splitter: tabela | painel de detalhes
        splitter = QSplitter(Horizontal)

        # — Tabela —
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Título', 'Autor(es)', 'Similaridade', 'Razão'])
        self.table.setSelectionBehavior(SelectRows)
        self.table.setSelectionMode(SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)

        header = self.table.horizontalHeader()
        header.setMinimumSectionSize(80)
        header.setStretchLastSection(True)
        try:
            interactive = QHeaderView.ResizeMode.Interactive
        except AttributeError:
            interactive = QHeaderView.Interactive
        for col in range(3):
            header.setSectionResizeMode(col, interactive)
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 160)
        self.table.setColumnWidth(2, 95)

        self.table.doubleClicked.connect(self._on_book_double_clicked)
        self.table.selectionModel().currentRowChanged.connect(self._on_row_changed)
        splitter.addWidget(self.table)

        # — Painel de detalhes —
        self.detail_panel = BookDetailPanel(self.gui, self.engine)
        splitter.addWidget(self.detail_panel)

        # Proporção inicial: ~70% tabela, ~30% painel
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)

        layout.addWidget(splitter, 1)

        # Botões
        button_layout = QHBoxLayout()
        self.view_button = QPushButton('Ver Livro')
        self.view_button.clicked.connect(self._on_view_book)
        button_layout.addWidget(self.view_button)
        self.close_button = QPushButton('Fechar')
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def _populate_table(self):
        """Preenche tabela com recomendações"""
        self.table.setRowCount(len(self.recommendations))

        for row, (book_id, score, title, authors, rating) in enumerate(self.recommendations):
            title_item = QTableWidgetItem(title)
            title_item.setData(UserRole, book_id)
            self.table.setItem(row, 0, title_item)

            author_item = QTableWidgetItem(', '.join(authors) if authors else 'Desconhecido')
            self.table.setItem(row, 1, author_item)

            similarity_item = QTableWidgetItem(f'{score * 100:.1f}%')
            similarity_item.setData(UserRole, score)
            self.table.setItem(row, 2, similarity_item)

            explanation = self.engine.get_explanation(self.book_id, book_id)
            self.table.setItem(row, 3, QTableWidgetItem(explanation))

        if self.recommendations:
            self.table.selectRow(0)
    
    def _on_row_changed(self, current, previous):
        """Atualiza painel de detalhes ao mudar seleção na tabela."""
        if not current.isValid():
            return
        item = self.table.item(current.row(), 0)
        if item:
            self.detail_panel.show_book(item.data(UserRole))

    def _on_book_double_clicked(self):
        """Evento de double-click em livro"""
        self._on_view_book()
    
    def _on_view_book(self):
        """Visualiza livro selecionado no Calibre"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return

        book_id = self.table.item(current_row, 0).data(UserRole)
        self.accept()

        self.gui.library_view.select_rows([book_id], using_ids=True)

        # Se livro não aparece no filtro atual, limpa busca e tenta novamente
        if getattr(self.gui.library_view, 'current_id', None) != book_id:
            try:
                self.gui.search.clear()
            except Exception:
                pass
            self.gui.library_view.select_rows([book_id], using_ids=True)

        self.gui.library_view.scrollTo(self.gui.library_view.currentIndex())


class RecommenderAction(InterfaceAction):
    """
    Action principal do plugin - adiciona botão na interface
    """

    name = 'Smart Book Recommender'
    action_spec = ('Recomendar Similares', None, 'Encontra livros similares ao selecionado', None)
    action_type = 'current'
    popup_type = PopupMode  # split button: clique → recomendar, seta → menu

    def genesis(self):
        """Inicializa a action"""
        self.qaction.setIcon(self._load_plugin_icon())
        self.qaction.triggered.connect(self.show_recommendations)
        self.engine = None

        menu = QMenu()
        menu.addAction('Recomendar Similares', self.show_recommendations)
        menu.addSeparator()
        menu.addAction('Configurações...', self._show_config)
        menu.addAction('Reindexar Biblioteca', self._force_reindex)
        self.qaction.setMenu(menu)

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    def _load_plugin_icon(self):
        """Carrega ícone do zip do plugin, com fallbacks."""
        try:
            data = self.interface_action_base_plugin.load_resources(['images/icon.png'])
            icon_bytes = data.get('images/icon.png')
            if icon_bytes:
                pm = QPixmap()
                pm.loadFromData(icon_bytes)
                icon = QIcon(pm)
                if not icon.isNull():
                    return icon
        except Exception:
            pass
        try:
            from calibre.gui2 import I
            for name in ('books_in_library.png', 'book.png', 'search.png'):
                icon = QIcon(I(name))
                if not icon.isNull():
                    return icon
        except Exception:
            pass
        return QIcon()

    def load_preferences(self):
        from calibre.utils.config import JSONConfig
        prefs = JSONConfig('plugins/recommender')
        prefs.defaults['use_tfidf'] = False
        prefs.defaults['min_similarity'] = 0.1
        return prefs

    def _ensure_engine(self, db):
        """Inicializa o engine na primeira chamada."""
        if not self.engine:
            self.engine = RecommendationEngine(db, self.load_preferences())

    def _build_index_with_progress(self):
        """Constrói (ou reconstrói) o índice mostrando barra de progresso.

        Returns True em caso de sucesso, False se houve erro.
        """
        progress = QProgressDialog('Preparando indexação...', None, 0, 0, self.gui)
        progress.setWindowTitle('Indexando Biblioteca')
        progress.setWindowModality(WindowModal)
        progress.show()

        worker = IndexWorker(self.engine)
        error_holder = [None]
        loop = QEventLoop()

        def on_progress(current, total):
            progress.setMaximum(total)
            progress.setValue(current)
            progress.setLabelText(f'Indexando: {current} / {total} livros...')

        def on_error(msg):
            error_holder[0] = msg
            loop.quit()

        worker.progress.connect(on_progress)
        worker.finished.connect(loop.quit)
        worker.error.connect(on_error)
        worker.start()
        loop.exec() if PYQT6 else loop.exec_()
        progress.close()

        if error_holder[0]:
            error_dialog(self.gui, 'Erro na indexação',
                         f"Erro ao construir índice:\n{error_holder[0]}", show=True)
            return False

        log.info("Índice construído com %d livros", len(self.engine.metadata_index['books']))
        return True

    # ------------------------------------------------------------------
    # Ações do menu de contexto
    # ------------------------------------------------------------------

    def _show_config(self):
        """Abre dialog de configurações do plugin."""
        from calibre_plugins.recommender.config import ConfigWidget

        d = QDialog(self.gui)
        d.setWindowTitle('Smart Book Recommender — Configurações')
        layout = QVBoxLayout()
        d.setLayout(layout)

        config_widget = ConfigWidget()
        layout.addWidget(config_widget)

        buttons = QDialogButtonBox(OkCancel)
        buttons.accepted.connect(lambda: (config_widget.save_settings(), d.accept()))
        buttons.rejected.connect(d.reject)
        layout.addWidget(buttons)

        d.exec() if PYQT6 else d.exec_()
        self.apply_settings()

    def _force_reindex(self):
        """Reconstrói o índice imediatamente."""
        db = self.gui.current_db
        self._ensure_engine(db)
        self.engine.metadata_index = None
        self._build_index_with_progress()

    # ------------------------------------------------------------------
    # Ação principal
    # ------------------------------------------------------------------

    def show_recommendations(self):
        """Mostra dialog de recomendações para o livro selecionado."""
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows:
            error_dialog(self.gui, 'Nenhum livro selecionado',
                         'Por favor, selecione um livro para obter recomendações.',
                         show=True)
            return

        try:
            db = self.gui.current_db

            if hasattr(self.gui.library_view, 'current_id'):
                book_id = self.gui.library_view.current_id
            else:
                book_id = self.gui.library_view.model().id(rows[0])

            if book_id is None or book_id < 1:
                error_dialog(self.gui, 'Erro',
                             'Não foi possível obter ID do livro selecionado.', show=True)
                return

            log.debug("Book ID obtido: %d", book_id)

            try:
                if hasattr(db, 'new_api'):
                    title = db.new_api.field_for('title', book_id)
                else:
                    title = db.get_metadata(book_id).title
                log.debug("Livro selecionado: %s", title)
            except Exception as e:
                error_dialog(self.gui, 'Erro',
                             f'Livro ID {book_id} inválido ou não encontrado.\n{e}',
                             show=True)
                return

            self._ensure_engine(db)

            if not self.engine.metadata_index:
                if not self._build_index_with_progress():
                    return

            progress = QProgressDialog('Calculando recomendações...', None, 0, 0, self.gui)
            progress.setWindowTitle('Recomendando')
            progress.setWindowModality(WindowModal)
            progress.show()

            try:
                recommendations = self.engine.recommend(book_id, top_n=20)
                log.debug("%d recomendações encontradas", len(recommendations))
            except Exception as e:
                import traceback
                error_msg = (f"Erro ao calcular recomendações:\n{e}\n\n"
                             f"Detalhes:\n{traceback.format_exc()}")
                log.error(error_msg)
                error_dialog(self.gui, 'Erro ao recomendar', error_msg, show=True)
                return
            finally:
                progress.close()

            if not recommendations:
                book_info = self.engine.metadata_index['books'].get(book_id)
                details = ''
                if book_info:
                    details = (
                        f"\n\nInformações do livro:"
                        f"\n- Tags: {', '.join(book_info['tags']) or 'Nenhuma'}"
                        f"\n- Autores: {', '.join(book_info['authors']) or 'Nenhum'}"
                        f"\n- Idioma: {', '.join(book_info['languages']) or 'Nenhum'}"
                        f"\n- Série: {book_info['series'] or 'Nenhuma'}"
                        f"\n- Editora: {book_info['publisher'] or 'Nenhuma'}"
                    )
                info_dialog(self.gui, 'Sem recomendações',
                            f'Não foram encontrados livros similares.{details}\n\n'
                            'Dicas:\n'
                            '- Adicione tags descritivas ao livro\n'
                            '- Preencha metadados (autor, série, editora)\n'
                            '- Verifique se há outros livros do mesmo idioma',
                            show=True)
                return

            RecommenderDialog(self.gui, book_id, recommendations, self.engine).exec()

        except Exception as e:
            import traceback
            error_msg = f"Erro inesperado:\n{e}\n\nStack trace:\n{traceback.format_exc()}"
            log.error(error_msg)
            error_dialog(self.gui, 'Erro', error_msg, show=True)

    def apply_settings(self):
        """Invalida índice ao salvar configurações."""
        if self.engine:
            self.engine.metadata_index = None


def get_plugin_icon():
    """Carrega ícone do plugin com fallbacks."""
    try:
        from calibre.gui2 import I
        for name in ('books_in_library.png', 'book.png', 'search.png'):
            icon = QIcon(I(name))
            if not icon.isNull():
                return icon
    except Exception:
        pass
    for theme_name in ('system-search', 'book', 'find'):
        icon = QIcon.fromTheme(theme_name)
        if not icon.isNull():
            return icon
    return QIcon()
