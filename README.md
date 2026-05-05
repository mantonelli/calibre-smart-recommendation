# Smart Book Recommender

A [Calibre](https://calibre-ebook.com/) plugin that recommends similar books from your own library based on metadata analysis — no internet connection required, no external services.

## Features

- **Metadata-driven recommendations** — compares tags, authors, series, publisher, and publication year using a weighted scoring model
- **Automatic category detection** — adjusts scoring weights for technical vs. fiction books based on tags
- **Book detail panel** — shows cover, authors, series, tags, rating, and formats for each recommendation without leaving the dialog
- **Unread filter** — optionally restrict recommendations to books not yet marked as read via a custom boolean column
- **Optional TF-IDF analysis** — text-based scoring from book descriptions/comments when `scikit-learn` is available
- **Per-library index cache** — JSON cache keyed by library, invalidated automatically when `metadata.db` changes
- **Split toolbar button** — main click recommends; dropdown opens Settings and Re-index
- **PyQt5 / PyQt6 compatible** — works on Calibre 5.x through 8.x on Windows, macOS, and Linux

## Requirements

| Requirement | Notes |
|---|---|
| Calibre ≥ 5.0.0 | Python is bundled — no separate install needed |
| scikit-learn | **Optional.** Enables TF-IDF mode for text-based scoring |

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
| Use TF-IDF analysis | Off | Text-based scoring using book descriptions. Requires `scikit-learn`. Slower on first run. |
| Number of recommendations | 20 | Results to show per search (5–50). |
| Minimum similarity | 10% | Results below this threshold are hidden (0–100%). |
| Suggest only unread books | Off | Hides books already marked as read in your library. |
| Read column | *(empty)* | Name of the custom boolean column that flags a book as read. Omit the `#` prefix — e.g. use `read`, not `#read`. |

Changing **Use TF-IDF** or **Minimum similarity** invalidates the index automatically. Changing only the unread filter or number of results does not require re-indexing.

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
- **Fix:** review and standardise tags across your library. Consider enabling TF-IDF if `scikit-learn` is available.

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

1. Extract strings with `xgettext` (or `pygettext`) targeting `ui.py`, `config.py`, and `engine.py`.
2. Create `translations/<locale>.po` and fill in translations.
3. Compile: `msgfmt translations/<locale>.po -o translations/<locale>.mo`.
4. Run `python build.py` — compiled `.mo` files in `translations/` are included in the ZIP automatically.

## License

GPL v3 — see <https://www.gnu.org/licenses/gpl-3.0.html>.
