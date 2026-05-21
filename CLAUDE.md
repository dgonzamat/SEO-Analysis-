# CLAUDE.md

Premisa de este repo: **estilo Karpathy**. Código pequeño, hackeable, legible. Cero magia, cero abstracciones especulativas. Si dudas entre dos formas, elige la que un lector humano entiende leyendo el archivo de arriba a abajo una sola vez.

## Filosofía operativa

1. **Yes-code, not no-code.** El código es el producto. No escondemos lógica detrás de configs YAML, plugins o decoradores. Si algo es importante, debe estar en un `.py` que cualquiera pueda abrir y modificar.
2. **Aplanar antes que jerarquizar.** Un solo nivel de paquete. Nada de `seo_analyzer/checks/onpage/title.py`. Si dos archivos comparten un import, viven en el mismo directorio.
3. **Archivos cortos.** Apunta a < 250 líneas por archivo. Si un archivo crece más, parte por **dominio**, no por capa (no inventes `services/`, `repositories/`, `handlers/`).
4. **Funciones, no clases.** Sólo introduce una clase cuando hay estado real que coordinar. Un dataclass para transportar datos sí, una clase con tres métodos para envolver una función no.
5. **Dependencias mínimas.** Cada nueva dependencia paga su renta. Hoy: `requests`, `beautifulsoup4`, `lxml`, `click`. Punto. Antes de agregar otra, intenta resolverlo con stdlib.
6. **Cero metaprogramación.** Nada de `__init_subclass__`, registries automáticos, decoradores que mutan firmas. Llamar a una función explícitamente desde `analyzer.py` siempre gana sobre auto-discovery.
7. **El happy path domina la lectura.** Maneja errores donde ocurren, no envuelvas todo en try/except. `requests.get` ya levanta excepciones útiles — propágalas o conviértelas una sola vez en `cli.py`.
8. **Comentarios sólo si el "por qué" no es obvio.** No documentes lo que el código ya dice. Si el código necesita un párrafo de explicación, probablemente el código está mal.
9. **Tests cortos y reales.** Sin mocks elaborados. Para checks: alimenta HTML literal y verifica los `Issue.code` que aparecen. Para scoring: arma `Issue` a mano y comprueba el output numérico. No hay infraestructura de tests, sólo `pytest`.
10. **README es documentación primaria.** No abras un `docs/` con 20 markdowns. Si algo merece documentarse, va al README o como comentario corto al inicio del archivo donde sucede.

## Estructura actual

```
seo_analyzer/
├── __init__.py         # exporta analyze, score_report
├── __main__.py         # python -m seo_analyzer
├── cli.py              # CLI Click; única capa que captura excepciones
├── fetcher.py          # wrapper de requests
├── issues.py           # dataclass Issue + pesos de severidad
├── onpage.py           # check_onpage(html, url) -> (issues, metrics)
├── technical.py        # check_technical(...) -> (issues, metrics)
├── performance.py      # check_performance(url) -> (issues, metrics)
├── scoring.py          # score_report(issues) -> dict
├── analyzer.py         # orquesta: fetch + 3 checks + scoring
└── report.py           # render consola y JSON
```

Reglas para esta estructura:

- Cada `check_*` recibe lo que necesita y devuelve **siempre** `(list[Issue], dict)`. Esa firma es el contrato; no la cambies.
- `analyzer.py` es el único que llama a los checks. Si agregas un nuevo check, edítalo ahí explícitamente — sin auto-registro.
- `cli.py` no contiene lógica de análisis. Sólo parsea args, llama `analyze()`, llama `write_output()`, traduce errores.
- `Issue` es inmutable conceptualmente. No agregues campos hasta que tres checks distintos los necesiten.

## Cómo agregar un check nuevo

1. Crea `seo_analyzer/<nombre>.py` con una función `check_<nombre>(...) -> tuple[list[Issue], dict]`.
2. Importa y llama esa función desde `analyzer.py`.
3. Si introduce una nueva categoría, agrégala al literal `Category` en `issues.py` y al diccionario `weights` en `scoring.py`.
4. Escribe 2-3 tests en `tests/test_checks.py` con HTML literal.

No hay paso 5. Si sientes que falta uno (clase base, registro, factory) — relee la premisa.

## Cómo agregar una recomendación o severidad

- Cada `Issue` lleva `recommendation` accionable, en español, una frase. Imperativo ("Agrega...", "Reduce...", "Habilita..."), no descriptivo.
- Severidad: `critical` corta el SEO (sin title, noindex, status 5xx); `high` daña fuerte (sin h1, sin description, sin viewport); `medium` fricción notable; `low` cosmético/marginal.

## Tests

```bash
pytest -q
```

Apuntar a:

- Tiempo total < 1 s.
- Cero llamadas de red (los smoke tests contra URLs reales son manuales, no parte del suite).
- Cada test cabe en pantalla.

## Anti-patrones que rechazamos en review

- Crear `services/`, `domain/`, `infrastructure/`, `interfaces/`, `adapters/`.
- Convertir funciones libres en métodos de una "Analyzer class" sin estado real.
- Inyección de dependencias vía constructores cuando un parámetro de función basta.
- Configs en YAML/JSON para algo que es un `dict` en Python de 10 líneas.
- Async sin razón (no servimos HTTP, no necesitamos concurrencia todavía).
- Logging frameworks (`logging.getLogger(__name__)` en cada módulo) — usa `print` o el output del CLI.
- Tipos genéricos demasiado abstractos (`TypeVar`, `Protocol`) en código de aplicación.
- Wrappers de `requests` por encima del wrapper que ya tenemos.

## Cuando dudes

Lee `nanoGPT` o `micrograd`. Si lo que vas a escribir se siente más enterprise que eso, está mal. Borra y vuelve a empezar más simple.
