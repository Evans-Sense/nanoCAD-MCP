# nanoCAD MCP Server

## Project Structure
```
F:\nanoCAD\
├── server/                    # Python MCP server
│   ├── src/
│   │   ├── domain/            # Entities, value objects, interfaces
│   │   ├── application/       # Use cases
│   │   ├── infrastructure/    # COM bridge, HTTP bridge, SafeBridge, repository
│   │   └── presentation/      # MCP server + tool definitions
│   ├── scripts/               # Demo scripts
│   ├── tests/
│   │   ├── unit/              # 777+ unit tests (mocked)
│   │   └── integration/       # 165+ integration tests (live nanoCAD)
│   └── pyproject.toml
├── engine/CadEngine.Plugin/   # .NET plugin inside nanoCAD (HttpListener :5080)
├── MultiCAD_API/              # SDK assemblies
└── .opencode/                 # Agent configuration + skill
```

## Demos

### `demo_lite.py` — быстрый обзор всех категорий
```powershell
py F:\nanoCAD\server\scripts\demo_lite.py
```
14 категорий, ~47 entities, 7 layers, 6 blocks. Результат в `%TEMP%/nanoCAD_demo/`.

### `demo_engineering_project.py` — расширенная версия
```powershell
py F:\nanoCAD\server\scripts\demo_engineering_project.py
```
24 категории, максимальный охват MCP инструментов.

### Другие демо
`demo_bracket.py`, `demo_3d_part.py`, `bearing_bracket.py`, `flange_coupling.py`, `chair.py`, `apartment_plan.py`, `plow_30hp.py`, `create_lighthouse.py`

## Commands

### Run MCP server
```powershell
cd F:\nanoCAD\server
py -m src.presentation.server
```

### Debug mode
```powershell
$env:NANOCAD_MCP_DEBUG = "1"
py -m src.presentation.server
```

### Run tests
```powershell
cd F:\nanoCAD\server
py -m pytest tests/ -v                                      # all tests
py -m pytest tests/unit/ -v --cov=src                       # unit + coverage
py -m pytest tests/integration/ -v                           # integration (requires nanoCAD running)
```

### Lint / Type check
```powershell
cd F:\nanoCAD\server
py -m ruff check src/
py -m ruff format src/
py -m mypy src/
```

### Build .NET engine plugin
```powershell
& "C:\Program Files\dotnet\dotnet.exe" build "F:\nanoCAD\engine\CadEngine.Plugin\CadEngine.Plugin.csproj"
```

### Install plugin (nCad.ini)
Add DLL path to `[\NetModules]` in `F:\nanoCAD\nanoCAD\nCad.ini`:
```
F:\nanoCAD\engine\CadEngine.Plugin\bin\Debug\CadEngine.Plugin.dll
```
Restart nanoCAD.

### Live HTTP API test
```powershell
Invoke-RestMethod -Uri "http://localhost:5080/api/system/health"
Invoke-RestMethod -Uri "http://localhost:5080/api/document"
Invoke-RestMethod -Uri "http://localhost:5080/api/layer"
```

## Architecture

- **Python MCP Server** (stdio + SSE transport) — validates input, routes tool calls, 183 tool definitions
- **.NET Engine Plugin** — hostmgd/hostdbmgd API inside nanoCAD, HttpListener REST API on localhost:5080
- **SafeBridge** (obatnik.py) — отказоустойчивая обёртка над HTTP-мостом с авто-reconnect, задержками и обработкой ошибок
- **COM Bridge** (fallback) — basic operations via `nanoCAD.Application` COM

Connection priority: HTTP (.NET engine) → COM → offline

## Key Components

| Component | Path | Description |
|-----------|------|-------------|
| Tool definitions | `server/src/presentation/tool_defs.py` | 183 MCP tools |
| HTTP bridge | `server/src/infrastructure/http_bridge.py` | REST client to .NET plugin |
| SafeBridge | `server/src/infrastructure/safe_bridge.py` | Error-tolerant wrapper |
| CadRepository | `server/src/infrastructure/cad_repository.py` | Strategy: HTTP → COM → offline |
| ICadRepository | `server/src/domain/interfaces.py` | Port interface for all CAD ops |

## Test Status

- **777 unit tests** passing (81% coverage)
- **189 integration tests** passing (requires live nanoCAD)
- **33 integration tests** skipped (Plus/Pro license features)
- **51 MCP server tests** passing (full chain: server -> use_case -> HTTP -> CAD)
- **0 SendCommand callers** remaining (all replaced with synchronous `Editor.Command()` or programmatic API)
