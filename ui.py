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
                          QPixmap, QGridLayout, QWidget, QSizePolicy,
                          QColor, QBrush)
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
                          QPixmap, QGridLayout, QWidget, QSizePolicy,
                          QColor, QBrush)
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

try:
    _
except NameError:
    _ = lambda x: x


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

        self.cover_label = QLabel()
        self.cover_label.setAlignment(AlignHCenter | AlignTop)
        self.cover_label.setMinimumHeight(self.COVER_H)
        self.cover_label.setMaximumHeight(self.COVER_H)
        self.cover_label.setSizePolicy(QSizePolicy.Policy.Expanding if PYQT6
                                       else QSizePolicy.Expanding,
                                       QSizePolicy.Policy.Fixed if PYQT6
                                       else QSizePolicy.Fixed)
        layout.addWidget(self.cover_label)

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
        self.cover_label.setText(_('<i>Selecione<br/>um livro</i>'))
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
            self._add_row(row, _('Autores'), ', '.join(book_info['authors']))
            row += 1

        if book_info['series']:
            series = book_info['series']
            if book_info.get('series_index'):
                series += f' #{int(book_info["series_index"])}'
            self._add_row(row, _('Série'), series)
            row += 1

        if book_info['tags']:
            self._add_row(row, _('Tags'), ', '.join(book_info['tags']))
            row += 1

        if book_info['rating']:
            filled = int(book_info['rating'] / 2)
            stars = '★' * filled + '☆' * (5 - filled)
            self._add_row(row, _('Avaliação'), stars)
            row += 1

        if book_info['formats']:
            self._add_row(row, _('Formatos'), ', '.join(book_info['formats']))
            row += 1

        if book_info['publisher']:
            self._add_row(row, _('Editora'), book_info['publisher'])
            row += 1

        if book_info['pubdate'] and hasattr(book_info['pubdate'], 'year'):
            self._add_row(row, _('Ano'), str(book_info['pubdate'].year))

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
        self.cover_label.setText(_('<i>(sem capa)</i>'))
        self.cover_label.setAlignment(AlignCenter)


class RecommenderDialog(QDialog):
    """Dialog que exibe recomendações de livros."""

    def __init__(self, gui, book_id, recommendations, engine):
        QDialog.__init__(self, gui)
        self.gui = gui
        self.book_id = book_id
        self.recommendations = recommendations
        self.engine = engine

        self.setWindowTitle(_('Recomendações de Livros Similares'))
        self.setMinimumWidth(1050)
        self.setMinimumHeight(520)

        self._setup_ui()
        self._populate_table()

    def _setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        db = self.gui.current_db
        try:
            if hasattr(db, 'new_api'):
                title = db.new_api.field_for('title', self.book_id) or _('Sem título')
                authors = db.new_api.field_for('authors', self.book_id) or []
                authors_text = ', '.join(authors) if authors else _('Autor desconhecido')
            else:
                meta = db.get_metadata(self.book_id, index_is_id=True)
                title = meta.title
                authors_text = ', '.join(meta.authors) if meta.authors else _('Autor desconhecido')
        except Exception as e:
            log.warning("Erro ao obter metadados do livro %d: %s", self.book_id, e)
            title = f'Livro ID {self.book_id}'
            authors_text = _('Informação não disponível')

        layout.addWidget(QLabel(
            _('<h2>Recomendações baseadas em:</h2>'
              '<p><b>{title}</b><br/>por {authors}</p>').format(
                  title=title, authors=authors_text)
        ))

        splitter = QSplitter(Horizontal)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            _('Título'), _('Autor(es)'), _('Similaridade'), _('Razão')
        ])
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

        self.detail_panel = BookDetailPanel(self.gui, self.engine)
        splitter.addWidget(self.detail_panel)

        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)

        layout.addWidget(splitter, 1)

        button_layout = QHBoxLayout()
        self.view_button = QPushButton(_('Ver Livro'))
        self.view_button.clicked.connect(self._on_view_book)
        button_layout.addWidget(self.view_button)
        self.close_button = QPushButton(_('Fechar'))
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

    def _populate_table(self):
        self.table.setRowCount(len(self.recommendations))

        for row, (book_id, score, title, authors, rating) in enumerate(self.recommendations):
            title_item = QTableWidgetItem(title)
            title_item.setData(UserRole, book_id)
            self.table.setItem(row, 0, title_item)

            author_item = QTableWidgetItem(', '.join(authors) if authors else _('Desconhecido'))
            self.table.setItem(row, 1, author_item)

            similarity_item = QTableWidgetItem(f'{score * 100:.1f}%')
            similarity_item.setData(UserRole, score)
            self.table.setItem(row, 2, similarity_item)

            explanation = self.engine.get_explanation(self.book_id, book_id)
            self.table.setItem(row, 3, QTableWidgetItem(explanation))

        if self.recommendations:
            self.table.selectRow(0)

    def _on_row_changed(self, current, previous):
        if not current.isValid():
            return
        item = self.table.item(current.row(), 0)
        if item:
            self.detail_panel.show_book(item.data(UserRole))

    def _on_book_double_clicked(self):
        self._on_view_book()

    def _on_view_book(self):
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


class QualityReportDialog(QDialog):
    """Dialog que exibe livros com metadados incompletos."""

    def __init__(self, gui, report, min_score):
        QDialog.__init__(self, gui)
        self.gui = gui
        self.report = report
        self.min_score = min_score

        self.setWindowTitle(_('Qualidade dos Metadados'))
        self.setMinimumWidth(900)
        self.setMinimumHeight(500)
        self._setup_ui()
        self._populate_table()

    def _setup_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        count = len(self.report)
        self.summary_label = QLabel(
            _('<b>{count} livro(s)</b> com score abaixo de {threshold}% — '
              'ordenados do mais incompleto para o mais completo.').format(
                  count=count, threshold=self.min_score)
        )
        layout.addWidget(self.summary_label)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            _('Título'), _('Autor(es)'), _('Score'), _('Problemas')
        ])
        self.table.setSelectionBehavior(SelectRows)
        self.table.setSelectionMode(SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers if PYQT6
            else QAbstractItemView.NoEditTriggers
        )

        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        try:
            interactive = QHeaderView.ResizeMode.Interactive
        except AttributeError:
            interactive = QHeaderView.Interactive
        for col in range(3):
            header.setSectionResizeMode(col, interactive)
        self.table.setColumnWidth(0, 240)
        self.table.setColumnWidth(1, 160)
        self.table.setColumnWidth(2, 70)

        self.table.doubleClicked.connect(self._open_metadata_editor)
        layout.addWidget(self.table, 1)

        btn_layout = QHBoxLayout()
        self.edit_button = QPushButton(_('Editar Metadados'))
        self.edit_button.clicked.connect(self._open_metadata_editor)
        btn_layout.addWidget(self.edit_button)
        btn_layout.addStretch()
        close_btn = QPushButton(_('Fechar'))
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _populate_table(self):
        self.table.setRowCount(len(self.report))

        for row, entry in enumerate(self.report):
            score = entry['score']

            title_item = QTableWidgetItem(entry['title'])
            title_item.setData(UserRole, entry['id'])
            self.table.setItem(row, 0, title_item)

            authors_text = ', '.join(entry['authors']) if entry['authors'] else _('Desconhecido')
            self.table.setItem(row, 1, QTableWidgetItem(authors_text))

            score_item = QTableWidgetItem(f'{score}%')
            score_item.setData(UserRole, score)
            if score < 40:
                score_item.setForeground(QBrush(QColor('#c0392b')))
            elif score < 70:
                score_item.setForeground(QBrush(QColor('#e67e22')))
            self.table.setItem(row, 2, score_item)

            issues_text = ' • '.join(entry['issues']) if entry['issues'] else ''
            self.table.setItem(row, 3, QTableWidgetItem(issues_text))

        if self.report:
            self.table.selectRow(0)

    def _open_metadata_editor(self):
        row = self.table.currentRow()
        if row < 0:
            return
        book_id = self.table.item(row, 0).data(UserRole)

        # Seleciona o livro na biblioteca (necessário para a ação de edição)
        self.gui.library_view.select_rows([book_id], using_ids=True)
        if getattr(self.gui.library_view, 'current_id', None) != book_id:
            try:
                self.gui.search.clear()
            except Exception:
                pass
            self.gui.library_view.select_rows([book_id], using_ids=True)

        # Abre o editor de metadados sem fechar este diálogo
        try:
            self.gui.iactions['Edit Metadata'].edit_metadata(False)
        except Exception as e:
            log.warning("Erro ao abrir editor de metadados: %s", e)


class RecommenderAction(InterfaceAction):
    """Action principal do plugin - adiciona botão na interface."""

    name = 'Smart Book Recommender'
    action_spec = (
        _('Recomendar Similares'), None,
        _('Encontra livros similares ao selecionado'), None,
    )
    action_type = 'current'
    popup_type = PopupMode  # split button: clique → recomendar, seta → menu

    def genesis(self):
        self.qaction.setIcon(self._load_plugin_icon())
        self.qaction.triggered.connect(self.show_recommendations)
        self.engine = None

        menu = QMenu()
        menu.addAction(_('Recomendar Similares'), self.show_recommendations)
        menu.addSeparator()
        menu.addAction(_('Qualidade dos Metadados...'), self._show_quality_report)
        menu.addSeparator()
        menu.addAction(_('Configurações...'), self._show_config)
        menu.addAction(_('Reindexar Biblioteca'), self._force_reindex)
        self.qaction.setMenu(menu)

    # ------------------------------------------------------------------

    def _load_plugin_icon(self):
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
        prefs.defaults['min_similarity'] = 0.1
        prefs.defaults['quality_min_score'] = 50
        return prefs

    def _ensure_engine(self, db):
        if not self.engine:
            self.engine = RecommendationEngine(db, self.load_preferences())

    def _build_index_with_progress(self):
        """Constrói o índice com barra de progresso. Retorna True em sucesso."""
        progress = QProgressDialog(_('Preparando indexação...'), None, 0, 0, self.gui)
        progress.setWindowTitle(_('Indexando Biblioteca'))
        progress.setWindowModality(WindowModal)
        progress.show()

        worker = IndexWorker(self.engine)
        error_holder = [None]
        loop = QEventLoop()

        def on_progress(current, total):
            progress.setMaximum(total)
            progress.setValue(current)
            progress.setLabelText(
                _('Indexando: {current} / {total} livros...').format(
                    current=current, total=total)
            )

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
            error_dialog(self.gui, _('Erro na indexação'),
                         _('Erro ao construir índice:\n{error}').format(error=error_holder[0]),
                         show=True)
            return False

        log.info("Índice construído com %d livros", len(self.engine.metadata_index['books']))
        return True

    # ------------------------------------------------------------------

    def _show_config(self):
        from calibre_plugins.recommender.config import ConfigWidget

        d = QDialog(self.gui)
        d.setWindowTitle(_('Smart Book Recommender — Configurações'))
        layout = QVBoxLayout()
        d.setLayout(layout)

        config_widget = ConfigWidget()
        layout.addWidget(config_widget)

        # Captura settings que exigem reindexação ANTES de salvar
        algo_before = config_widget.prefs.get('min_similarity', 0.1)

        buttons = QDialogButtonBox(OkCancel)
        buttons.accepted.connect(lambda: (config_widget.save_settings(), d.accept()))
        buttons.rejected.connect(d.reject)
        layout.addWidget(buttons)

        d.exec() if PYQT6 else d.exec_()

        # Invalida índice apenas se configurações de algoritmo mudaram
        algo_after = config_widget.prefs.get('min_similarity', 0.1)
        if algo_after != algo_before:
            self.apply_settings()

    def _show_quality_report(self):
        db = self.gui.current_db
        self._ensure_engine(db)

        if not self.engine.metadata_index:
            if not self._build_index_with_progress():
                return

        prefs = self.load_preferences()
        min_score = int(prefs.get('quality_min_score', 70))

        progress = QProgressDialog(_('Analisando metadados...'), None, 0, 0, self.gui)
        progress.setWindowTitle(_('Qualidade dos Metadados'))
        progress.setWindowModality(WindowModal)
        progress.show()
        try:
            report = self.engine.get_quality_report(min_score=min_score)
        finally:
            progress.close()

        if not report:
            info_dialog(
                self.gui,
                _('Metadados em boa forma'),
                _('Nenhum livro encontrado com score abaixo de {threshold}%.').format(
                    threshold=min_score),
                show=True,
            )
            return

        d = QualityReportDialog(self.gui, report, min_score)
        d.exec() if PYQT6 else d.exec_()

    def _force_reindex(self):
        db = self.gui.current_db
        self._ensure_engine(db)
        self.engine.metadata_index = None
        self._build_index_with_progress()

    # ------------------------------------------------------------------

    def show_recommendations(self):
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows:
            error_dialog(self.gui, _('Nenhum livro selecionado'),
                         _('Por favor, selecione um livro para obter recomendações.'),
                         show=True)
            return

        try:
            db = self.gui.current_db

            if hasattr(self.gui.library_view, 'current_id'):
                book_id = self.gui.library_view.current_id
            else:
                book_id = self.gui.library_view.model().id(rows[0])

            if book_id is None or book_id < 1:
                error_dialog(self.gui, _('Erro'),
                             _('Não foi possível obter ID do livro selecionado.'),
                             show=True)
                return

            log.debug("Book ID obtido: %d", book_id)

            try:
                if hasattr(db, 'new_api'):
                    title = db.new_api.field_for('title', book_id)
                else:
                    title = db.get_metadata(book_id).title
                log.debug("Livro selecionado: %s", title)
            except Exception as e:
                error_dialog(self.gui, _('Erro'),
                             _('Livro ID {book_id} inválido ou não encontrado.\n{error}').format(
                                 book_id=book_id, error=e),
                             show=True)
                return

            self._ensure_engine(db)

            if not self.engine.metadata_index:
                if not self._build_index_with_progress():
                    return

            progress = QProgressDialog(_('Calculando recomendações...'), None, 0, 0, self.gui)
            progress.setWindowTitle(_('Recomendando'))
            progress.setWindowModality(WindowModal)
            progress.show()

            try:
                top_n = self.engine.prefs.get('default_top_n', 20)
                recommendations = self.engine.recommend(book_id, top_n=top_n)
                log.debug("%d recomendações encontradas", len(recommendations))
            except Exception as e:
                import traceback
                error_msg = _('Erro ao calcular recomendações:\n{error}\n\nDetalhes:\n{details}').format(
                    error=e, details=traceback.format_exc()
                )
                log.error(error_msg)
                error_dialog(self.gui, _('Erro ao recomendar'), error_msg, show=True)
                return
            finally:
                progress.close()

            if not recommendations:
                book_info = self.engine.metadata_index['books'].get(book_id)
                details = ''
                if book_info:
                    details = _(
                        '\n\nInformações do livro:'
                        '\n- Tags: {tags}'
                        '\n- Autores: {authors}'
                        '\n- Idioma: {languages}'
                        '\n- Série: {series}'
                        '\n- Editora: {publisher}'
                    ).format(
                        tags=', '.join(book_info['tags']) or _('Nenhuma'),
                        authors=', '.join(book_info['authors']) or _('Nenhum'),
                        languages=', '.join(book_info['languages']) or _('Nenhum'),
                        series=book_info['series'] or _('Nenhuma'),
                        publisher=book_info['publisher'] or _('Nenhuma'),
                    )
                info_dialog(self.gui, _('Sem recomendações'),
                            _('Não foram encontrados livros similares.') + details + '\n\n'
                            + _('Dicas:\n'
                                '- Adicione tags descritivas ao livro\n'
                                '- Preencha metadados (autor, série, editora)\n'
                                '- Verifique se há outros livros do mesmo idioma'),
                            show=True)
                return

            RecommenderDialog(self.gui, book_id, recommendations, self.engine).exec()

        except Exception as e:
            import traceback
            error_msg = _('Erro inesperado:\n{error}\n\nStack trace:\n{details}').format(
                error=e, details=traceback.format_exc()
            )
            log.error(error_msg)
            error_dialog(self.gui, _('Erro'), error_msg, show=True)

    def apply_settings(self):
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
