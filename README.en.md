# 🏗 nanoCAD MCP Server

[![Python](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-777%20unit%20%2B%20222%20integration-green.svg)]()

**MCP server for nanoCAD 26 automation** — 183 tools for 2D/3D drafting, engineering symbols, dimensions, sheet metal, assemblies, IFC, NURBS and MultiCAD API.

Works via [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) with any MCP client: opencode, Claude Desktop, Cursor, and more.

```
AI Agent (opencode / Claude / Cursor)
     │
     │ MCP (stdio / SSE)
     ▼
Python MCP Server (183 tools)
     │
     │ HTTP REST (localhost:5080)
     ▼
.NET Engine Plugin (inside nanoCAD 26)
     │
     │ Multicad.* API / Teigha
     ▼
nanoCAD — drawing
```

## ✨ Feature Overview

| Category | Tools | Highlights |
|-----------|:-----:|------------|
| 2D Primitives | 16 | line, circle, arc, spline, ellipse, helix, region |
| 3D Solids | 16 | box, sphere, cylinder, cone, torus, wedge, pyramid |
| Boolean Operations | 3 | union, subtract, intersect |
| 3D Operations | 7 | extrude, revolve, sweep, loft, fillet, chamfer |
| Dimensions | 8 | linear, radial, diametric, angular, ordinate, arc length |
| Engineering Symbols | 9 | roughness (GOST), tolerances, datums, welding, leaders |
| Layers | 11 | create, isolate, freeze, delete |
| Blocks | 6 | create, insert, explode, delete |
| Tables | 4 | create, edit cells |
| Hatching | 4 | hatch, gradient |
| Transformations | 7 | move, copy, rotate, scale, mirror |
| 3D Transforms | 6 | 3D array, align, 3D mirror |
| 2D Constraints | 12 | parallel, perpendicular, tangent, concentric, fix |
| Assemblies | 5 | mate, angle, tangent, symmetry, insert part |
| Sheet Metal | 5 | base flange, edge flange, bend, unfold |
| 3D Features | 13 | holes, shell, sketches, extrude/revolve features |
| Documents | 16 | create, open, save, export PDF/DWG/DXF/STEP/STL/IFC |
| System | 6 | variables, fonts, linetypes, commands |
| Measurements | 6 | distance, angle, area, entity info |
| NURBS / IFC | 5 | NURBS curves, surfaces, IFC import/export |
| MultiCAD API | 12 | grid axes, rooms, parametric objects, reactors |
| Other | 12 | mesh, selection, trim, extend, offset, viewport, render |
| **TOTAL** | **183** | |

## 🚀 Quick Start

### 1. Installation

```powershell
# Clone the repository
git clone https://github.com/nanoCAD/nanoCAD-MCP.git
cd nanoCAD-MCP

# Install Python package
cd server
pip install -e .
pip install -e ".[sse,dev]"   # for SSE transport and development
```

### 2. Install .NET Plugin

**Option A (recommended):** A pre-built plugin is included in the repository:
`engine\dist\CadEngine.Plugin.dll` (Release, 254 KB). No build required.

**Option B:** Build from source:
```powershell
dotnet build engine\CadEngine.Plugin\CadEngine.Plugin.csproj --configuration Release
```

### 3. Configure nanoCAD

Add the plugin DLL path to `nCad.ini` (section `[\NetModules]`):

```
F:\full\path\to\nanoCAD-MCP\engine\dist\CadEngine.Plugin.dll
```

### 4. Run

```powershell
# Terminal 1: Start nanoCAD 26 (with plugin loaded)

# Terminal 2: Start MCP server
cd server
py -m src.presentation.server
```

### 5. Connect MCP Client

**opencode** (`opencode.json`):
```json
{
  "mcp": {
    "nanoCAD": {
      "command": "py",
      "args": ["-m", "src.presentation.server"],
      "cwd": "F:\\nanoCAD\\server"
    }
  }
}
```

**Claude Desktop** (`%APPDATA%\Claude\claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "nanoCAD": {
      "command": "py",
      "args": ["-m", "src.presentation.server"],
      "cwd": "F:\\nanoCAD\\server"
    }
  }
}
```

**Cursor** (`~/.cursor/mcp.json`):
```json
{
  "mcpServers": {
    "nanoCAD": {
      "command": "py",
      "args": ["-m", "src.presentation.server"],
      "cwd": "F:\\nanoCAD\\server"
    }
  }
}
```

### 6. Verify

```powershell
# Check if the plugin responds
Invoke-RestMethod -Uri "http://localhost:5080/api/system/health"

# Run a demo script (creates a test drawing)
py server\scripts\demo_lite.py
```

## 🔧 Commands

```powershell
# Start server
py -m src.presentation.server
py -m src.presentation.server --transport sse --port 8081   # remote access

# Tests
py -m pytest server/tests/ -v                              # all
py -m pytest server/tests/unit/ -v --cov=src               # unit + coverage
py -m pytest server/tests/integration/ -v                  # integration

# Linting
py -m ruff check server/src/
py -m ruff format server/src/
py -m mypy server/src/

# Demo scripts
py server/scripts/demo_lite.py
py server/scripts/demo_engineering_project.py
py server/scripts/demo_bracket.py
```

## 🧪 Test Status

| Test Type | Count | Status |
|-----------|:-----:|:------:|
| Unit tests (mocked HTTP) | 777 | ✅ Pass |
| Integration (live nanoCAD) | 189 (+33 skipped) | ✅ Pass |
| MCP server (full chain) | 51 | ✅ Pass |
| Types (mypy --strict) | 17 files | ✅ Clean |
| Linter (ruff) | — | ✅ Clean |
| Python code coverage | 81% | ✅ |

## 🔌 Architecture

```
server/src/
├── domain/              # Entities, Value Objects, ports (ICadRepository)
├── application/         # Use cases, DTO, business logic
├── infrastructure/      # HTTP bridge (.NET plugin), COM bridge (fallback), SafeBridge
└── presentation/        # MCP server (stdio/SSE), 183 tool definitions

engine/CadEngine.Plugin/
├── Services/            # 35+ C# services (EntityService, SolidService, SymbolService ...)
├── Models/              # DTO models
└── HttpServer.cs        # REST API (localhost:5080, 170+ endpoints)
```

**Connection priority:** HTTP (.NET engine) → COM → offline

**Graceful degradation:** When nanoCAD is unavailable, all tools return a descriptive error message in Russian (or English with `--lang en`). `health_check` and `get_system_info` remain functional offline.

## 📦 System Requirements

- **OS:** Windows 10/11 64-bit
- **Python:** 3.12+
- **nanoCAD:** 26 (Free/Plus/Pro) with .NET plugin loaded
- **.NET:** 8.0 SDK (only needed to build the plugin from source)

> 💡 **Pre-built plugin** is available at `engine/dist/CadEngine.Plugin.dll`.
> No .NET SDK required — just point nCad.ini to this DLL.

## 🛠 Development

### Adding a New Tool

1. **C# (engine):** DTO in `ApiModels.cs`, method in service, route in `HttpServer.cs`
2. **Python bridge:** Method in `http_bridge.py`
3. **Use case:** Class in `extended_use_cases.py` / `use_cases.py`
4. **MCP:** Definition in `tool_defs.py`, handler map in `server.py`
5. **Tests:** Unit + integration

### Principles

- **MultiCAD API first** — all new tools through .NET engine
- **No SendCommand** — all calls use synchronous `Editor.Command()` or programmatic API
- **Clean Architecture** — strict layer boundaries (domain → application → infrastructure → presentation)
- **TDD** — test first, implement later

## 📄 License

MIT License — open source project.

## 👤 Author

**Ivan Vinogradov** — project developer and architect.

## 🙏 Credits

- [nanoCAD](https://nanocad.ru) and MultiCAD API team
- [Model Context Protocol](https://modelcontextprotocol.io/) community
- All contributors and testers
