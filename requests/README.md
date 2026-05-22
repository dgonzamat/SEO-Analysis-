# Requests

Puente para analizar URLs desde un entorno con egress restringido (Claude Code on the web, sandboxes, etc.).

Crea un archivo `<nombre>.txt` con una URL adentro y haz commit. El workflow `.github/workflows/seo-analyze.yml` se dispara, corre el analizador en un runner de GitHub Actions (con internet libre) y commitea el JSON en `reports/<nombre>.json`.
