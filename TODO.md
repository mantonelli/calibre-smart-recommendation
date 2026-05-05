# TODO - Smart Book Recommender

## P0 — Bugs críticos / segurança

- [x] **[engine.py:193]** Cache em `pickle` → substituído por JSON (pickle executa código arbitrário no load)
- [x] **[ui.py:178]** `select_rows([book_id])` seleciona por row index, não book_id → corrigido com `using_ids=True`

## P1 — Bugs funcionais

- [x] **[ui.py:256-273]** `QProgressDialog` de indexação não renderiza conteúdo — `build_index()` bloqueia a main thread, impedindo o Qt de pintar o dialog. Corrigido com `IndexWorker(QThread)` + `QEventLoop`; engine emite progresso via callback.

- [x] **[engine.py:116-117]** Validação de cache só por contagem → agora compara mtime do cache com mtime de `metadata.db`
- [x] **[engine.py:359]** `pubdate.year` sem guard → adicionado `hasattr(..., 'year')` antes de acessar
- [x] **[ui.py:316]** `exec_()` deprecated no PyQt6 → `exec()`
- [x] **[engine.py:205]** `'programming'` duplicado no set `technical_keywords` → removido
- [x] **[ui.py:show_recommendations]** `recommend()` chamado com `top_n=20` hardcoded, ignorando a preferência `default_top_n` do usuário.
- [x] **[engine.py:_get_cache_dir]** Cache não isola por biblioteca — path fixo sobrescreve índice ao trocar de biblioteca. Corrigido com hash do `library_path` no nome do arquivo.

## P2 — Qualidade / UX

- [x] **[ui.py:94-106]** Colunas da tabela de recomendações truncadas e não redimensionáveis — `Stretch`/`ResizeToContents` substituídos por `Interactive` em todas + `setStretchLastSection(True)` na coluna Razão. Larguras iniciais: Título 220px, Autor 180px, Similaridade 100px.

- [x] **[ui.py:150-163]** `_populate_table` cria engine temporário por livro se `gui._recommender_engine` ausente → engine passado como parâmetro ao `RecommenderDialog`; hack `gui._recommender_engine` removido.
- [x] **[config.py:136-152]** Botão "Reconstruir Índice" só apaga cache, não reconstrói imediatamente → renomeado para "Limpar Cache do Índice"; mensagens e tooltip explicam que reindexação ocorre na próxima pesquisa.
- [x] **[ui.py:195]** `icon.png` não existe → `get_icons` substituída por `get_plugin_icon()` que usa `calibre.gui2.get_icons` (carrega do zip), depois `I('books_in_library.png')`, depois tema do sistema. `build.py` inclui `images/` automaticamente quando presente.
- [x] Botão funciona como split button: clique principal recomenda, seta abre menu com "Configurações..." e "Reindexar Biblioteca". Lógica de indexação extraída para `_build_index_with_progress()` reutilizável.
- [x] Filtro de livros não lidos: config.py ganhou seção "Filtro de Leitura" com checkbox + campo de coluna (desabilitado quando filtro inativo). engine.py filtra candidatos via `_is_read()` consultando a coluna customizada booleana (new_api e legacy).
- [x] Prever internacionalização dos textos usados no plugin → `load_translations()` em `__init__.py`; guard `try: _ except NameError` em `ui.py` e `config.py`; todas as strings UI envolvidas com `_()`; f-strings dinâmicas convertidas para `_('template {x}').format(x=x)`; `build.py` inclui `translations/*.mo`.
- [x] Quando existe um filtro aplicado na biblioteca e um livro recomedado é selecionado, esse livro não é apresentado se não fizer parte do filtro atual. → `_on_view_book` limpa busca via `gui.search.clear()` quando `current_id` difere do esperado após `select_rows`.
- [x] **[engine.py:detect_category]** Heurística `PDF → técnico` falsa positiva para romances em PDF. Removida; categoria determinada exclusivamente por tags e keywords.
- [x] **[ui.py:apply_settings]** `apply_settings` invalida índice mesmo quando só mudou o filtro de leitura (não requer reindexação). Corrigido: só invalida se mudou `use_tfidf` ou `min_similarity`.
- [x] **[engine.py:recommend]** `_is_read` consultado individualmente por candidato a cada busca → construído set de IDs lidos uma vez no início de `recommend()`.
- [x] **[engine.py:get_explanation]** Strings da coluna "Razão" (`"Mesmo autor:"`, `"Série:"`, `"Tags:"`, etc.) não passaram pelo wrap de i18n. Guard `_()` adicionado ao módulo; todas as strings de `get_explanation` e `_get_metadata` envolvidas.
- [x] **[engine.py:pre_filter]** Editora não era usada como fonte de candidatos no pré-filtro. `publisher_candidates` adicionado à união; livros com zero tags mas mesma editora agora chegam ao scoring.
- [x] Criar `README.md` com instruções de instalação, funcionalidades, configuração e contribuição para publicação no GitHub. Conteúdo em inglês; reescrito do zero para refletir estado atual do plugin.

## P3 — Manutenção

- [x] **[engine.py:37,267+]** `print()` espalhados pelo engine → substituídos por `logging` com níveis corretos (DEBUG/INFO/WARNING/ERROR) em engine.py e ui.py
