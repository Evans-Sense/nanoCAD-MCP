# Унифицированный формат описания CAD-модели (CAD-Spec YAML)
# Версия: 2.0 (с актуальными данными по ГОСТ, ISO, AGMA, ASME)
# База знаний: .opencode/knowledge/*.md

## Справочные источники по разделам
# materials.md    — стали, чугуны, цветные сплавы, термообработка, полимеры
# mechanics.md    — сопромат, усталость, сварка, резьба, шпонки, пружины, подшипники
# tolerances.md   — ЕСДП (ГОСТ 25346/25347-2013), квалитеты, посадки, шероховатость
# engineering-standards.md — ЕСКД, крепёж, модули, элементы, шпонки, СИ
# kinematics.md   — кинематика, зубчатые/червячные/планетарные/цепные/ремённые передачи

## Секции файла *.cad-spec.yaml:

# ─── 1. МЕТАДАННЫЕ ───────────────────────────────────────────────
project:
  name: "Наименование изделия/проекта"
  description: "Краткое описание"
  author: "ФИО разработчика"
  date: "ГГГГ-ММ-ДД"
  revision: "A"
  standard: "ГОСТ | ISO | DIN | ANSI"      # Основной стандарт оформления
  application: "nanoCAD | AutoCAD | SolidWorks | Компас-3D | Inventor | Solid Edge"
  units: "mm | cm | m | inch"               # Единицы измерения
  coordinate_system: "WCS | UCS"            # Система координат
  drawing_format: "A0 | A1 | A2 | A3 | A4"  # Формат листа (ГОСТ 2.301-68)
  drawing_scale: "1:1 | 1:2 | 2:1 | ..."    # Масштаб (ГОСТ 2.302-68)
  drawing_number: "АБВГ.123456.001"         # Обозначение по ЕСКД
  department: "ОГК | ОГТ | ОГМ"
  notes:
    - "Примечание 1"
    - "Примечание 2"

# ─── 2. СЛОИ (LAYERS) ────────────────────────────────────────────
layers:
  - name: "0"                            # Имя слоя
    color: "white | red | yellow | green | cyan | blue | magenta | ..."  # Цвет или номер (1-255)
    linetype: "Continuous | Dashed | Hidden | Center | DashDot | Phantom | Border | ..."
    lineweight: "0.0 | 0.05 | 0.09 | 0.13 | 0.18 | 0.25 | 0.35 | 0.50 | 0.70 | 1.00 | 1.40 | 2.00"  # мм
    plot: true                           # Печатать слой
    frozen: false                        # Заморозить
    locked: false                        # Заблокировать
    description: "Назначение слоя"        # Описание
    transparency: 0                      # Прозрачность (0-90)
    lineweight_mm: 0.25                  # Толщина линии в мм (по ГОСТ 2.303-68: S=0.5-1.4 мм)

# ─── 3. ГЕОМЕТРИЧЕСКИЕ ПРИМИТИВЫ (ENTITIES) ────────────────────
entities:
  # 3.1. ТОЧКА (POINT)
  - type: point
    layer: "0"
    position: [x, y, z]                  # Координаты точки
    point_size: 5                         # Размер точки в %
    point_type: 0                         # Тип точки (0-4: точка, крест, круг и т.д.)

  # 3.2. ЛИНИЯ (LINE)
  - type: line
    layer: "0"
    start: [x1, y1, z1]                  # Начальная точка
    end: [x2, y2, z2]                    # Конечная точка
    length: 100.0                         # Длина (авторасчёт или заданная)
    angle: 45.0                           # Угол наклона к оси X (градусы)
    properties:
      color: "ByLayer" | "Red" | "1" | etc
      linetype: "ByLayer" | "Continuous" | "Hidden" | etc
      lineweight: "ByLayer" | "0.25"

  # 3.3. КРУГ (CIRCLE)
  - type: circle
    layer: "0"
    center: [cx, cy, cz]                  # Центр
    radius: 25.0                           # Радиус
    diameter: 50.0                         # Альтернатива: диаметр

  # 3.4. ДУГА (ARC)
  - type: arc
    layer: "0"
    center: [cx, cy, cz]                  # Центр
    radius: 50.0                           # Радиус
    start_angle: 0.0                       # Начальный угол (градусы)
    end_angle: 180.0                       # Конечный угол (градусы)
    start: [x1, y1]                        # Альтернатива: начальная точка
    end: [x2, y2]                          # Альтернатива: конечная точка
    chord_length: 100.0                    # Длина хорды
    arc_length: 157.08                     # Длина дуги
    clockwise: false                       # По часовой стрелке

  # 3.5. ПОЛИЛИНИЯ (POLYLINE / LWPOLYLINE)
  - type: polyline
    layer: "0"
    closed: true                           # Замкнутая
    linetype_generation: true              # Генерация типа линии по всем вершинам
    vertices:                              # Вершины
      - [x1, y1]
      - [x2, y2]
      - [x3, y3]
    widths:                                # Ширины в начале/конце сегмента
      - [0.0, 0.0]                        # [start_width, end_width]
      - [0.0, 0.0]
    bulges: [0.0, 0.5, 0.0]               # Выпуклость (0=прямая, 1=полуокружность)
    elevation: 0.0                         # Высота над плоскостью XY
    thickness: 0.0                         # Толщина выдавливания (3D)

  # 3.6. ПРЯМОУГОЛЬНИК (RECTANGLE)
  - type: rectangle
    layer: "0"
    corner1: [x1, y1]                      # Первый угол
    corner2: [x2, y2]                      # Второй угол (противоположный)
    width: 100.0                           # Альтернатива: ширина
    height: 50.0                           # Альтернатива: высота
    center: [cx, cy]                       # Альтернатива: центрирование
    rotation: 0.0                          # Поворот (градусы)
    chamfer: [0.0, 0.0]                    # Фаски [d1, d2] (ГОСТ 2.307)
    fillet: 0.0                            # Скругление углов
    elevation: 0.0
    area: 5000.0                           # Площадь (авторасчёт)

  # 3.7. ЭЛЛИПС (ELLIPSE)
  - type: ellipse
    layer: "0"
    center: [cx, cy, cz]                   # Центр
    major_axis_end: [dx, dy, dz]           # Конечная точка большой оси (от центра)
    major_radius: 50.0                     # Большая полуось
    minor_ratio: 0.5                       # Отношение малой оси к большой (0-1)
    start_param: 0.0                       # Начальный параметр
    end_param: 6.2832                      # Конечный параметр (2π = полный эллипс)

  # 3.8. СПЛАЙН (SPLINE)
  - type: spline
    layer: "0"
    degree: 3                              # Степень (обычно 3 — кубический)
    closed: false                          # Замкнутый
    periodic: false                        # Периодический (замкнутый гладкий)
    fit_points:                            # Точки аппроксимации
      - [x1, y1, z1]
      - [x2, y2, z2]
    control_points:                        # Управляющие точки (альтернатива)
      - [x1, y1, z1]
    knots: [0, 0, 0, 0.5, 1, 1, 1]        # Узловые векторы (для NURBS)
    weights: [1.0, 1.0, 1.0]              # Веса (для NURBS)
    tolerance: 0.001                       # Допуск аппроксимации

  # 3.9. ТЕКСТ (TEXT / DTEXT)
  - type: text
    layer: "0"
    content: "Текст надписи"
    position: [x, y, z]                    # Точка вставки
    height: 2.5                            # Высота текста (мм) — по ГОСТ 2.304-81
    rotation: 0.0                          # Угол поворота (градусы)
    style: "STANDARD"                      # Стиль текста
    font: "ISOCPEUR | GOST type A | GOST type B | Arial | ..."
    alignment: "left | center | right | top | middle | bottom"
    width_factor: 1.0                      # Коэффициент ширины
    oblique_angle: 0.0                     # Наклон (градусы, 15° по ГОСТ)
    text_style_type: "A | Б"               # Тип шрифта по ГОСТ 2.304-81
    text_size_mm: 3.5                      # Стандартный размер: 2.5; 3.5; 5; 7; 10; 14; 20

  # 3.10. МНОГОСТРОЧНЫЙ ТЕКСТ (MTEXT)
  - type: mtext
    layer: "0"
    content: |
      Первая строка
      Вторая строка
    position: [x, y, z]                    # Угол рамки
    width: 200.0                           # Ширина рамки
    height: 20.0                           # Высота рамки
    style: "STANDARD"
    alignment: "TL | TC | TR | ML | MC | MR | BL | BC | BR"
    line_spacing: 1.0                      # Межстрочный интервал (1.0 = одинарный)
    line_spacing_style: "exactly | proportional"
    rotation: 0.0
    background_color: "none | 255,255,255" # Цвет фона

  # 3.11. ВЫНОСКА (LEADER / QLEADER / MLEADER)
  - type: leader
    layer: "0"
    text: "Текст выноски"
    points:                                # Точки выноски
      - [x1, y1]                          # Начало стрелки
      - [x2, y2]                          # Точка излома
      - [x3, y3]                          # Полка
    arrow_size: 3.0                        # Размер стрелки
    arrow_type: "closed_filled | open | dot | ..."
    text_position: "after | before | over | ..."

  # 3.12. ШТРИХОВКА (HATCH)
  - type: hatch
    layer: "0"
    pattern: "ANSI31 | SOLID | CROSS | LINE | ANGLE | NET | ZIGZAG | ..."
    scale: 1.0                             # Масштаб штриховки
    angle: 0.0                             # Угол поворота (градусы)
    color: "ByLayer"
    background_color: "none | 255,255,255"
    boundaries:                            # Обход контуров
      - type: polyline                    # Тип контура
        vertices: [...]                   # Вершины
      - type: circle
        center: [cx, cy]
        radius: 10.0
    hatching_style: "normal | outer | ignore"  # Стиль штриховки
    associative: true                      # Ассоциативная

# ─── 4. РАЗМЕРЫ (DIMENSIONS) ─────────────────────────────────────
dimensions:
  - type: "aligned | horizontal | vertical | radial | diametric | angular | ordinate | arc"
    layer: "Dim"
    style: "STANDARD"                      # Размерный стиль
    definition_points:
      - [x1, y1, z1]                      # Точка 1 (начало замера)
      - [x2, y2, z2]                      # Точка 2 (конец замера)
      - [x3, y3, z3]                      # Положение размерной линии
    text: "100±0.1"                       # Текст (если не автоматический)
    text_height: 2.5                      # Высота размерного текста
    precision: 2                           # Количество десятичных знаков
    tolerance:
      type: "symmetrical | deviation | limits | none"
      upper: 0.1                          # Верхнее отклонение
      lower: 0.0                          # Нижнее отклонение
    units: "mm"
    arrow_size: 3.0
    extension_line_offset: 1.5
    text_above_dim_line: false

  - type: radial
    center: [cx, cy]
    radius: 25.0
    text: "R25"
    position: [px, py]

  - type: angular
    vertex: [vx, vy]                      # Вершина угла
    point1: [x1, y1]                      # Первая точка
    point2: [x2, y2]                      # Вторая точка
    text: "45°"

# ─── 5. ДОПУСКИ И ПОСАДКИ (TOLERANCES & FITS) ──────────────────
# Справочник: tolerances.md
tolerances:
  - applies_to: "Вал_1"
    fit: "H7/g6 | H7/k6 | H7/p6 | H8/f7 | ..."  # Посадка по ЕСДП
    system: "hole_basis | shaft_basis"           # Система отверстия/вала
    nominal: 50.0                                 # Номинальный размер, мм
    tolerance_grade: "IT6 | IT7 | IT8 | ..."     # Квалитет
    surface_roughness: 1.6                        # Ra, мкм (ГОСТ 2789-73)
    roughness_class: 7                            # Класс шероховатости (1-14)
    form_tolerance:
      type: "cylindricity | roundness | straightness | flatness | parallelism | perpendicularity | coaxiality"
      value: 0.01                                 # мм
      datum: "A"
    notes: "Шлифовать | Полировать | Хонинговать"

# ─── 6. БЛОКИ (BLOCKS) ───────────────────────────────────────────
blocks:
  - name: "Болт_M10x60"                   # Имя блока
    description: "Болт с шестигранной головкой М10×60 ГОСТ 7798-70"
    insert_point: [0, 0, 0]                # Базовая точка вставки
    scale: [1.0, 1.0, 1.0]                # Масштаб по умолчанию
    scale_uniform: true                    # Равномерный масштаб
    rotation: 0.0                          # Поворот по умолчанию
    layers: ["0", "Bolts"]
    entities:                              # Вложенные примитивы
      - type: circle
        center: [0, 0]
        radius: 8.0
      - type: circle
        center: [0, 0]
        radius: 5.0
    attributes:                            # Атрибуты
      - tag: "POS"
        value: "1"
        position: [0, 0]
        height: 2.5
        invisible: false

  - type: insert                           # Вставка существующего блока
    name: "Болт_M10x60"
    layer: "Bolts"
    position: [100.0, 50.0, 0.0]          # Точка вставки
    scale: [1.0, 1.0, 1.0]               # Масштаб
    rotation: 0.0                          # Поворот
    row_count: 4                           # Массив (ARRAY)
    column_count: 1
    row_spacing: 50.0
    column_spacing: 0.0
    attributes:
      - tag: "POS"
        value: "1"

# ─── 7. МАТЕРИАЛЫ (MATERIALS) ────────────────────────────────────
# Справочник: materials.md
materials:
  - name: "Сталь 45 ГОСТ 1050-2013"
    type: "steel | cast_iron | aluminum | copper | titanium | plastic | composite | rubber"
    density: 7850                          # кг/м³
    young_modulus: 210                     # ГПа (E)
    shear_modulus: 80                      # ГПа (G)
    poisson_ratio: 0.3                     # μ
    yield_strength: 355                    # σ_т, МПа
    ultimate_strength: 600                 # σ_в, МПа
    fatigue_limit: 270                     # σ_₋₁, МПа (предел выносливости)
    endurance_limit_reversed: 270          # σ_₋₁, МПа (симметричный цикл)
    hardness: "HB 200 | HRC 32-40 | HV 240"
    elongation: 16                         # δ, % (относительное удлинение)
    reduction_in_area: 40                  # ψ, %
    impact_strength: 49                    # KCU, Дж/см² (ударная вязкость)
    heat_treatment:
      type: "улучшение | закалка | цементация | азотирование | нормализация | отжиг"
      hardness_after: "HB 240-280"
      case_depth: 1.0                      # Глубина слоя (мм)
    corrosion_resistance: "низкая | средняя | высокая"
    standard: "ГОСТ 1050-2013"
    notes: "Рекомендуется для валов и шестерён. Улучшение HB 240-280"
    thermal_conductivity: 47               # Вт/(м·K)
    thermal_expansion: 11.2                # α·10⁻⁶, 1/°C

# ─── 8. ПРОЧНОСТНЫЕ ХАРАКТЕРИСТИКИ (STRUCTURAL) ──────────────────
# Справочник: mechanics.md
structural:
  - element: "Вал_редуктора"
    material: "Сталь 40Х ГОСТ 4543-2016"
    geometry:                               # Геометрия элемента
      type: "solid_cylinder | hollow_cylinder | rectangular"
      diameter: 40.0                        # мм
      length: 300.0                         # мм
    loads:
      - type: "force | moment | torque | pressure | distributed | thermal"
        value: 1000                         # Н или Н·м
        direction: [0, 0, -1]              # Вектор направления
        point: [x, y, z]                  # Точка приложения
        cyclic: true                       # Циклическая нагрузка (для усталости)
    supports:                               # Опоры
      - type: "fixed | pinned | roller | bearing"
        location: [x, y, z]
        bearing_type: "ball | roller | plain"
    safety_factor: 2.0                     # Коэф. запаса (по пределу текучести)
    fatigue_analysis:                       # Расчёт на усталость (ASME B106.1M)
      method: "Soderberg | Goodman | Gerber | ASME_elliptic"
      surface_finish: "ground | machined | hot_rolled | as_forged"
      reliability: 0.95                    # Надёжность (50-99.99%)
      notch_type: "keyway | groove | shoulder | hole | thread"
      required_life: 10000                 # часов
    critical_speed: 3000                   # об/мин
    max_deflection: 0.05                   # мм (допустимый прогиб)
    natural_frequency: 50                  # Гц
    notes: "Расчёт по 4-й теории прочности (von Mises)"
    references: "Shigley ch.7, ASME B106.1M"

# ─── 9. КИНЕМАТИКА (KINEMATICS) ──────────────────────────────────
# Справочник: kinematics.md
kinematics:
  - type: "revolute_joint | prismatic_joint | cylindrical_joint | spherical_joint | planar_joint | cam"
    name: "Шарнир_1"
    link1: "Кривошип"
    link2: "Шатун"
    origin: [x, y, z]
    axis: [0, 0, 1]
    range:
      min: 0
      max: 360
    input: true                            # Ведущее звено
    actuator:
      type: "motor | hydraulic | pneumatic | manual"
      speed: 1500                           # об/мин
      torque: 10                            # Н·м
      power: 1.5                            # кВт

  - type: "gear_pair"
    name: "Цилиндрическая_передача_1"
    type: "spur | helical | bevel | worm | planetary"
    # Стандарты: ISO 6336-2:2019, ISO 6336-3:2019, ГОСТ 21354-87
    gear1:
      teeth: 20                            # Число зубьев (z₁ ≥ 17 прямозубые, z₁ ≥ 14 косозубые)
      module: 2                             # Модуль, мм (ГОСТ 9563-60: 1; 1.25; 1.5; 2; 2.5; 3; 4; 5; 6; 8; 10...)
      profile_angle: 20                      # Угол профиля, градусы
      material: "Сталь 40Х ГОСТ 4543-2016"
      heat_treatment: "цементация | улучшение | закалка ТВЧ"
      hardness: "HRC 56-62 | HB 280-320"
      shift_coefficient: 0.0               # Коэф. смещения x (для коррегирования)
      face_width: 40                         # Ширина венца, мм
      precision_grade: 7                     # Степень точности (6-9 по ГОСТ 1643-81)
    gear2:
      teeth: 80
      module: 2
      profile_angle: 20
      material: "Сталь 45 ГОСТ 1050-2013"
      heat_treatment: "улучшение"
      hardness: "HB 240-280"
      shift_coefficient: 0.0
      face_width: 36
    center_distance: 100                    # Межосевое расстояние a_w, мм
    helix_angle: 15                          # Угол наклона зуба β, градусы
    ratio: 4                                # Передаточное отношение i = z₂/z₁
    efficiency: 0.97                        # КПД (0.96-0.98 для 1 ступени)
    lubrication: "oil_bath | spray | grease"
    oil_type: "ISO VG 150 | ISO VG 220 | ..."
    calculation_method: "ISO 6336 | GOST 21354-87"
    allowable_contact_stress: 600            # σ_HP, МПа (допуск. контактное)
    allowable_bending_stress: 250            # σ_FP, МПа (допуск. изгибное)

# ─── 10. СБОРКИ И СОЕДИНЕНИЯ (ASSEMBLY & JOINTS) ────────────────
assembly:
  - part: "Корпус_редуктора"
    file: "корпус.dwg"
    position: [0, 0, 0]
    rotation: [0, 0, 0]
    constraints:                           # Сборочные зависимости
      - type: "coincident | concentric | parallel | perpendicular | tangent | distance | angle"
        entity1: ["face", "part1", "id1"]
        entity2: ["face", "part2", "id2"]
        value: 0.0

  - connection:
    name: "Сварное_соединение_1"
    parts: ["Корпус", "Крышка"]
    type: "weld | bolt | rivet | glue | press_fit | key | spline | pin"
    specification:
      weld_type: "fillet | butt | lap | corner | plug"
      weld_throat: 6                          # Катет шва k, мм
      weld_length: 50                         # Длина шва, мм
      electrode: "Э42 | Э46 | Э50"           # Тип электрода
      bolt: "M10×60"                         # Стандарт: ГОСТ 7798-70, ISO 4014
      bolt_grade: "8.8 | 10.9 | 12.9"        # Класс прочности (ГОСТ Р 52627-2006)
      preload_torque: 30                      # Момент затяжки, Н·м
      fit_type: "H7/g6 | H7/k6"             # Посадка (по tolerances.md)
      key_type: "prismatic | woodruff | feather"
      key_dimensions: "8×7×40"               # b×h×l (ГОСТ 23360-78)
      key_fit: "P9 | N9 | Js9"

# ─── 11. СТАНДАРТНЫЕ ИЗДЕЛИЯ (STANDARD PARTS) ───────────────────
# Справочник: engineering-standards.md
standard_parts:
  - type: "bearing"
    name: "Подшипник 6205"
    standard: "ГОСТ 8338-75 | ISO 104"
    bore: 25                                 # d, мм (внутренний диаметр)
    outer: 52                                # D, мм (наружный диаметр)
    width: 15                                # B, мм (ширина)
    dynamic_load: 14.0                       # C, кН (ГОСТ 8338-75)
    static_load: 7.0                         # C₀, кН
    speed_limit_grease: 9000                  # об/мин (предельная со смазкой)
    speed_limit_oil: 11000                    # об/мин (предельная с маслом)
    clearance: "CN | C2 | C3 | C4"          # Группа зазора
    fit_shaft: "k6"                          # Посадка на вал (по tolerances.md)
    fit_housing: "H7"                        # Посадка в корпус
    cage: "steel | brass | polyamide"
    sealing: "open | ZZ (2 shields) | 2RS (2 seals)"

  - type: "bolt | screw | nut | washer | pin | ring"
    designation: "Болт M10×60.58 ГОСТ 7798-70"  # Полное обозначение
    count: 8                                  # Количество
    positions:
      - [x1, y1, z1]
      - [x2, y2, z2]

# ─── 12. ТЕХНОЛОГИЧЕСКИЕ УКАЗАНИЯ (MANUFACTURING NOTES) ─────────
manufacturing:
  - process: "turning | milling | drilling | grinding | welding | casting | forging | 3d_printing | EDM"
    notes: "Шероховатость Ra 1.6 на посадочных поверхностях"
    tolerances: "IT7"                       # Требуемая точность
    surface_treatment:
      - "Полировка"
      - "Хромирование | Никелирование | Цинкование"
    heat_treatment: "Закалка ТВЧ h 1.5 мм"
    coating: "Покраска RAL 7035 | Анодирование | Фосфатирование"
    marking: "АБВГ.123456.001"
    packaging: "Индивидуальная упаковка"
    inspection: "100% | выборочный 10% | визуальный"
    ndt: "ультразвук | магнитопорошок | цветная дефектоскопия | радиография"

# ─── 13. ЭКСПОРТ (EXPORT SETTINGS) ───────────────────────────────
export:
  - format: "dwg | dxf | pdf | stl | stp | iges | step | sat | obj | gltf"
    path: "output/model.pdf"
    options:
      pdf_paper: "A2"                       # Формат листа (ГОСТ 2.301-68)
      pdf_scale: "1:1"                      # Масштаб печати
      monochrome: true                      # Монохромная печать
      explode_blocks: false                 # Расчленить блоки
      include_xrefs: true
      dwg_version: "AC1032"                 # AutoCAD 2018

# ─── 14. МЕТАДАННЫЕ (EXTENDED DATA) ─────────────────────────────
xdata:
  - app_name: "ENGINEERING_DATA"
    data:
      weight: 2.5                           # кг
      material_code: "1050-88"
      drawing_number: "АБВГ.123456.001"
      department: "ОГК | ОГТ | ОГМ"
      designer: "Иванов И.И."
      checker: "Петров П.П."
      norm_controller: "Сидоров А.А."
      approval: "Директор"
      document_type: "original | revision | copy"
      revision_history:
        - rev: "A"
          date: "2024-01-15"
          description: "Первоначальный выпуск"
          author: "Иванов И.И."
        - rev: "B"
          date: "2024-03-20"
          description: "Изменение посадочного диаметра"
          author: "Иванов И.И."
