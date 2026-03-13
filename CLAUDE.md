# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
This project contains a set of web mapping plugins for Xpublish - a framework for serving xarray datasets via HTTP APIs.

The goal of this project is to transform xarray datasets to raster, vector and other types of tiles, which can then be served via HTTP APIs. To do this, the package implements a set of xpublish plugins:
* `xpublish_tiles.xpublish.tiles.TilesPlugin`: An [OGC Tiles](https://www.ogc.org/standards/ogcapi-tiles/) conformant plugin for serving raster, vector and other types of tiles.
* `xpublish_tiles.xpublish.wms.WMSPlugin`: An [OGC Web Map Service](https://www.ogc.org/standards/wms/) conformant plugin for serving raster, vector and other types of tiles.

### Background Information

The WMS and Tiles specifications are available in in the `docs` directory for reference.

## Development Workflow

### Key Commands
- **Environment sync**: `uv sync --dev`
- **Type check**: `uv run ty check src/ tests/` (only checks src/ and tests/ directories)
- **Run unit tests**: `uv run pytest tests` (defaults to --where=local)
- **Run a single test**: `uv run pytest tests/path/to/test_file.py::test_name`
- **Run tests with coverage**: `uv run pytest tests --cov=src/xpublish_tiles --cov-report=term-missing`
- **Run pre-commit checks**: `pre-commit run --all-files`

### Dependency Groups
- **dev**: All development dependencies (includes testing, linting, type checking, debugging)
- **testing**: Testing-only dependencies (pytest, syrupy, hypothesis, matplotlib, etc.)

## Architecture

### Plugin System
Both plugins extend `xpublish.Plugin` and use `@hookimpl` decorated methods:
- `app_router()`: Global endpoints (e.g., `/tiles/conformance`, `/tiles/tileMatrixSets`)
- `dataset_router()`: Dataset-specific endpoints (e.g., `/tiles/{tileMatrixSetId}/{z}/{y}/{x}`)

Entry points are declared in `pyproject.toml` under `[project.entry-points."xpublish.plugin"]`.

### Grid System (`grids.py`)
Extensible hierarchy for different spatial data layouts:
- `GridSystem` (ABC) → `GridSystem2D` → `Rectilinear` / `Curvilinear` / `Affine`
- `Triangular`: Unstructured grids
- `guess_grid_system()` auto-detects the appropriate type from dataset variables
- Grids are LRU-cached (up to 16) keyed by `_xpublish_id` and variable name

### Rendering Pipeline (`pipeline.py`)
HTTP request → FastAPI route → query param validation → `pipeline()`:
1. Grid detection (`grids.py`)
2. Subset data to tile bbox with padding
3. Coordinate reprojection (`lib.py`, optimized EPSG:4326→3857 fast path)
4. Optional curvilinear→rectilinear approximation
5. Async data loading (configurable concurrency/timeout)
6. Render via `RenderRegistry` → `Renderer.render()` → PNG/JPEG response

### Renderer Registry (`render/`)
- `RenderRegistry`: Singleton loaded from entry points (`xpublish_tiles.renderer`)
- `Renderer` (ABC): implement `render()`, `render_error()`, `style_id()`, `supported_variants()`, `describe_style()`
- Currently registered: `DatashaderRasterRenderer` (`render/raster.py`)

### Key Types (`types.py`)
- `ValidatedArray`: Holds data, grid, and datatype info
- `RenderContext`: Abstract base → `NullRenderContext` (errors) / `PopulatedRenderContext` (full data)
- `DataType` → `ContinuousData` (valid_min/max) / `DiscreteData` (CF flag_values/flag_meanings)

### Configuration (`config.py`)
Donfig-based configuration; all settings overridable via `XPUBLISH_TILES_*` environment variables. Key settings: `num_threads`, `async_load`, `async_load_timeout_per_tile`, `detect_approx_rectilinear`, `max_renderable_size`.

### Testing Infrastructure
- **Snapshot testing**: `syrupy` for PNG comparisons — do not recreate snapshots by default
- **Property testing**: `hypothesis` with CI/default profiles
- **Visual debugging**: `--debug-visual` and `--debug-visual-save` pytest flags
- **Test datasets**: `xpublish_tiles.testing` module provides factories for different grid types

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
ALWAYS run pre-commit checks before committing.
ALWAYS put imports at the top of the file unless you need to avoid circular import issues.
Do not add obvious or silly comments. Code should be self-explanatory.
For pytest fixtures, prefer separate independent parametrized inputs over using itertools.product() for cleaner test combinations.
Do not recreate snapshots by default.
Do not add unnecessary comments.
Add imports to the top of the file unless necessary to avoid circular imports.
Never add try/except clauses that catch Exceptions in a test.
Never remove test cases without confirming with me first.
