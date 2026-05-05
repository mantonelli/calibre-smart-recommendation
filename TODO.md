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

- [ ] **[ui.py:150-163]** `_populate_table` cria engine temporário por livro se `gui._recommender_engine` ausente → garantir que engine sempre propagado
- [ ] **[config.py:136-152]** Botão "Reconstruir Índice" só apaga cache, não reconstrói imediatamente → UX enganosa; reconstrói na hora ou avisa claramente
- [ ] **[ui.py:195]** `icon.png` não existe no projeto → `get_icons` sempre usa fallback; adicionar ícone ou simplificar
- [ ] Botão deve funcionar com menu de contexto, dano possibilidade de acessar a janela de configurações e reindexar a biblioteca
- [ ] Tela de configuração deve prever a possibilidade do usuário optar pelas sugestões serem feitas apenas entre livros não lidos. Se o usuário optar por desconsiderar os lidos, na tela de configurações deverá informar o nome da coluna (booleana) que armazena essa informação.

## P3 — Manutenção

- [ ] **[engine.py:37,267+]** `print()` espalhados pelo engine → substituir por `logging` (evita spam no console Calibre em prod)
