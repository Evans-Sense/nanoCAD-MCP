# Skill: nano-cad-mcp

# nanoCAD MCP Server — Справочник инструментов

## Общая информация

MCP сервер nanoCAD предоставляет **183 инструмента** для создания и редактирования
CAD-чертежей через протокол Model Context Protocol.

**Подключение (приоритет):**
- `HTTP (.NET engine)` — полный функционал (~175 инструментов; nanoCAD с загруженным плагином `CadEngine.Plugin`)
- `COM` — базовые операции (nanoCAD без плагина, только `health_check`, `get_system_info`)
- `offline` — только проверка доступности

**Статистика (июнь 2026):**
- **183 MCP инструмента** в `TOOL_DEFS` / `_TOOL_HANDLER_MAP`
- **777 unit-тестов**, 81% Python code coverage
- **189 integration-тестов** проходят против живого nanoCAD, 33 skipp (Plus/Pro features)
- **35+ C# сервисов** в .NET плагине, 0 вызовов `CadContext.SendCommand()`

**Требуется .NET engine** — если примечание «requires .NET engine», инструмент
работает только при запущенном плагине.

**Graceful degradation:** При недоступности nanoCAD все MCP инструменты возвращают
русское сообщение: *«ОШИБКА: nanoCAD недоступен. Запустите nanoCAD с загруженным
.NET плагином...»*. `health_check` и `get_system_info` остаются рабочими для диагностики.

**Важно:** `create_note_comb` и `create_dim_number` блокируются на фоновом потоке
и НЕ работают через HTTP API (требуют главный CAD-поток).

---

## Сводка по категориям

| # | Категория | Инструментов | Требует .NET |
|---|-----------|-------------|-------------|
| 1 | Система | 6 | частично |
| 2 | 2D примитивы | 16 | частично |
| 3 | Трансформации | 7 | да |
| 4 | 3D трансформации | 6 | да |
| 5 | Слои | 11 | частично |
| 6 | Блоки | 6 | да |
| 7 | Документ | 16 | частично |
| 8 | 3D тела | 16 | да |
| 9 | 3D утилиты | 3 | да |
| 10 | Условные обозначения | 9 | да |
| 11 | Таблицы | 4 | да |
| 12 | Штриховка | 4 | да |
| 13 | Размеры | 8 | да |
| 14 | Измерения | 6 | да |
| 15 | Обрезка/Смещение | 3 | да |
| 16 | Доп. примитивы | 4 | да |
| 17 | Выборка | 2 | да |
| 18 | 2D ограничения | 12 | да |
| 19 | Сборка | 5 | да |
| 20 | Листовой металл | 5 | да |
| 21 | 3D особенности | 13 | да |
| 22 | Сетка/Вьюпорт/Рендер | 4 | да |
| 23 | NURBS / IFC | 5 | да |
| 24 | MultiCAD API | 12 | да |
| | **ИТОГО** | **183** | |

---

## 1. Системные инструменты (6)

### health_check
- **Описание:** Проверка доступности nanoCAD
- **Параметры:** (нет)
- **Результат:** `"available"` или сообщение об ошибке
- **Работает:** offline

### get_system_info
- **Описание:** Информация о версии nanoCAD, хосте, режиме работы
- **Параметры:** (нет)
- **Работает:** offline

### get_system_fonts
- **Описание:** Список доступных шрифтов
- **Параметры:** (нет)
- **Требует:** .NET engine

### get_system_variable / set_system_variable
- **Описание:** Получить/установить системную переменную CAD
- **Параметры:** `name, [value]`
- **Пример:** `get_system_variable(name="DWGNAME")` → `"Drawing1.dwg"`
- **Работает:** COM (без плагина)

### execute_command
- **Описание:** Выполнить произвольную CAD-команду
- **Параметры:** `command, [args: [str,...]]`
- **Пример:** `execute_command(command="ZOOM", args=["E"])` → Zoom Extents
- **Требует:** .NET engine

---

## 2. 2D примитивы (16)

### create_line
- **Параметры:** `x1, y1, x2, y2, [layer]`
- **Пример:** `create_line(x1=0, y1=0, x2=100, y2=0, layer="Контур")`

### create_circle
- **Параметры:** `cx, cy, radius, [layer]`

### create_arc
- **Параметры:** `cx, cy, radius, start_angle, end_angle, [layer]` (углы в градусах)

### create_rectangle
- **Параметры:** `x1, y1, x2, y2, [layer]`

### create_polyline
- **Параметры:** `vertices: [[x,y],...], [closed: bool], [layer]`

### create_text
- **Параметры:** `x, y, content, height, [layer]`

### create_mtext
- **Параметры:** `x1, y1, x2, y2, content, height, [layer]`
- **Требует:** .NET engine

### create_point
- **Параметры:** `x, y, [layer]`

### create_ellipse
- **Параметры:** `cx, cy, major_axis_x, major_axis_y, [radius_ratio], [layer]`
- **Требует:** .NET engine

### create_spline
- **Параметры:** `fit_points: [[x,y],...], [degree], [closed], [layer]`
- **Требует:** .NET engine

### create_helix
- **Параметры:** `center_x, center_y, center_z, start_radius, end_radius, height, turns, [layer]`
- **Требует:** .NET engine

### create_region
- **Параметры:** `curve_handles: [str,...]`
- **Требует:** .NET engine

### create_boundary
- **Параметры:** `point_x, point_y, [layer]`
- **Требует:** .NET engine

### delete_entity
- **Параметры:** `handle`
- **Работает:** COM

### get_entity
- **Параметры:** `handle`
- **Требует:** .NET engine

---

## 3. Редактирование / Трансформации (7)

### move_entity
- **Параметры:** `handle, dx, dy`

### copy_entity
- **Параметры:** `handle`

### rotate_entity
- **Параметры:** `handle, angle` (градусы)

### scale_entity
- **Параметры:** `handle, factor, [cx, cy]`

### mirror_entity
- **Параметры:** `handle, p1_x, p1_y, p2_x, p2_y`

### stretch_entity
- **Параметры:** `handle, dx, dy`

### explode_entity
- **Параметры:** `handle`

Все в этом разделе требуют .NET engine.

---

## 4. 3D трансформации (6)

### divide_entity
- **Параметры:** `handle, segments`
- **Требует:** .NET engine

### measure_entity
- **Параметры:** `handle, distance`
- **Требует:** .NET engine

### array_3d
- **Параметры:** `handle, count_x, [count_y], [count_z], [spacing_x], [spacing_y], [spacing_z]`
- **Требует:** .NET engine

### align_3d
- **Параметры:** `handle, src_p1_{x,y,z}, src_p2_{x,y,z}, src_p3_{x,y,z}, dst_p1_{x,y,z}, dst_p2_{x,y,z}, dst_p3_{x,y,z}`
- **Требует:** .NET engine

### mirror_3d
- **Параметры:** `handle, p1_{x,y,z}, p2_{x,y,z}, p3_{x,y,z}`
- **Требует:** .NET engine

---

## 5. Слои (11)

### create_layer
- **Параметры:** `name`
- **Работает:** COM

### get_layers
- **Параметры:** (нет)
- **Работает:** COM

### get_linetypes
- **Параметры:** (нет)
- **Требует:** .NET engine

### set_current_layer
- **Параметры:** `name`
- **Работает:** COM

### set_layer_state
- **Параметры:** `name, [on: bool], [frozen: bool], [locked: bool]`
- **Требует:** .NET engine

### delete_layer
- **Параметры:** `name`
- **Требует:** .NET engine

### layer_isolate
- **Параметры:** `name`
- **Требует:** .NET engine

### layer_off
- **Параметры:** `name`
- **Требует:** .NET engine

### layer_freeze
- **Параметры:** `name`
- **Требует:** .NET engine

### layer_on_all
- **Параметры:** (нет)
- **Требует:** .NET engine

### layer_thaw_all
- **Параметры:** (нет)
- **Требует:** .NET engine

---

## 6. Блоки (6)

### get_blocks
- **Параметры:** (нет)
- **Требует:** .NET engine

### get_block_entities
- **Параметры:** `name`
- **Требует:** .NET engine

### insert_block
- **Параметры:** `name, x, y, [scale], [rotation]`
- **Требует:** .NET engine

### create_block
- **Параметры:** `name, handles: [str,...], [base_x], [base_y]`
- **Требует:** .NET engine

### explode_block
- **Параметры:** `name`
- **Требует:** .NET engine

### delete_block
- **Параметры:** `name`
- **Требует:** .NET engine

---

## 7. Документ (16)

### get_document_info
- **Параметры:** (нет)

### save_document
- **Параметры:** `[path]`
- **Пример:** `save_document(path="C:/Projects/val.dwg")`

### new_document
- **Параметры:** `[template]`
- **Требует:** .NET engine

### open_document
- **Параметры:** `path`
- **Требует:** .NET engine

### close_document
- **Параметры:** `[save: bool]`
- **Требует:** .NET engine

### create_project
- **Параметры:** `name, [folder]`
- **Требует:** .NET engine

### save_project
- **Параметры:** `name`
- **Требует:** .NET engine

### export_pdf
- **Параметры:** `path`

### export_dwg
- **Параметры:** `path`
- **Требует:** .NET engine

### export_dxf
- **Параметры:** `path`
- **Требует:** .NET engine

### export_step
- **Параметры:** `path`
- **Требует:** .NET engine

### export_stl
- **Параметры:** `path, [binary: bool]`
- **Требует:** .NET engine

### export_ifc
- **Параметры:** `path`
- **Требует:** .NET engine

### import_step
- **Параметры:** `path`
- **Требует:** .NET engine

### zoom_extents
- **Параметры:** (нет)

### undo / redo / purge
- **Параметры:** (нет)
- **Требует:** .NET engine

---

## 8. 3D твёрдотельные примитивы (16)

### create_box / create_sphere / create_cylinder / create_cone / create_torus / create_wedge / create_pyramid
- **Параметры:** зависят от примитива (размеры, радиусы, высота)
- **Примеры:**
  - `create_box(x=100, y=100, z=50)`
  - `create_cylinder(radius=30, height=100)`
  - `create_cone(base_radius=50, height=100)`
  - `create_torus(major_radius=60, minor_radius=20)`

### extrude_solid
- **Параметры:** `handle, height, [taper_angle]`

### revolve_solid
- **Параметры:** `handle, axis_{x,y,z}, dir_{x,y,z}, angle`

### sweep_solid
- **Параметры:** `profile_handle, path_handle`

### loft_solid
- **Параметры:** `section_handles: [str,...]`

### boolean_union / boolean_subtract / boolean_intersect
- **Параметры:** `handle1, handle2`

### fillet_edge / chamfer_edge
- **Параметры:** `handle, radius` / `handle, dist1, [dist2]`

### move_solid
- **Параметры:** `handle, dx, dy, dz`

Все в этом разделе требуют .NET engine.

---

## 9. 3D утилиты (3)

### set_3d_view
- **Параметры:** `direction, [render_mode]`
- **Направления:** `top`, `bottom`, `left`, `right`, `front`, `back`,
  `SW_ISOMETRIC`, `SE_ISOMETRIC`, `NE_ISOMETRIC`, `NW_ISOMETRIC`
- **Режимы:** `WIREFRAME`, `CONCEPTUAL`, `REALISTIC`, `SHADED`

### get_solid_properties
- **Параметры:** `handle`
- **Возвращает:** объём, масса, площадь поверхности, центр масс

---

## 10. Условные обозначения (9)

### create_roughness
- **Параметры:** `value, [angle], [allowance], [type]`
- **ГОСТ шероховатость**

### create_old_roughness
- **Параметры:** `value, [angle], [method], [companion_mirror], [surf_pos]`

### create_tolerance
- **Параметры:** `[type1], [value1], [letters1], [type2], [value2], [letters2], [text]`

### create_datum
- **Параметры:** `letter`

### create_weld
- **Параметры:** `[swap_sides], [right_orientation], [length_above], [length_below]`
- **ISO сварной шов**

### create_leader
- **Параметры:** `arrow_x, arrow_y, bend_x, bend_y, shelf_x, shelf_y, text, [text_below]`

### create_note_comb
- **Параметры:** `[angle], [text_size], [first_line], [second_line]`
- ⚠ **БЛОКИРУЕТСЯ** на фоновом потоке — не работает через HTTP API

### create_dim_number
- **Параметры:** `x, y, arrow_x, arrow_y, text, [index], [autonum]`
- ⚠ **БЛОКИРУЕТСЯ** — не работает через HTTP API

### create_mleader
- **Параметры:** `arrow_x, arrow_y, leader_x, leader_y, text, [text_height], [layer]`

Все в этом разделе требуют .NET engine.

---

## 11. Таблицы (4)

### create_table
- **Параметры:** `[rows], [columns], [row_height], [column_width], [cells: [{row_index, column_index, value}]]`

### edit_table_cell
- **Параметры:** `table_handle, row, col, value, [row_height], [col_width]`

### get_table_info
- **Параметры:** `table_handle`

### delete_table
- **Параметры:** `table_handle`

Все требуют .NET engine.

---

## 12. Штриховка (4)

### create_hatch
- **Параметры:** `[pattern], [scale], [rotation], [boundary_handles], [boundary_points]`
- **Пример:** `create_hatch(pattern="ANSI31", scale=1.0, boundary_handles=["ABC"])`
- **Важно:** nanoCAD Free не имеет `acad.pat` — все предопределённые образцы (ANSI31, ANGLE и т.д.) не работают. Используйте `SOLID` (всегда встроен).

### create_gradient
- **Параметры:** `color1, color2, [scale], [gradient_type], [boundary_handles], [point_xs], [point_ys]`

### get_hatch_info
- **Параметры:** `handle`

### edit_hatch
- **Параметры:** `handle, [pattern], [scale], [rotation]`

Все требуют .NET engine.

---

## 13. Размеры (8)

### create_aligned_dimension
- **Параметры:** `x1, y1, x2, y2, dim_x, dim_y`

### create_rotated_dimension
- **Параметры:** `x1, y1, x2, y2, dim_x, dim_y, rotation`

### create_linear_dimension
- **Параметры:** `x1, y1, x2, y2, dim_x, dim_y, [direction]`

### create_radial_dimension
- **Параметры:** `center_x, center_y, arc_x, arc_y`

### create_diametric_dimension
- **Параметры:** `center_x, center_y, arc_x, arc_y`

### create_angular_dimension
- **Параметры:** `center_x, center_y, p1_x, p1_y, p2_x, p2_y`

### create_ordinate_dimension
- **Параметры:** `use_x_axis, defining_x, defining_y, leader_x, leader_y`

### create_arc_length_dimension
- **Параметры:** `center_x, center_y, radius, start_angle, end_angle, dim_x, dim_y`

Все требуют .NET engine.

---

## 14. Измерения (6)

### get_distance
- **Параметры:** `x1, y1, [z1], x2, y2, [z2]`

### get_angle
- **Параметры:** `x1, y1, x2, y2, x3, y3, x4, y4` (угол между линиями 1-2 и 3-4)

### get_area
- **Параметры:** `handle`

### get_entity_info
- **Параметры:** `handle`
- **Возвращает:** тип, слой, цвет, геометрические параметры

### get_all_entities
- **Параметры:** (нет)
- **Возвращает:** список всех объектов в пространстве модели

### get_entity_detail
- **Параметры:** `handle`
- **Возвращает:** расширенная информация

Все требуют .NET engine.

---

## 15. Обрезка / Удлинение / Смещение (3)

### trim_entity
- **Параметры:** `handle, cut_x, cut_y, [keep_start]`

### extend_entity
- **Параметры:** `handle, end_x, end_y`

### offset_entity
- **Параметры:** `handle, distance`

Все требуют .NET engine.

---

## 16. Дополнительные примитивы (4)

### create_polygon
- **Параметры:** `center_x, center_y, radius, sides, [inscribed], [layer]`

### create_donut
- **Параметры:** `center_x, center_y, inner_radius, outer_radius, [layer]`

### create_xline
- **Параметры:** `p1_x, p1_y, p2_x, p2_y, [layer]`

### create_ray
- **Параметры:** `p1_x, p1_y, p2_x, p2_y, [layer]`

Все требуют .NET engine.

---

## 17. Выборка (2)

### select_entities
- **Параметры:** `[entity_type], [layer], [color], [max_count]`
- **Типы:** `AcDbLine`, `AcDbCircle`, `AcDbPolyline`, `AcDbText`, `AcDbBlockReference`, `AcDb3dSolid` и др.

### select_by_handles
- **Параметры:** `handles: [str,...]`

Все требуют .NET engine.

---

## 18. 2D ограничения (12)

### constraint_parallel / constraint_perpendicular / constraint_collinear / constraint_coincident / constraint_concentric / constraint_tangent / constraint_horizontal / constraint_vertical / constraint_fix / constraint_equal / constraint_symmetric / constraint_distance

Все требуют .NET engine.

---

## 19. Сборка (5)

### insert_part
- **Параметры:** `block_name, [x], [y], [z]`

### assembly_mate / assembly_angle / assembly_tangent / assembly_symmetry

Все требуют .NET engine.

---

## 20. Листовой металл (5)

### create_base_flange / create_base_plate
- **Параметры:** `[x], [y], width, length, thickness`

### create_edge_flange
- **Параметры:** `handle, width, [angle]`

### create_bend
- **Параметры:** `handle, radius, [angle]`

### unfold_sheet_metal
- **Параметры:** `handle, x, y`

Все требуют .NET engine.

---

## 21. 3D особенности / Sketches (13)

### create_sketch
- **Параметры:** `[plane], [name]`

### add_sketch_circle
- **Параметры:** `sketch, cx, cy, radius`

### add_sketch_line
- **Параметры:** `sketch, x1, y1, x2, y2`

### create_profile
- **Параметры:** `sketch`

### create_extrude_feature / create_revolve_feature
- **Параметры:** `profile, [distance], [angle]`

### create_simple_hole / create_standard_hole / create_threaded_hole
- **Параметры:** `face, [diameter], [depth]`

### create_shell
- **Параметры:** `body, [thickness]`

### create_mirror_feature
- **Параметры:** `body, [mirror_plane]`

### create_circular_pattern / create_rectangular_pattern
- **Параметры:** `body, count, [spacing]`

Все требуют .NET engine.

---

## 22. Сетка / Вьюпорт / Рендер (4)

### create_mesh
- **Параметры:** `vertices: [[x,y,z],...], face_indices: [int,...], [smooth_level], [layer]`
- **Требует:** .NET engine

### edit_mesh
- **Параметры:** `handle, [smooth_level]`
- **Требует:** .NET engine

### set_viewport
- **Параметры:** `name`
- **Требует:** .NET engine

### render
- **Параметры:** `[output_path]`
- **Требует:** .NET engine

---

## 23. NURBS / IFC (5)

### create_nurb_curve
- **Параметры:** `control_points: [[x,y,z],...], [degree], [knots]`

### create_nurb_surface
- **Параметры:** `control_points: [[x,y,z],...], degree_u, degree_v, [knots_u], [knots_v]`
- **Примечание:** `NurbSurface` конструктор в Teigha возвращает `eNotImplementedYet`

### modify_nurb
- **Параметры:** `handle, [control_points], [degree]`

### import_ifc
- **Параметры:** `path`

### get_ifc_entities
- **Параметры:** (нет) — получить IFC-объекты из чертежа

Все требуют .NET engine.

---

## 24. MultiCAD API (12)

Расширенные функции через `Multicad.*` API (.NET engine).

### create_grid_axis
- **Параметры:** `x, y, [angle], [label_x], [label_y], [length]`
- **Координационные оси**

### create_grid_label
- **Параметры:** `axis, label`
- **Марки осей**

### create_room
- **Параметры:** `points: [[x,y],...], [name], [level]`
- **Помещение**

### get_room_properties
- **Параметры:** `room_handle`

### create_custom_object
- **Параметры:** `[properties: dict]`
- **Пользовательский объект**

### create_parametric_object
- **Параметры:** `[parameters: dict]`
- **Параметрический объект**

### create_reactor
- **Параметры:** `[event], [callback]`
- **Реактор на события CAD**

### create_2d_break
- **Параметры:** `[handle], [point_x], [point_y], [direction_angle]`
- **Разрыв на 2D виде**

### start_motion_preview / stop_motion_preview
- **Предпросмотр движения сборки**

### create_body_contour
- **Параметры:** `[handle], [projection_plane]`
- **Контур тела на плоскости**

### check_3d_faces
- **Параметры:** `[handle]`
- **Проверка 3D граней**

Все требуют .NET engine.

---

## Типовые последовательности вызовов

### Создание 2D чертежа
```
1. create_layer(name="Контур")
2. create_layer(name="Оси")
3. set_current_layer(name="Оси")
4. create_line(x1=0, y1=-10, x2=0, y2=110)
5. set_current_layer(name="Контур")
6. create_rectangle(x1=-50, y1=0, x2=50, y2=100)
7. create_circle(cx=0, cy=50, radius=25)
8. zoom_extents()
```

### 3D моделирование с булевыми операциями
```
1. create_box(x=200, y=100, z=50)
2. create_cylinder(radius=20, height=50)
3. boolean_subtract(handle1="BOX_123", handle2="CYL_456")
4. fillet_edge(handle="BOX_123", radius=5)
5. set_3d_view(direction="SE_ISOMETRIC")
```

### Экспорт документа
```
1. save_document(path="C:/output/project.dwg")
2. export_pdf(path="C:/output/project.pdf")
3. export_step(path="C:/output/project.step")
4. export_stl(path="C:/output/project.stl", binary=true)
5. export_ifc(path="C:/output/project.ifc")
```

### Работа со слоями
```
1. get_layers()
2. create_layer(name="Штриховка")
3. set_current_layer(name="Штриховка")
4. create_hatch(pattern="SOLID", boundary_points=[[0,0],[100,0],[100,50],[0,50]])
5. layer_isolate(name="Штриховка")
```

### Таблицы с данными
```
1. create_table(rows=4, columns=3, cells=[
     {"row_index": 0, "column_index": 0, "value": "№"},
     {"row_index": 0, "column_index": 1, "value": "Наименование"},
     {"row_index": 0, "column_index": 2, "value": "Кол."},
     {"row_index": 1, "column_index": 0, "value": "1"},
     {"row_index": 1, "column_index": 1, "value": "Вал"},
     {"row_index": 1, "column_index": 2, "value": "2"},
   ])
2. get_table_info(table_handle="TBL_123")
3. edit_table_cell(table_handle="TBL_123", row=1, col=1, value="Ось")
```

### Работа с инженерными символами
```
1. create_roughness(value="3.2")
2. create_tolerance(type1="∥", value1="0.05", letters1="A")
3. create_datum(letter="A")
4. create_weld(length_above="8")
5. create_leader(arrow_x=50, arrow_y=50, bend_x=80, bend_y=70,
     shelf_x=120, shelf_y=70, text="Сварка")
```

---

## Тестовый статус

```
Покрытие кода Python: 81%
Unit-тесты:            777 passed
Integration-тесты:     189 passed, 33 skipped, 0 failed
MCP server тесты:      51 passed (45 HTTP + 6 graceful degradation)
Типы (mypy --strict):  clean
Линтер (ruff):         clean
```

## Демо-скрипты

- `demo_lite.py` — 14 категорий, ~47 objects, 7 layers, 6 blocks
- `demo_engineering_project.py` — 24 категории, максимальный охват MCP инструментов
- `demo_bracket.py`, `demo_3d_part.py`, `bearing_bracket.py`, `flange_coupling.py`,
  `chair.py`, `apartment_plan.py`, `plow_30hp.py`, `create_lighthouse.py`
