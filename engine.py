#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Motor de Recomendações - Core do algoritmo
Implementa similaridade por metadados com suporte opcional para TF-IDF
"""

import logging
import os
import json
from collections import defaultdict
from datetime import datetime

log = logging.getLogger(__name__)

try:
    _
except NameError:
    _ = lambda x: x


class RecommendationEngine:
    """
    Motor principal de recomendações
    Usa abordagem híbrida em camadas para performance em bibliotecas grandes
    """
    
    def __init__(self, db, prefs):
        """
        Args:
            db: Database do Calibre (calibre.library.db.LibraryDatabase)
            prefs: Preferências do plugin
        """
        self.db = db
        self.prefs = prefs
        self.cache_dir = self._get_cache_dir()
        self.metadata_index = None
        # Detecta API do Calibre
        self.use_new_api = hasattr(db, 'new_api')
        log.debug("Calibre API: %s", 'new_api' if self.use_new_api else 'legacy')
    
    def _get_all_book_ids(self):
        """Obtém todos os IDs de livros de forma compatível com diferentes versões do Calibre"""
        if self.use_new_api:
            return list(self.db.new_api.all_book_ids())
        else:
            # Tenta métodos alternativos
            if hasattr(self.db, 'all_book_ids'):
                return self.db.all_book_ids()
            elif hasattr(self.db, 'data'):
                return list(self.db.data.all_book_ids())
            else:
                raise AttributeError("Não foi possível encontrar método para listar livros")
    
    def _get_metadata(self, book_id):
        """Obtém metadados de um livro de forma compatível"""
        if self.use_new_api:
            proxy = self.db.new_api
            return {
                'title': proxy.field_for('title', book_id) or _('Sem título'),
                'authors': proxy.field_for('authors', book_id) or [],
                'tags': proxy.field_for('tags', book_id) or [],
                'series': proxy.field_for('series', book_id),
                'series_index': proxy.field_for('series_index', book_id),
                'publisher': proxy.field_for('publisher', book_id),
                'pubdate': proxy.field_for('pubdate', book_id),
                'languages': proxy.field_for('languages', book_id) or ['por'],
                'rating': proxy.field_for('rating', book_id),
                'comments': proxy.field_for('comments', book_id) or '',
                'formats': proxy.formats(book_id) or []
            }
        else:
            metadata = self.db.get_metadata(book_id)
            return {
                'title': metadata.title or _('Sem título'),
                'authors': list(metadata.authors) if metadata.authors else [],
                'tags': list(metadata.tags) if metadata.tags else [],
                'series': metadata.series,
                'series_index': metadata.series_index,
                'publisher': metadata.publisher,
                'pubdate': metadata.pubdate,
                'languages': list(metadata.languages) if metadata.languages else ['por'],
                'rating': metadata.rating,
                'comments': metadata.comments if metadata.comments else '',
                'formats': metadata.formats() if hasattr(metadata, 'formats') else []
            }
    
    def _get_cache_dir(self):
        from calibre.utils.config import config_dir
        cache_dir = os.path.join(config_dir, 'plugins', 'recommender_cache')
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        return cache_dir

    def _cache_file(self):
        """Caminho do cache específico para a biblioteca atual."""
        import hashlib
        library_path = getattr(self.db, 'library_path', '') or ''
        lib_hash = hashlib.md5(library_path.encode()).hexdigest()[:8]
        return os.path.join(self.cache_dir, f'metadata_index_{lib_hash}.json')

    def _serialize_index(self, index):
        """Converte índice para formato JSON-serializável"""
        def serialize_book(book):
            b = dict(book)
            if b['pubdate'] and hasattr(b['pubdate'], 'isoformat'):
                b['pubdate'] = b['pubdate'].isoformat()
            return b

        return {
            'books': {str(k): serialize_book(v) for k, v in index['books'].items()},
            'tags': {k: list(v) for k, v in index['tags'].items()},
            'authors': {k: list(v) for k, v in index['authors'].items()},
            'series': {k: list(v) for k, v in index['series'].items()},
            'publishers': {k: list(v) for k, v in index['publishers'].items()},
            'languages': {k: list(v) for k, v in index['languages'].items()},
            'last_updated': index['last_updated'],
        }

    def _deserialize_index(self, data):
        """Reconstrói índice a partir de JSON"""
        books = {}
        for k, v in data['books'].items():
            book = dict(v)
            if book['pubdate'] and isinstance(book['pubdate'], str):
                try:
                    book['pubdate'] = datetime.fromisoformat(book['pubdate'])
                except (ValueError, TypeError):
                    book['pubdate'] = None
            books[int(k)] = book

        return {
            'books': books,
            'tags': defaultdict(set, {k: set(v) for k, v in data['tags'].items()}),
            'authors': defaultdict(set, {k: set(v) for k, v in data['authors'].items()}),
            'series': defaultdict(set, {k: set(v) for k, v in data['series'].items()}),
            'publishers': defaultdict(set, {k: set(v) for k, v in data['publishers'].items()}),
            'languages': defaultdict(set, {k: set(v) for k, v in data['languages'].items()}),
            'last_updated': data.get('last_updated', ''),
        }
    
    def build_index(self, force_rebuild=False, progress_callback=None):
        """
        Constrói índice de metadados para busca rápida
        Deve ser chamado ao iniciar o plugin ou quando biblioteca muda

        Args:
            progress_callback: callable(current: int, total: int) chamado a cada N livros
        """
        cache_file = self._cache_file()

        # Verifica se cache existe e está atualizado
        if not force_rebuild and os.path.exists(cache_file):
            try:
                # Invalida cache se metadata.db foi modificado após o cache
                library_path = getattr(self.db, 'library_path', None)
                if library_path:
                    metadata_db = os.path.join(library_path, 'metadata.db')
                    if os.path.exists(metadata_db):
                        if os.path.getmtime(cache_file) < os.path.getmtime(metadata_db):
                            log.warning("Cache desatualizado: metadata.db modificado após cache")
                            raise ValueError("stale cache")

                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.metadata_index = self._deserialize_index(json.load(f))
                    log.info("Cache carregado: %d livros", len(self.metadata_index['books']))
                    return
            except Exception as e:
                log.warning("Erro ao carregar cache: %s", e)
        
        # Constrói índice do zero
        log.info("Construindo índice de metadados...")
        self.metadata_index = {
            'books': {},
            'tags': defaultdict(set),
            'authors': defaultdict(set),
            'series': defaultdict(set),
            'publishers': defaultdict(set),
            'languages': defaultdict(set),
            'last_updated': datetime.now().isoformat()
        }
        
        # Obtém todos os IDs de livros
        all_ids = self._get_all_book_ids()
        total = len(all_ids)
        log.info("Total de livros na biblioteca: %d", total)

        for idx, book_id in enumerate(all_ids):
            if idx % 1000 == 0:
                log.debug("Indexando: %d/%d", idx, total)
            if progress_callback and idx % 100 == 0:
                progress_callback(idx, total)

            try:
                metadata = self._get_metadata(book_id)
            except Exception as e:
                log.warning("Erro ao indexar livro %d: %s", book_id, e)
                continue
            
            # Extrai informações relevantes
            book_info = {
                'id': book_id,
                'title': metadata['title'],
                'authors': metadata['authors'],
                'tags': metadata['tags'],
                'series': metadata['series'],
                'series_index': metadata['series_index'],
                'publisher': metadata['publisher'],
                'pubdate': metadata['pubdate'],
                'languages': metadata['languages'],
                'rating': metadata['rating'],
                'comments': metadata['comments'],
                'formats': metadata['formats']
            }
            
            # Adiciona ao índice principal
            self.metadata_index['books'][book_id] = book_info
            
            # Indexa por tags
            for tag in book_info['tags']:
                self.metadata_index['tags'][tag.lower()].add(book_id)
            
            # Indexa por autor
            for author in book_info['authors']:
                self.metadata_index['authors'][author.lower()].add(book_id)
            
            # Indexa por série
            if book_info['series']:
                self.metadata_index['series'][book_info['series'].lower()].add(book_id)
            
            # Indexa por editora
            if book_info['publisher']:
                self.metadata_index['publishers'][book_info['publisher'].lower()].add(book_id)
            
            # Indexa por idioma
            for lang in book_info['languages']:
                self.metadata_index['languages'][lang.lower()].add(book_id)
        
        # Salva cache
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(self._serialize_index(self.metadata_index), f, ensure_ascii=False)

        if progress_callback:
            progress_callback(total, total)

        log.info("Índice construído: %d livros indexados", total)
    
    def detect_category(self, book_info):
        """
        Detecta se livro é técnico ou ficção baseado em tags e formato
        
        Returns:
            str: 'technical' ou 'fiction'
        """
        technical_keywords = {
            'programming', 'python', 'java', 'javascript', 'c++', 'database',
            'algorithm', 'computer science', 'data science', 'machine learning',
            'ai', 'reference', 'tutorial', 'guide', 'manual', 'textbook',
            'development', 'software', 'engineering', 'network',
            'security', 'web', 'api', 'cloud', 'devops', 'tecnologia', 'computação'
        }
        
        tags_lower = [t.lower() for t in book_info['tags']]
        if any(keyword in ' '.join(tags_lower) for keyword in technical_keywords):
            return 'technical'
        return 'fiction'
    
    def jaccard_similarity(self, set1, set2):
        """
        Calcula similaridade de Jaccard entre dois conjuntos
        
        Returns:
            float: Valor entre 0 e 1
        """
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def year_proximity(self, year1, year2):
        """
        Calcula proximidade entre anos de publicação
        
        Returns:
            float: Valor entre 0 e 1 (1 = mesmo ano, decresce com distância)
        """
        if not year1 or not year2:
            return 0.0
        
        diff = abs(year1 - year2)
        # Proximidade decresce com distância (max diferença considerada = 10 anos)
        return max(0, 1 - (diff / 10.0))
    
    def pre_filter(self, book_info):
        """
        Primeira camada: filtro rápido para reduzir espaço de busca
        22.000 livros → ~500-1500 candidatos
        
        Returns:
            set: IDs dos livros candidatos
        """
        candidates = set()
        
        # Filtro 1: Mesmo idioma (essencial)
        primary_lang = book_info['languages'][0] if book_info['languages'] else 'por'
        same_language = self.metadata_index['languages'].get(primary_lang.lower(), set())

        log.debug("Pré-filtro: idioma '%s' → %d livros", primary_lang, len(same_language))

        # Filtro 2: Pelo menos 1 tag em comum OU mesmo autor OU mesma série
        tags_candidates = set()
        for tag in book_info['tags']:
            tags_candidates.update(self.metadata_index['tags'].get(tag.lower(), set()))

        author_candidates = set()
        for author in book_info['authors']:
            author_candidates.update(self.metadata_index['authors'].get(author.lower(), set()))

        series_candidates = set()
        if book_info['series']:
            series_candidates = self.metadata_index['series'].get(book_info['series'].lower(), set())

        publisher_candidates = set()
        if book_info['publisher']:
            publisher_candidates = self.metadata_index['publishers'].get(
                book_info['publisher'].lower(), set()
            )

        candidates = (
            tags_candidates | author_candidates | series_candidates | publisher_candidates
        ) & same_language

        candidates.discard(book_info['id'])

        log.debug(
            "Pré-filtro: %d candidatos (tags=%d, autores=%d, série=%d, editora=%d, idioma=%d)",
            len(candidates), len(tags_candidates), len(author_candidates),
            len(series_candidates), len(publisher_candidates), len(same_language),
        )
        
        return candidates
    
    def calculate_similarity(self, book1_info, book2_info, category):
        """
        Segunda camada: calcula score de similaridade entre dois livros
        
        Args:
            book1_info: Informações do livro selecionado
            book2_info: Informações do livro candidato
            category: 'technical' ou 'fiction'
        
        Returns:
            float: Score de similaridade (0 a 1)
        """
        # Pesos diferentes para categorias diferentes
        if category == 'technical':
            weights = {
                'tags': 0.50,
                'author': 0.20,
                'publisher': 0.10,
                'year': 0.05,
                'series': 0.15
            }
        else:  # fiction
            weights = {
                'tags': 0.35,
                'author': 0.25,
                'series': 0.25,
                'year': 0.05,
                'publisher': 0.10
            }
        
        score = 0.0
        
        # Similaridade de tags (Jaccard)
        tags1 = set(t.lower() for t in book1_info['tags'])
        tags2 = set(t.lower() for t in book2_info['tags'])
        score += weights['tags'] * self.jaccard_similarity(tags1, tags2)
        
        # Mesmo autor
        authors1 = set(a.lower() for a in book1_info['authors'])
        authors2 = set(a.lower() for a in book2_info['authors'])
        if authors1 & authors2:
            score += weights['author']
        
        # Mesma série
        if book1_info['series'] and book2_info['series']:
            if book1_info['series'].lower() == book2_info['series'].lower():
                score += weights['series']
        
        # Mesma editora
        if book1_info['publisher'] and book2_info['publisher']:
            if book1_info['publisher'].lower() == book2_info['publisher'].lower():
                score += weights['publisher']
        
        # Proximidade de ano
        year1 = book1_info['pubdate'].year if book1_info['pubdate'] and hasattr(book1_info['pubdate'], 'year') else None
        year2 = book2_info['pubdate'].year if book2_info['pubdate'] and hasattr(book2_info['pubdate'], 'year') else None
        score += weights['year'] * self.year_proximity(year1, year2)
        
        return score

    def _is_read(self, book_id, column_label):
        """Verifica se livro está marcado como lido na coluna customizada."""
        label = column_label.lstrip('#')
        try:
            if self.use_new_api:
                return bool(self.db.new_api.field_for(f'#{label}', book_id))
            else:
                return bool(self.db.get_custom(book_id, label=label, index_is_id=True))
        except Exception:
            return False

    def _get_read_ids(self, column_label):
        """Retorna set de IDs marcados como lidos via uma única query."""
        label = column_label.lstrip('#')
        query = f'#{label}:true'
        try:
            if self.use_new_api:
                result = self.db.new_api.search(query)
            else:
                result = self.db.search_getting_ids(query, '')
            return set(result) if result else set()
        except Exception:
            # Fallback: verificação individual se a query falhar
            log.warning("_get_read_ids: query '%s' falhou, usando fallback por livro", query)
            return {bid for bid in self.metadata_index['books'] if self._is_read(bid, label)}

    def recommend(self, book_id, top_n=20):
        """
        Recomenda livros similares
        
        Args:
            book_id: ID do livro selecionado
            top_n: Número de recomendações a retornar
        
        Returns:
            list: Lista de tuplas (book_id, score, title) ordenadas por score
        """
        # Garante que índice está construído
        if not self.metadata_index:
            log.warning("Índice não existe, construindo...")
            self.build_index()

        # Obtém informações do livro selecionado
        book_info = self.metadata_index['books'].get(book_id)
        if not book_info:
            log.error("Livro %d não encontrado no índice", book_id)
            return []

        log.debug("recommend(): livro %d — '%s' tags=%s idiomas=%s",
                  book_id, book_info['title'], book_info['tags'], book_info['languages'])

        # Detecta categoria
        category = self.detect_category(book_info)
        log.debug("Categoria detectada: %s", category)

        # Pré-filtra candidatos
        candidates = self.pre_filter(book_info)

        # Filtro de livros não lidos (opcional) — uma query, não N chamadas
        filter_unread = self.prefs.get('filter_unread', False)
        read_column = self.prefs.get('read_column', '').strip()
        if filter_unread and read_column:
            before = len(candidates)
            read_ids = self._get_read_ids(read_column)
            candidates -= read_ids
            log.debug("Filtro não lidos: %d → %d candidatos (coluna=#%s, lidos=%d)",
                      before, len(candidates), read_column, len(read_ids))

        if not candidates:
            lang_counts = {}
            for binfo in self.metadata_index['books'].values():
                for lang in binfo['languages']:
                    lang_counts[lang] = lang_counts.get(lang, 0) + 1
            log.warning(
                "Nenhum candidato para livro %d. Idiomas=%s distribuição=%s tags=%s",
                book_id, book_info['languages'], lang_counts,
                [t for t in book_info['tags'] if t.lower() in self.metadata_index['tags']],
            )
            return []

        # Calcula scores
        scores = []
        for candidate_id in candidates:
            candidate_info = self.metadata_index['books'][candidate_id]
            similarity = self.calculate_similarity(book_info, candidate_info, category)
            if similarity > 0:
                scores.append((
                    candidate_id,
                    similarity,
                    candidate_info['title'],
                    candidate_info['authors'],
                    candidate_info['rating']
                ))

        scores.sort(key=lambda x: x[1], reverse=True)
        log.info("recommend(): %d resultados para '%s'", len(scores), book_info['title'])
        for i, (_, score, title, _, _) in enumerate(scores[:3]):
            log.debug("  top%d: %s (%.1f%%)", i + 1, title, score * 100)

        return scores[:top_n]
    
    def get_explanation(self, book_id, recommended_id):
        """
        Explica por que um livro foi recomendado
        
        Returns:
            str: Texto explicativo curto e claro
        """
        book1 = self.metadata_index['books'].get(book_id)
        book2 = self.metadata_index['books'].get(recommended_id)
        
        if not book1 or not book2:
            return _('Informações não disponíveis')

        reasons = []

        # 1. Mesmo autor
        authors1 = set(a.lower() for a in book1['authors'])
        authors2 = set(a.lower() for a in book2['authors'])
        common_authors = authors1 & authors2
        if common_authors:
            author_name = next(
                (a for a in book2['authors'] if a.lower() in common_authors), None
            )
            reasons.append(_('Mesmo autor: {author}').format(author=author_name))

        # 2. Mesma série
        if book1['series'] and book2['series']:
            if book1['series'].lower() == book2['series'].lower():
                reasons.append(_('Série: {series}').format(series=book2['series']))

        # 3. Tags em comum (máx. 3)
        tags1 = set(t.lower() for t in book1['tags'])
        tags2 = set(t.lower() for t in book2['tags'])
        common_tags = tags1 & tags2
        if common_tags:
            original_tags = [t for t in book2['tags'] if t.lower() in common_tags][:3]
            if original_tags:
                reasons.append(_('Tags: {tags}').format(tags=', '.join(original_tags)))

        # 4. Mesma editora (só se poucas razões)
        if len(reasons) < 2 and book1['publisher'] and book2['publisher']:
            if book1['publisher'].lower() == book2['publisher'].lower():
                reasons.append(_('Editora: {publisher}').format(publisher=book2['publisher']))

        if not reasons:
            return _('Semelhança de metadados')

        return ' • '.join(reasons)
