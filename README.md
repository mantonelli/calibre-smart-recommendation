# Smart Book Recommender

A [Calibre](https://calibre-ebook.com/) plugin that recommends similar books from your own library based on metadata analysis — no internet connection required, no external services.

## Features

- **Metadata-driven recommendations** — compares tags, authors, series, publisher, and publication year using a weighted scoring model
- **Automatic category detection** — adjusts scoring weights for technical vs. fiction books based on tags
- **Book detail panel** — shows cover, authors, series, tags, rating, and formats for each recommendation without leaving the dialog
- **Unread filter** — optionally restrict recommendations to books not yet marked as read via a custom boolean column
- **Per-library index cache** — JSON cache keyed by library, invalidated automatically when `metadata.db` changes
- **Split toolbar button** — main click recommends; dropdown opens Settings and Re-index
- **PyQt5 / PyQt6 compatible** — works on Calibre 5.x through 8.x on Windows, macOS, and Linux

## Requirements

| Requirement | Notes |
|---|---|
| Calibre ≥ 5.0.0 | Python is bundled — no separate install needed |

## Installation

### From a release ZIP (recommended)

1. Download `recommender-x.y.z.zip` from the [Releases](../../releases) page.
2. In Calibre: **Preferences → Plugins → Load plugin from file**.
3. Select the downloaded ZIP and confirm.
4. Restart Calibre.

The **Recomendar Similares** button appears in the main toolbar after restart.

### Building from source

```bash
git clone <repo-url>
cd "Smart Recommendation"
python build.py                    # outputs dist/recommender-x.y.z.zip
python build.py --output /tmp      # custom output directory
```

`build.py` has no dependencies beyond the Python standard library. It also generates the toolbar icon automatically.

## Usage

1. Select a book in your library.
2. Click **Recomendar Similares** in the toolbar.
3. On the first run the plugin builds a metadata index — a few seconds for small libraries, a couple of minutes for very large ones. Subsequent runs load from cache instantly.
4. The recommendation dialog shows the top N similar books. Select a row to preview book details in the side panel. Double-click or press **Ver Livro** to navigate directly to that book in the library.

> If the library has an active search filter, the plugin clears it automatically so the selected book is always visible.

## Configuration

Open settings via the toolbar dropdown → **Configurações...** or via Calibre's **Preferences → Plugins → Smart Book Recommender → Customize plugin**.

| Setting | Default | Description |
|---|---|---|
| Number of recommendations | 20 | Results to show per search (5–50). |
| Minimum similarity | 10% | Results below this threshold are hidden (0–100%). |
| Suggest only unread books | Off | Hides books already marked as read in your library. |
| Read column | *(empty)* | Name of the custom boolean column that flags a book as read. Omit the `#` prefix — e.g. use `read`, not `#read`. |

Changing **Minimum similarity** invalidates the index automatically. Changing only the unread filter or number of results does not require re-indexing.

## How it works

### Step 1 — Pre-filter

To avoid scoring every book in a large library, the engine first collects candidates that share at least one of the following with the selected book (within the same language):

- a tag
- an author
- a series
- a publisher

This reduces tens of thousands of books to a few hundred candidates.

### Step 2 — Weighted scoring

Each candidate receives a score from 0 to 1 using a weighted sum. The weights differ by detected category:

| Signal | Technical | Fiction |
|---|---|---|
| Tag similarity (Jaccard) | 50% | 35% |
| Same author | 20% | 25% |
| Same series | 15% | 25% |
| Same publisher | 10% | 10% |
| Publication year proximity | 5% | 5% |

**Category detection** is tag-based: if any tag matches a set of technical keywords (programming languages, CS topics, data science, etc.) the book is classified as technical; otherwise it is fiction.

### Step 3 — Cache

The metadata index is serialised as JSON and stored at:

```
<calibre-config-dir>/plugins/recommender_cache/metadata_index_<lib-hash>.json
```

`<lib-hash>` is an 8-character MD5 of the library path, so each library has its own independent cache file. The cache is invalidated automatically when `metadata.db` is newer than the cache.

## Tips for better results

The quality of recommendations depends directly on the quality of your metadata.

**Tags** — use descriptive, consistent tags rather than personal notes:

```
# Avoid
Tags: read, to-read, favourite, mine, 2024

# Prefer
Tags: Python, Machine Learning, O'Reilly, Programming
Tags: Fantasy, Epic, Trilogy, Brandon Sanderson
```

**Other fields** — fill in author, series, publisher, and comments whenever possible. The author and series signals are especially important for fiction; tags and publisher matter most for technical books.

## Troubleshooting

### No recommendations found

- The selected book has no tags, no matched author, series, or publisher in your library.
- The book's language does not match other books.
- **Fix:** add descriptive tags to the book and make sure other books in your library share at least one metadata field.

### Recommendations look unrelated

- Metadata is sparse or inconsistent.
- Tags are personal notes rather than descriptive genre/topic labels.
- **Fix:** review and standardise tags across your library.

### First indexing is slow

Normal for large libraries — the index is built once and then cached. You can continue using Calibre while indexing runs in the background thread.

## Project structure

```
Smart Recommendation/
├── __init__.py          # Plugin entry point (InterfaceActionBase)
├── ui.py                # Qt UI — toolbar action, dialogs, book detail panel
├── engine.py            # Recommendation algorithm and index cache
├── config.py            # Settings widget
├── build.py             # Packaging script → dist/recommender-x.y.z.zip
├── images/
│   └── icon.png         # 32×32 toolbar icon (auto-generated by build.py)
├── translations/        # Optional compiled .mo files for i18n
└── plugin-import-name-recommender.txt
```

## Contributing

Contributions are welcome. Please open an issue before submitting a large pull request.

### Running the plugin from source during development

```bash
calibre-customize -a .   # installs from current directory
calibre-debug -g         # launches Calibre with debug output
```

### Adding a translation

The plugin has ~74 translatable strings spread across `ui.py`, `config.py`, and `engine.py`. Calibre loads translations from compiled `.mo` files in the `translations/` directory, matching the system locale automatically.

#### Prerequisites

Install the GNU gettext utilities:

```bash
# Debian / Ubuntu
sudo apt install gettext

# macOS (Homebrew)
brew install gettext

# Windows
# Download from https://mlocati.github.io/articles/gettext-iconv-windows.html
```

Alternatively, use [Poedit](https://poedit.net/) — a graphical editor that handles extraction, editing, and compilation in one tool.

#### Step 1 — Generate the POT template

Run this from the repository root to extract all translatable strings into a single template file:

```bash
xgettext --language=Python --keyword=_ \
  --output=translations/recommender.pot \
  ui.py config.py engine.py
```

The `.pot` file is the source of truth for all strings that need translation. Re-run this command whenever source files change to pick up new or modified strings.

#### Step 2 — Create a PO file for your locale

```bash
# Replace <locale> with your language code (see table below)
msginit --input=translations/recommender.pot \
        --locale=<locale> \
        --output=translations/<locale>.po
```

If a `.po` file for your locale already exists and you want to update it with new strings from the POT:

```bash
msgmerge --update translations/<locale>.po translations/recommender.pot
```

#### Step 3 — Translate the strings

Open the `.po` file in a text editor or Poedit and fill in the `msgstr` fields:

```po
msgid "Recomendações de Livros Similares"
msgstr "Similar Book Recommendations"

msgid "Similaridade"
msgstr "Similarity"
```

Leave `msgstr` empty for any string you want to fall back to the original Portuguese.

#### Step 4 — Compile and test

```bash
msgfmt translations/<locale>.po -o translations/<locale>.mo
```

Then reinstall the plugin from source so Calibre picks up the new `.mo` file:

```bash
calibre-customize -a .
calibre-debug -g
```

#### Step 5 — Package and share

```bash
python build.py
```

`build.py` includes all `.mo` files from `translations/` in the ZIP automatically. Share the `.po` and `.mo` files via a pull request or attach them to an issue.

#### Locale code reference

Use the locale code that matches Calibre's interface language setting:

| Language | Locale code |
|---|---|
| English | `en` |
| Spanish | `es` |
| French | `fr` |
| German | `de` |
| Italian | `it` |
| Japanese | `ja` |
| Chinese (Simplified) | `zh_CN` |
| Chinese (Traditional) | `zh_TW` |
| Russian | `ru` |
| Dutch | `nl` |
| Polish | `pl` |

For other languages, use the [IETF BCP 47](https://www.iana.org/assignments/language-subtag-registry/language-subtag-registry) language tag (e.g. `pt_PT`, `ko`, `ar`).

## License

GPL v3 — see <https://www.gnu.org/licenses/gpl-3.0.html>.
