# Cloverwing Studio website

Live at https://www.cloverwingstudio.net

- `src/books.json` is the catalogue: every book, its blurb, covers and store links.
- `src/build.py` turns the catalogue into the pages in `docs/`.
- `docs/` is the published site (GitHub Pages serves this folder).

To change the site: edit `src/books.json` (or the styles in `src/site.css`), run `python3 src/build.py`, commit and push.
