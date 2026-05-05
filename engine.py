#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Motor de Recomendações - Core do algoritmo
Implementa similaridade por metadados com suporte opcional para TF-IDF
"""

import os
import pickle
from collections import defaultdict
from datetime import datetime
import json


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
        self.use_tfidf = False
        
        # Detecta API do Calibre
        self.use_new_api = hasattr(db, 'new_api')
        print(f"Calibre API: {'new_api' if self.use_new_api else 'legacy'}")
        
        # Tenta importar scikit-learn se disponível
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            self.TfidfVectorizer = TfidfVectorizer
            self.cosine_similarity = cosine_similarity
            self.use_tfidf = prefs.get('use_tfidf', False)
        except ImportError:
            self.use_tfidf = False
    
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
                'title': proxy.field_for('title', book_id) or 'Sem título',
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
                'title': metadata.title or 'Sem título',
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
        """Obtém diretório de cache do plugin"""
        from calibre.utils.config import config_dir
        cache_dir = os.path.join(config_dir, 'plugins', 'recommender_cache')
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        return cache_dir
    
    def build_index(self, force_rebuild=False):
        """
        Constrói índice de metadados para busca rápida
        Deve ser chamado ao iniciar o plugin ou quando biblioteca muda
        """
        cache_file = os.path.join(self.cache_dir, 'metadata_index.pkl')
        
        # Verifica se cache existe e está atualizado
        if not force_rebuild and os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    self.metadata_index = pickle.load(f)
                    # Valida se número de livros bate
                    current_count = len(self._get_all_book_ids())
                    cached_count = len(self.metadata_index['books'])
                    if cached_count == current_count:
                        print(f"Cache válido encontrado: {cached_count} livros")
                        return
                    else:
                        print(f"Cache desatualizado: {cached_count} != {current_count}")
            except Exception as e:
                print(f"Erro ao carregar cache: {e}")
        
        # Constrói índice do zero
        print("Construindo índice de metadados...")
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
        print(f"Total de livros na biblioteca: {total}")
        
        for idx, book_id in enumerate(all_ids):
            if idx % 1000 == 0:
                print(f"Indexando: {idx}/{total}")
            
            try:
                # Obtém metadados de forma compatível
                metadata = self._get_metadata(book_id)
            except Exception as e:
                print(f"Erro ao indexar livro {book_id}: {e}")
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
        with open(cache_file, 'wb') as f:
            pickle.dump(self.metadata_index, f)
        
        print(f"Índice construído: {total} livros indexados")
    
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
            'programming', 'development', 'software', 'engineering', 'network',
            'security', 'web', 'api', 'cloud', 'devops', 'tecnologia', 'computação'
        }
        
        # Verifica tags
        tags_lower = [t.lower() for t in book_info['tags']]
        if any(keyword in ' '.join(tags_lower) for keyword in technical_keywords):
            return 'technical'
        
        # Heurística: PDFs tendem a ser técnicos
        if 'PDF' in book_info['formats']:
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
        
        print(f"    Pré-filtro: Idioma '{primary_lang}' → {len(same_language)} livros")
        
        # Filtro 2: Pelo menos 1 tag em comum OU mesmo autor OU mesma série
        tags_candidates = set()
        for tag in book_info['tags']:
            tag_books = self.metadata_index['tags'].get(tag.lower(), set())
            tags_candidates.update(tag_books)
        
        print(f"    Pré-filtro: Tags → {len(tags_candidates)} livros")
        
        author_candidates = set()
        for author in book_info['authors']:
            author_books = self.metadata_index['authors'].get(author.lower(), set())
            author_candidates.update(author_books)
        
        print(f"    Pré-filtro: Autores → {len(author_candidates)} livros")
        
        series_candidates = set()
        if book_info['series']:
            series_books = self.metadata_index['series'].get(book_info['series'].lower(), set())
            series_candidates.update(series_books)
            print(f"    Pré-filtro: Série → {len(series_candidates)} livros")
        
        # União de tags, autores e séries
        candidates = tags_candidates | author_candidates | series_candidates
        print(f"    Pré-filtro: Total antes de idioma → {len(candidates)} livros")
        
        # Interseção: mesmo idioma E (tags OU autor OU série)
        candidates = candidates & same_language
        print(f"    Pré-filtro: Após filtro de idioma → {len(candidates)} livros")
        
        # Remove o próprio livro
        candidates.discard(book_info['id'])
        
        print(f"    Pré-filtro: Final (sem o próprio livro) → {len(candidates)} livros")
        
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
        year1 = book1_info['pubdate'].year if book1_info['pubdate'] else None
        year2 = book2_info['pubdate'].year if book2_info['pubdate'] else None
        score += weights['year'] * self.year_proximity(year1, year2)
        
        return score
    
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
            print("AVISO: Índice não existe, construindo...")
            self.build_index()
        
        # Obtém informações do livro selecionado
        book_info = self.metadata_index['books'].get(book_id)
        if not book_info:
            print(f"ERRO: Livro {book_id} não encontrado no índice!")
            print(f"IDs disponíveis: {list(self.metadata_index['books'].keys())[:10]}...")
            return []
        
        print(f"DEBUG recommend(): Processando livro {book_id}")
        print(f"  Título: {book_info['title']}")
        print(f"  Tags: {book_info['tags']}")
        print(f"  Idiomas: {book_info['languages']}")
        
        # Detecta categoria
        category = self.detect_category(book_info)
        print(f"  Categoria detectada: {category}")
        
        # Pré-filtra candidatos
        candidates = self.pre_filter(book_info)
        print(f"  Candidatos após pré-filtro: {len(candidates)}")
        
        if not candidates:
            print("  PROBLEMA: Nenhum candidato após pré-filtro!")
            print(f"  Idioma do livro: {book_info['languages']}")
            print(f"  Total de livros no índice: {len(self.metadata_index['books'])}")
            
            # Debug: mostra quantos livros por idioma
            lang_counts = {}
            for bid, binfo in self.metadata_index['books'].items():
                for lang in binfo['languages']:
                    lang_counts[lang] = lang_counts.get(lang, 0) + 1
            print(f"  Distribuição de idiomas: {lang_counts}")
            
            # Debug: mostra se há tags em comum
            tags_lower = set(t.lower() for t in book_info['tags'])
            print(f"  Tags do livro (lowercase): {tags_lower}")
            matching_tags = set()
            for tag in tags_lower:
                if tag in self.metadata_index['tags']:
                    matching_tags.add(tag)
                    print(f"    Tag '{tag}' encontrada em {len(self.metadata_index['tags'][tag])} livros")
            
            if not matching_tags:
                print("  PROBLEMA: Nenhuma tag do livro encontrada em outros livros!")
            
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
        
        print(f"  Scores calculados: {len(scores)}")
        
        # Ordena por score decrescente
        scores.sort(key=lambda x: x[1], reverse=True)
        
        # Debug: mostra top 3
        for i, (cid, score, title, _, _) in enumerate(scores[:3]):
            print(f"    {i+1}. {title} - {score*100:.1f}%")
        
        # Retorna top N
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
            return "Informações não disponíveis"
        
        reasons = []
        
        # 1. Verifica mesmo autor (prioridade alta)
        authors1 = set(a.lower() for a in book1['authors'])
        authors2 = set(a.lower() for a in book2['authors'])
        common_authors = authors1 & authors2
        if common_authors:
            # Pega nome original (com capitalização)
            author_name = None
            for a in book2['authors']:
                if a.lower() in common_authors:
                    author_name = a
                    break
            reasons.append(f"Mesmo autor: {author_name}")
        
        # 2. Verifica mesma série
        if book1['series'] and book2['series']:
            if book1['series'].lower() == book2['series'].lower():
                reasons.append(f"Série: {book2['series']}")
        
        # 3. Tags em comum (mostra no máximo 3)
        tags1 = set(t.lower() for t in book1['tags'])
        tags2 = set(t.lower() for t in book2['tags'])
        common_tags = tags1 & tags2
        if common_tags:
            # Pega nomes originais das tags
            original_tags = []
            for t in book2['tags']:
                if t.lower() in common_tags and len(original_tags) < 3:
                    original_tags.append(t)
            if original_tags:
                tags_text = ', '.join(original_tags)
                reasons.append(f"Tags: {tags_text}")
        
        # 4. Mesma editora (menos relevante, só menciona se tiver poucas razões)
        if len(reasons) < 2 and book1['publisher'] and book2['publisher']:
            if book1['publisher'].lower() == book2['publisher'].lower():
                reasons.append(f"Editora: {book2['publisher']}")
        
        # 5. Se não tiver razões específicas, usa genérico
        if not reasons:
            return "Semelhança de metadados"
        
        # Junta com " • " para ficar compacto
        return " • ".join(reasons)
