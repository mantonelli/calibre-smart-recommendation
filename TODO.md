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

## P2 — Qualidade / UX

- [x] **[ui.py:94-106]** Colunas da tabela de recomendações truncadas e não redimensionáveis — `Stretch`/`ResizeToContents` substituídos por `Interactive` em todas + `setStretchLastSection(True)` na coluna Razão. Larguras iniciais: Título 220px, Autor 180px, Similaridade 100px.

- [x] **[ui.py:150-163]** `_populate_table` cria engine temporário por livro se `gui._recommender_engine` ausente → engine passado como parâmetro ao `RecommenderDialog`; hack `gui._recommender_engine` removido.
- [x] **[config.py:136-152]** Botão "Reconstruir Índice" só apaga cache, não reconstrói imediatamente → renomeado para "Limpar Cache do Índice"; mensagens e tooltip explicam que reindexação ocorre na próxima pesquisa.
- [x] **[ui.py:195]** `icon.png` não existe → `get_icons` substituída por `get_plugin_icon()` que usa `calibre.gui2.get_icons` (carrega do zip), depois `I('books_in_library.png')`, depois tema do sistema. `build.py` inclui `images/` automaticamente quando presente.
- [x] Botão funciona como split button: clique principal recomenda, seta abre menu com "Configurações..." e "Reindexar Biblioteca". Lógica de indexação extraída para `_build_index_with_progress()` reutilizável.
- [x] Filtro de livros não lidos: config.py ganhou seção "Filtro de Leitura" com checkbox + campo de coluna (desabilitado quando filtro inativo). engine.py filtra candidatos via `_is_read()` consultando a coluna customizada booleana (new_api e legacy).

## P3 — Manutenção

- [x] **[engine.py:37,267+]** `print()` espalhados pelo engine → substituídos por `logging` com níveis corretos (DEBUG/INFO/WARNING/ERROR) em engine.py e ui.py
