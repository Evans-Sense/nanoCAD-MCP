# ⚡ nanoCAD MCP Server — Быстрый старт

Полная настройка от установки до первого чертежа за 10 минут.

## 1. Установка Python-пакета

```powershell
git clone https://github.com/nanoCAD/nanoCAD-MCP.git
cd nanoCAD-MCP\server
pip install -e .
pip install -e ".[sse]"    # опционально: для удалённого доступа
```

## 2. Установка .NET плагина

### Вариант А: Взять готовый (рекомендуется)

В репозитории уже есть собранный плагин:

```
engine\dist\CadEngine.Plugin.dll    (254 KB, Release)
```

Никакой сборки не требуется.

### Вариант Б: Собрать из исходников

```powershell
cd engine\CadEngine.Plugin
dotnet build --configuration Release
```

Результат: `bin\Release\CadEngine.Plugin.dll`.

## 3. Подключение к nanoCAD

Откройте файл `nCad.ini` в папке nanoCAD и добавьте в раздел `[\NetModules]`:

```ini
[\NetModules]
CadEngine.Plugin=F:\nanoCAD-MCP\engine\dist\CadEngine.Plugin.dll
```

**Важно:** укажите абсолютный путь без кавычек.

## 4. Запуск

```powershell
# Терминал 1 — nanoCAD
# Запустите nanoCAD 26, убедитесь что плагин загружен (сообщение в консоли)

# Терминал 2 — MCP сервер
cd F:\nanoCAD-MCP\server
py -m src.presentation.server
```

## 5. Проверка

```powershell
# Проверка HTTP API
Invoke-RestMethod -Uri "http://localhost:5080/api/system/health"

# Должны увидеть: {"status":"ok","mode":"full","host":"nanoCAD x64","timestamp":"..."}
```

## 6. Создание первого чертежа

```powershell
# Запустите демо-скрипт
py scripts\demo_lite.py
```

Или вызовите инструменты напрямую из MCP-клиента:

```
health_check()                                               # проверка связи
create_layer(name="Контур")                                   # создать слой
create_rectangle(x1=0, y1=0, x2=200, y2=100, layer="Контур") # прямоугольник
create_circle(cx=100, cy=50, radius=30, layer="Контур")       # окружность
zoom_extents()                                                # показать всё
save_document(path="C:/Temp/my_first.dwg")                    # сохранить
```

## 7. Подключение MCP-клиента

### opencode
```json
{
  "mcp": {
    "nanoCAD": {
      "command": "py",
      "args": ["-m", "src.presentation.server"],
      "cwd": "F:\\nanoCAD-MCP\\server"
    }
  }
}
```

### Claude Desktop
```json
{
  "mcpServers": {
    "nanoCAD": {
      "command": "py",
      "args": ["-m", "src.presentation.server"],
      "cwd": "F:\\nanoCAD-MCP\\server"
    }
  }
}
```

## 8. Демо-скрипты

| Скрипт | Описание |
|--------|----------|
| `demo_lite.py` | Базовые примитивы: 14 категорий, ~47 объектов |
| `demo_engineering_project.py` | Расширенный: 24 категории, макс. охват |
| `demo_bracket.py` | Кронштейн: 3D + отверстия + листовой металл |
| `demo_3d_part.py` | 3D деталь: выдавливание, отверстия, фаски |
| `bearing_bracket.py` | Корпус подшипника |
| `flange_coupling.py` | Фланцевая муфта |
| `chair.py` | Конструкция стула |
| `apartment_plan.py` | План квартиры: стены, окна, двери, мебель |
| `plow_30hp.py` | Плуг для трактора 30 л.с. |
| `create_lighthouse.py` | 3D маяк: архитектурная модель |

## 9. Решение проблем

| Проблема | Решение |
|----------|---------|
| `connection refused` на :5080 | nanoCAD не запущен или плагин не загружен |
| `Class X is not supported` | Функция требует Plus/Pro лицензию |
| `Hatch pattern failed: eNoDatabase` | nanoCAD Free не содержит `acad.pat`. Используйте `SOLID` |
| Плагин не загружается в nCad.ini | Проверьте путь до DLL, перезапустите nanoCAD |
| `Import "mcp" could not be resolved` | Выполните `pip install -e .` в папке `server` |
| Сервер висит при create_note_comb | Этот блокирующий вызов не работает через HTTP API |

---

**Полная документация:** [README.md](README.md)
