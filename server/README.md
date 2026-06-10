# nanoCAD MCP Server

MCP сервер для автоматизации nanoCAD. **183 инструмента** для 2D/3D черчения, инженерных символов, размеров, листового металла, сборок, IFC, NURBS и MultiCAD API.

## Установка

```powershell
cd server
pip install -e .
pip install -e ".[sse]"  # для SSE транспорта (удалённый доступ)
```

## Запуск

### stdio (для MCP-клиентов: Claude Desktop, opencode)

```powershell
cd server
py -m src.presentation.server
```

### SSE (удалённый доступ, на разных устройствах)

```powershell
# Запуск сервера
py -m src.presentation.server --transport sse --port 8081

# Или через bat-файл
start_mcp.bat
```

### Аргументы командной строки

| Аргумент | Описание | По умолчанию |
|----------|----------|--------------|
| `--transport` | `stdio` или `sse` | `stdio` |
| `--port` | Порт для SSE | `8081` |
| `--host` | Хост для SSE | `0.0.0.0` |

## Интеграция с opencode

### Локальный сервер (рекомендуется)

```jsonc
// ~/.config/opencode/opencode.jsonc
{
  "mcp": {
    "nanoCAD": {
      "type": "local",
      "command": ["py", "-m", "src.presentation.server"],
      "cwd": "F:\\nanoCAD\\server",
      "environment": {
        "PYTHONPATH": "F:\\nanoCAD\\server\\src"
      }
    }
  }
}
```

### Удалённый сервер (SSE)

```jsonc
{
  "mcp": {
    "nanoCAD": {
      "type": "remote",
      "url": "http://your-server:8081/sse"
    }
  }
}
```

## Интеграция с Claude Desktop

```jsonc
// %APPDATA%\Claude\claude_desktop_config.json
{
  "mcpServers": {
    "nanoCAD": {
      "command": "py",
      "args": ["-m", "src.presentation.server"],
      "cwd": "F:\\nanoCAD\\server",
      "env": {
        "PYTHONPATH": "F:\\nanoCAD\\server\\src"
      }
    }
  }
}
```

## Интеграция с Cursor

```jsonc
// ~/.cursor/mcp.json
{
  "mcpServers": {
    "nanoCAD": {
      "command": "py",
      "args": ["-m", "src.presentation.server"],
      "cwd": "F:\\nanoCAD\\server",
      "env": {
        "PYTHONPATH": "F:\\nanoCAD\\server\\src"
      }
    }
  }
}
```

## Архитектура

```
server/src/
├── domain/              # Сущности, интерфейсы (ICadRepository)
├── application/         # Use cases, реестр инструментов
├── infrastructure/      # HTTP bridge (.NET engine), COM bridge, offline
└── presentation/        # MCP сервер, tool definitions, валидация
```

**Приоритет подключения:** HTTP (.NET engine) → COM → offline

### Ключевые компоненты

| Компонент | Назначение |
|-----------|-----------|
| `ToolRegistry` | Декларативная регистрация инструментов через `@tool()` |
| `ToolDef` | Описание инструмента (name, description, parameters, handler) |
| `tool_defs.py` | Все 183 определения инструментов |
| `tool_validation.py` | Валидация аргументов по JSON Schema |
| `CadRepository` | Стратегия HTTP → COM → offline |

## MCP транспорты

| Транспорт | Использование | Протокол |
|-----------|--------------|----------|
| **stdio** | Claude Desktop, opencode (локально) | stdin/stdout JSON-RPC |
| **SSE** | Удалённый доступ, другие устройства | HTTP Server-Sent Events |

## Инструменты (183)

### 2D примитивы
`create_line` `create_circle` `create_arc` `create_polyline` `create_rectangle` `create_text` `create_mtext` `create_point` `create_ellipse` `create_spline` `create_polygon` `create_donut` `create_xline` `create_ray` `create_helix` `create_region` `create_boundary` `create_mleader`

### 3D тела
`create_box` `create_sphere` `create_cylinder` `create_cone` `create_torus` `create_wedge` `create_pyramid`

### 3D операции
`extrude_solid` `revolve_solid` `sweep_solid` `loft_solid` `fillet_edge` `chamfer_edge`

### Булевы операции
`boolean_union` `boolean_subtract` `boolean_intersect`

### Слои
`create_layer` `get_layers` `set_current_layer` `set_layer_state` `delete_layer`

### Трансформации
`move_entity` `copy_entity` `rotate_entity` `scale_entity` `mirror_entity` `stretch_entity` `offset_entity` `trim_entity` `extend_entity`

### Инженерные символы
`create_roughness` `create_tolerance` `create_datum` `create_weld` `create_leader` `create_note_comb` `create_dim_number`

### Размеры
`create_linear_dimension` `create_aligned_dimension` `create_angular_dimension` `create_radial_dimension` `create_diametric_dimension`

### Штриховка и градиент
`create_hatch` `edit_hatch` `get_hatch_info` `create_gradient`

### Блоки
`get_blocks` `insert_block` `create_block` `explode_block` `delete_block` `get_block_entities`

### Документы
`get_document_info` `save_document` `export_pdf` `export_dwg` `export_dxf` `export_step` `export_stl` `import_step` `new_document` `open_document` `close_document` `create_project` `save_project` `export_ifc` `import_ifc`

### 2D ограничения
`constraint_horizontal` `constraint_vertical` `constraint_parallel` `constraint_perpendicular` `constraint_tangent` `constraint_concentric` `constraint_collinear` `constraint_coincident` `constraint_fix` `constraint_equal` `constraint_symmetric` `constraint_distance`

### Сборки
`assembly_mate` `assembly_angle` `assembly_tangent` `assembly_symmetry` `insert_part`

### Листовой металл
`create_base_flange` `create_edge_flange` `create_bend` `unfold_sheet_metal`

### Система
`health_check` `get_system_info` `get_system_variable` `set_system_variable` `execute_command`

### Измерения
`get_distance` `get_area` `get_entity_info` `get_all_entities` `get_entity_detail` `get_solid_properties`

### Дополнительные категории
`create_table` `edit_table_cell` `get_table_info` `delete_table` `create_mesh` `edit_mesh` `create_nurb_curve` `create_nurb_surface` `modify_nurb` `get_ifc_entities` `create_grid_axis` `create_grid_label` `create_room` `get_room_properties` `create_custom_object` `create_parametric_object` `create_reactor` `create_2d_break` `start_motion_preview` `stop_motion_preview` `create_body_contour` `check_3d_faces`

## Тесты

```powershell
cd server

# Все тесты (923 unit + 19 contract + 189 integration)
py -m pytest tests/ -v

# Только unit-тесты
py -m pytest tests/unit/ -v

# С coverage
py -m pytest tests/unit/ -v --cov=src --cov-report=term-missing

# Интеграционные тесты (требуется запущенный .NET engine)
py -m pytest tests/integration/ -v
```

**Статус:** 923 unit ✅ | 189 integration ✅ | 33 skipped (Plus/Pro) | 19 contract ✅ | 86% coverage

## Линтинг

```powershell
cd server
py -m ruff check src/
py -m ruff format src/
```

## Системные требования

- Windows 10/11 64-bit
- Python 3.12+
- nanoCAD 26+ (для .NET engine плагина)
- .NET 8.0 SDK (только для сборки плагина из исходников)

> 💡 **Готовый плагин** уже лежит в `engine/dist/CadEngine.Plugin.dll`.
> Установка .NET SDK не требуется — просто укажите путь к этому DLL в nCad.ini.

## Запуск в SSE режиме (удалённый доступ)

```powershell
# На сервере с nanoCAD
py -m src.presentation.server --transport sse --port 8081 --host 0.0.0.0

# Клиент подключается к http://server-ip:8081/sse
```

## Демо-скрипты

```powershell
# Быстрый обзор (14 категорий, ~47 объектов)
py scripts/demo_lite.py

# Максимальный охват (24 категории)
py scripts/demo_engineering_project.py

# Специализированные
py scripts/demo_bracket.py       # Кронштейн
py scripts/demo_3d_part.py       # 3D деталь
py scripts/bearing_bracket.py    # Корпус подшипника
py scripts/flange_coupling.py    # Фланцевая муфта
py scripts/apartment_plan.py     # План квартиры
```

## Лицензия

MIT
