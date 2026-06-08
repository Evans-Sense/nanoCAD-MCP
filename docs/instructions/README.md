# nanoCAD MCP Server - Инструкции и документация

## Содержание

### Инструкции по nanoCAD 26

| Файл | Описание |
|------|----------|
| [00_nanoCAD_overview.md](00_nanoCAD_overview.md) | Обзор платформы, модули, системные требования |
| [01_2d_drawing_commands.md](01_2d_drawing_commands.md) | Команды 2D черчения: примитивы, редактирование, привязки |
| [02_3d_modeling_commands.md](02_3d_modeling_commands.md) | Команды 3D моделирования: примитивы, выдавливание, сборки |
| [03_dimensions_and_annotation.md](03_dimensions_and_annotation.md) | Размеры, аннотации, штриховки, текст |
| [04_blocks_and_references.md](04_blocks_and_references.md) | Блоки, внешние ссылки, динамические блоки |
| [05_layers_and_properties.md](05_layers_and_properties.md) | Слои, свойства объектов, цвета, типы линий |

### Разработка MCP-сервера

| Файл | Описание |
|------|----------|
| [06_server_improvements.md](06_server_improvements.md) | **Доработки сервера** - полный список необходимых API-эндпоинтов |

## Краткая сводка по доработкам

### Текущее покрытие API nanoCAD: ~15%

```
Реализовано:  46 инструментов (2D + 3D)
Отсутствует: ~250+ инструментов
```

### Приоритеты доработки

1. **Приоритет 1 (Критично):** Редактирование 2D, размеры, штриховки
2. **Приоритет 2 (Важно):** Блоки, расширение слоёв, 3D-редактирование
3. **Приоритет 3 (Полезно):** Измерения, управление чертежом, ссылки
4. **Приоритет 4 (Продвинутое):** Параметрическое моделирование, сборки, модули

### Ожидаемое покрытие после доработок

| Фаза | Инструментов | Покрытие |
|------|-------------|----------|
| Текущее | 46 | ~15% |
| Фаза 1 | +120 | ~50% |
| Фаза 2 | +80 | ~70% |
| Фаза 3 | +60 | ~85% |
| Фаза 4 | +40 | ~95% |

## Быстрый старт

### Запуск MCP-сервера
```powershell
cd F:\nanoCAD\server
py -m src.presentation.server
```

### Запуск скрипта проекта
```powershell
cd F:\nanoCAD\server
py -m scripts.bearing_bracket
```

### Доступные скрипты проектов
- `scripts/flange_coupling.py` - Фланцевое соединение
- `scripts/chair.py` - Офисное кресло
- `scripts/bearing_bracket.py` - Опора подшипника (учебное задание)
- `scripts/plow_30hp.py` - Плуг для трактора 30 л.с.

## Ссылки на документацию

- **Официальный портал:** https://docs.nanocad.ru/home/ru-ru/
- **Онлайн-справка:** https://nanocad.com/learning/online-help/nanocad-platform/
- **PDF руководство:** https://www.nanocad.in/assets/pdf/User-guide-nanoCAD-26.pdf
- **Форум:** https://forum.nanocad.ru/
- **GitHub (MCP Server):** F:\nanoCAD\server\
