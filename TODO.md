# TODO - Smart Book Recommender

## P0 — Bugs críticos / segurança

- [ ] **[engine.py:193]** Cache em `pickle` → substituir por JSON (pickle executa código arbitrário no load)
- [ ] **[ui.py:178]** `select_rows([book_id])` seleciona por row index, não book_id → livro errado selecionado na biblioteca

## P1 — Bugs funcionais

- [ ] **[engine.py:116-117]** Validação de cache só por contagem → cache stale se mesmo nº de livros mas metadados mudaram (usar hash ou timestamp)
- [ ] **[engine.py:359]** `pubdate.year` sem guard → crash se `pubdate` mal tipado ou None inesperado
- [ ] **[ui.py:316]** `exec_()` deprecated no PyQt6 → usar `exec()`
- [ ] **[engine.py:205]** `'programming'` duplicado no set `technical_keywords`

## P2 — Qualidade / UX

- [ ] **[ui.py:150-163]** `_populate_table` cria engine temporário por livro se `gui._recommender_engine` ausente → garantir que engine sempre propagado
- [ ] **[config.py:136-152]** Botão "Reconstruir Índice" só apaga cache, não reconstrói imediatamente → UX enganosa; reconstrói na hora ou avisa claramente
- [ ] **[ui.py:195]** `icon.png` não existe no projeto → `get_icons` sempre usa fallback; adicionar ícone ou simplificar
- [ ] Botão deve funcionar com menu de contexto, dano possibilidade de acessar a janela de configurações e reindexar a biblioteca
- [ ] Tela de configuração deve prever a possibilidade do usuário optar pelas sugestões serem feitas apenas entre livros não lidos. Se o usuário optar por desconsiderar os lidos, na tela de configurações deverá informar o nome da coluna (booleana) que armazena essa informação.

## P3 — Manutenção

- [ ] **[engine.py:37,267+]** `print()` espalhados pelo engine → substituir por `logging` (evita spam no console Calibre em prod)
