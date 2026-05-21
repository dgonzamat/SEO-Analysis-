# SEO Analyzer

CLI de análisis SEO escrito en Python. Audita una URL y devuelve:

- **Score global 0-100** y nota A-F.
- **Score por categoría** (on-page, técnico, performance).
- **Lista priorizada de problemas** con severidad (crítico, alto, medio, bajo) y recomendación accionable para cada uno.
- Salida en consola (con colores) o JSON para integraciones.

## Instalación

```bash
git clone https://github.com/dgonzamat/seo-analysis-.git
cd seo-analysis-
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

## Uso

```bash
# Análisis básico
seo-analyze https://ejemplo.com

# JSON para integrar con otros sistemas
seo-analyze https://ejemplo.com --format json -o reporte.json

# Activar Core Web Vitals vía PageSpeed Insights
export PSI_API_KEY=tu_api_key
seo-analyze https://ejemplo.com --strategy mobile

# Modo CI: falla si el score queda bajo 80
seo-analyze https://ejemplo.com --fail-under 80
```

Si no tienes el comando instalado, también puedes ejecutar:

```bash
python -m seo_analyzer https://ejemplo.com
```

## Qué analiza

### On-page (peso 45%)

- `<title>` (presencia, longitud 30-60 chars).
- `<meta name="description">` (presencia, longitud 70-160 chars).
- Jerarquía de headings (`<h1>` único, uso de `<h2>`-`<h6>`).
- Atributo `lang` en `<html>`.
- Imágenes sin atributo `alt`.
- Enlaces internos.
- Open Graph y Twitter Card.
- Cantidad de contenido (thin content < 300 palabras).

### Técnico (peso 35%)

- HTTPS y código de estado HTTP.
- `<link rel="canonical">`.
- `<meta name="viewport">` (responsive).
- Declaración de charset.
- `<meta name="robots">` (detecta `noindex`).
- Datos estructurados JSON-LD (schema.org).
- `robots.txt` accesible y con referencia a sitemap.
- `sitemap.xml` accesible en la raíz.
- Compresión gzip/brotli en la respuesta.
- TTFB (Time To First Byte).

### Performance (peso 20%, opcional)

Si se provee `PSI_API_KEY`, se consulta Google PageSpeed Insights y se evalúan:

- **LCP** (Largest Contentful Paint).
- **CLS** (Cumulative Layout Shift).
- **INP** (Interaction to Next Paint).
- **TBT** (Total Blocking Time).
- Score de Lighthouse.

Sin API key, esta sección se omite y el score se calcula sobre las dos primeras categorías.

## Cómo se calcula el score

Cada categoría empieza en 100 y descuenta puntos según severidad de los problemas encontrados:

| Severidad | Descuento |
|-----------|-----------|
| crítico   | -15       |
| alto      | -8        |
| medio     | -4        |
| bajo      | -1        |

El score global es el promedio ponderado por los pesos indicados arriba.

## Desarrollo

```bash
pip install -e ".[dev]"
pytest
```

## Estructura

```
seo_analyzer/
├── analyzer.py        # orquestador principal
├── cli.py             # interfaz de línea de comandos
├── fetcher.py         # HTTP client
├── issues.py          # modelo Issue + pesos de severidad
├── scoring.py         # cálculo del score y priorización
├── report.py          # renderizado consola/JSON
├── onpage.py          # check_onpage
├── technical.py       # check_technical
└── performance.py     # check_performance (PageSpeed Insights)
```

Estructura plana intencional. Ver [`CLAUDE.md`](./CLAUDE.md) para la filosofía del proyecto.

## Extender

Para agregar un nuevo chequeo: crea `seo_analyzer/<nombre>.py` con una función que devuelva `(list[Issue], dict)`, importala desde `analyzer.py` y llamala explícitamente. Sin auto-discovery.

## Roadmap

- Crawling multi-página (no solo una URL).
- Modo comparativo (antes/después).
- Reporte HTML interactivo.
- Detección de keywords y densidad.
- Integración con sitemaps grandes.
