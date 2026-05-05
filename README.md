# Smart Book Recommender - Plugin para Calibre

Plugin de recomendações inteligentes para o Calibre que sugere livros similares da sua biblioteca baseado em metadados e opcionalmente análise textual.

## Características

✅ **Rápido e Escalável**: Otimizado para bibliotecas grandes (testado com 22.000+ livros)
✅ **Algoritmo Híbrido**: Combina análise de metadados com detecção automática de categoria
✅ **Zero Dependências**: Funciona sem bibliotecas externas (TF-IDF opcional)
✅ **Cache Inteligente**: Indexação automática para buscas instantâneas
✅ **Interface Intuitiva**: Integrado nativamente no Calibre

## Como Funciona

O plugin analisa:
- **Tags e categorias** (peso maior para livros técnicos)
- **Autores** (especialmente importante para ficção)
- **Séries** (detecta livros relacionados)
- **Editoras** (padrões de publicação)
- **Ano de publicação** (proximidade temporal)
- **Idioma** (filtra automaticamente)

### Detecção Automática

O plugin detecta se o livro é **técnico** ou **ficção** e ajusta os pesos automaticamente:

- **Livros Técnicos** (PDFs, programação, etc.): Prioriza tags e editora
- **Ficção** (EPUBs, romances, etc.): Prioriza autor e série

## Instalação

### Método 1: Via Interface do Calibre (Recomendado)

1. Baixe o arquivo `recommender.zip` deste repositório
2. Abra o Calibre
3. Vá em **Preferências → Plugins → Carregar plugin de arquivo**
4. Selecione o arquivo `recommender.zip`
5. Clique em **Sim** para aplicar e reiniciar o Calibre

### Método 2: Manual

1. Clone ou baixe este repositório
2. Compacte a pasta `calibre_recommender` em um arquivo ZIP
3. Renomeie para `recommender.zip`
4. Siga os passos 2-5 do Método 1

## Uso

### Básico

1. Selecione um livro na sua biblioteca
2. Clique no botão **"Recomendar Similares"** na barra de ferramentas
3. Uma janela mostrará até 20 livros similares com:
   - Título e autor
   - Porcentagem de similaridade
   - Avaliação (se disponível)
   - Razão da recomendação

4. Clique duas vezes em qualquer livro para visualizá-lo na biblioteca

### Primeira Execução

Na primeira vez que usar o plugin, ele construirá um índice da sua biblioteca. Para 22.000 livros, isso leva **2-5 minutos**. Esse índice é salvo e reutilizado nas próximas execuções.

### Configurações

Acesse **Preferências → Plugins → Interface Actions → Smart Book Recommender → Configurar**

Opções disponíveis:
- **Usar análise textual (TF-IDF)**: Melhora qualidade (requer scikit-learn)
- **Número de recomendações**: 5-50 livros
- **Similaridade mínima**: Filtro de qualidade (0-100%)
- **Reconstruir Índice**: Força atualização do cache

## Otimizações para Bibliotecas Grandes

### Performance Esperada (22.000 livros)

| Operação | Tempo |
|----------|-------|
| Indexação inicial | 2-5 minutos (uma vez) |
| Busca de recomendações | 50-200ms |
| Com TF-IDF ativado | 100-400ms |

### Dicas de Performance

1. **Mantenha metadados organizados**: Tags consistentes = melhores resultados
2. **Use cache**: Não force reconstrução sem necessidade
3. **TF-IDF opcional**: Só ative se tiver scikit-learn e quiser melhor qualidade

## Melhorando Resultados

### Tags Bem Organizadas

**❌ Evite:**
```
Tags: "lido", "ler depois", "favorito", "meu", "2024"
```

**✅ Prefira:**
```
Tags: "Python", "Machine Learning", "O'Reilly", "Programação"
Tags: "Fantasia", "Épico", "Trilogia", "Brandon Sanderson"
```

### Metadados Completos

Preencha sempre que possível:
- **Autor**: Essencial para ficção
- **Série**: Detecta livros relacionados automaticamente
- **Editora**: Importante para livros técnicos
- **Comentários**: Usado em TF-IDF (se ativado)

### Categorização Automática

O plugin detecta categoria baseado em:

**Técnico se:**
- Tags contêm: "programming", "python", "database", "algorithm", etc.
- Formato: PDF
- Tags em português: "programação", "tecnologia", "computação"

**Ficção caso contrário:**
- EPUBs sem tags técnicas
- Tags de gênero: "romance", "fantasia", "thriller"

## Dependências Opcionais

### TF-IDF (Análise Textual)

Para ativar análise textual avançada:

```bash
# No terminal/prompt de comando
pip install scikit-learn

# Ou no ambiente do Calibre (Windows)
calibre-debug -c "from calibre.utils.rapydscript import compile_pyj; compile_pyj()"
pip install --target="C:\Program Files\Calibre2\app\site-packages" scikit-learn
```

**Linux/Mac:**
```bash
calibre-customize --add-plugin recommender.zip
pip install --user scikit-learn
```

## Estrutura do Projeto

```
calibre_recommender/
├── __init__.py          # Plugin principal
├── engine.py            # Motor de recomendações (algoritmos)
├── ui.py               # Interface gráfica
├── config.py           # Widget de configuração
├── plugin-import-name-recommender.txt
└── README.md
```

## Algoritmo Detalhado

### Camada 1: Pré-Filtro (22k → ~500 livros)
```python
Filtros aplicados:
1. Mesmo idioma (essencial)
2. Pelo menos 1 tag EM COMUM
   OU mesmo autor
   OU mesma série
```

### Camada 2: Cálculo de Similaridade

**Para Livros Técnicos:**
```
Score = 0.50 × similaridade_tags +
        0.20 × mesmo_autor +
        0.15 × mesma_série +
        0.10 × mesma_editora +
        0.05 × proximidade_ano
```

**Para Ficção:**
```
Score = 0.35 × similaridade_tags +
        0.25 × mesmo_autor +
        0.25 × mesma_série +
        0.10 × mesma_editora +
        0.05 × proximidade_ano
```

### Camada 3: TF-IDF (Opcional)
Se ativado, refina top 100 candidatos analisando descrições/comentários.

## Troubleshooting

### "Nenhuma recomendação encontrada"

**Possíveis causas:**
- Livro sem tags ou metadados
- Livro muito único (sem similares na biblioteca)
- Idioma diferente dos demais

**Solução:**
1. Adicione tags ao livro selecionado
2. Preencha metadados (autor, série, editora)
3. Verifique se há outros livros do mesmo gênero/idioma

### Indexação muito lenta

**Para 22k livros:**
- Normal: 2-5 minutos
- Lento: >10 minutos

**Se muito lento:**
1. Verifique se HD/SSD está em uso alto
2. Feche outros programas pesados
3. Aguarde conclusão (só acontece uma vez)

### Recomendações de baixa qualidade

**Melhore seus metadados:**
1. Revise tags: Sejam descritivas, não genéricas
2. Complete informações de autor e série
3. Considere ativar TF-IDF (se tiver scikit-learn)

## Limitações Conhecidas

- Não analisa conteúdo dos arquivos (apenas metadados, exceto com TF-IDF)
- Depende de metadados bem preenchidos
- Primeira indexação pode demorar em bibliotecas muito grandes
- TF-IDF requer biblioteca externa (opcional)

## Roadmap Futuro

- [ ] Suporte a embeddings semânticos (Sentence-BERT)
- [ ] Análise de capas (similaridade visual)
- [ ] Histórico de leitura (livros lidos recentemente)
- [ ] Recomendações por cluster (descubra novos gêneros)
- [ ] Export de recomendações (CSV, JSON)

## Contribuindo

Sugestões e PRs são bem-vindos! Áreas de melhoria:
- Otimizações de performance
- Novos algoritmos de similaridade
- Melhorias na UI
- Testes com diferentes tipos de biblioteca

## Licença

GPL v3 - Compatível com Calibre

## Créditos

Desenvolvido para a comunidade Calibre
Algoritmo baseado em pesquisa de sistemas de recomendação
