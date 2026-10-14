# Plan 001 — MVP de habits-cli

Spec: `specs/001-habits-mvp/spec.md` · Constitución: `docs/constitution.md`
Estado: borrador · Fecha: 2026-10-14

## 1. Estructura de módulos

```
habits-cli/
├── pyproject.toml        # solo [tool.pytest.ini_options] pythonpath = ["."]; sin dependencias
├── habits/
│   ├── __init__.py
│   ├── __main__.py       # permite `python -m habits`; llama a cli.main()
│   ├── core.py           # lógica pura: modelo, normalización, marcar, racha
│   ├── storage.py        # único lector/escritor del JSON
│   └── cli.py            # argparse, fecha de hoy, mensajes en español, códigos de salida
└── tests/
    ├── test_core.py
    ├── test_storage.py
    └── test_cli.py
```

Dependencias permitidas: `cli → core`, `cli → storage`, `storage → core` (solo el
modelo `Habit`). `core` no importa nada del proyecto ni hace I/O (Principio 3).

### core.py (RF-1, RF-2, RF-3.2)

API pública, toda con type hints:

| Elemento | Responsabilidad | RF |
|---|---|---|
| `Habit` (dataclass: `name: str`, `done_dates: set[date]`) | Modelo | RF-1.1, RF-1.2 |
| `HabitError` → `EmptyNameError`, `DuplicateHabitError`, `HabitNotFoundError` | Errores de dominio (sin texto para el usuario) | RF-1.3, RF-1.4, RF-2.4 |
| `normalize_name(name) -> str` | `strip()` + `casefold()` | RF-2.2, CL-1, CL-3 |
| `find_habit(habits, name) -> Habit \| None` | Busca por nombre normalizado | RF-2.2 |
| `add_habit(habits, name) -> Habit` | Valida, guarda `name.strip()`, añade al final | RF-1.1–1.4 |
| `mark_done(habits, name, today) -> tuple[Habit, bool]` | Marca `today`; `False` si ya estaba | RF-2.1, RF-2.3–2.5 |
| `is_done_on(habit, day) -> bool` | ¿Marcado ese día? | RF-3.1 |
| `current_streak(habit, today) -> int` | Algoritmo de §3 | RF-3.2 |

`today` siempre es un parámetro: el núcleo nunca lee el reloj (P3, RNF-4).

### storage.py (RF-4.1, RF-4.5, RNF-3)

- `default_path() -> Path`: la variable de entorno `HABITS_FILE` si existe; si no, `~/.habits.json`.
- `load_habits(path) -> list[Habit]`: archivo inexistente → `[]` (RF-4.5); JSON
  inválido o con esquema incorrecto → `StorageError`.
- `save_habits(path, habits) -> None`: escritura atómica (archivo temporal en el
  mismo directorio + `os.replace`), UTF-8, `ensure_ascii=False`.

### cli.py (RF-4.2–4.4 y orquestación de todos los RF)

- `main(argv=None, *, today=None, data_path=None) -> int`. Los parámetros
  opcionales existen para los tests; en uso real valen `date.today()` y
  `default_path()`.
- Flujo: parsear → leer `today` **una vez** → `load_habits` → operación de `core`
  → `save_habits` **solo si hubo cambios** → imprimir → devolver código de salida.
- Traduce `HabitError` y `StorageError` a mensajes en español por stderr.

## 2. Modelo de datos JSON (RF-4.1)

```json
{
  "version": 1,
  "habits": [
    { "name": "Leer", "done_dates": ["2026-10-12", "2026-10-13", "2026-10-14"] },
    { "name": "Repasar inglés", "done_dates": [] }
  ]
}
```

- El orden de `habits` es el de creación (RF-3.1).
- `name` se guarda sin espacios en los extremos y con las mayúsculas originales
  (RF-1.2). El nombre normalizado no se guarda: se calcula al vuelo.
- `done_dates`: fechas ISO `AAAA-MM-DD`, sin repetir y ordenadas al guardar.
- `version` permite migrar el formato en el futuro; cualquier cambio exige
  actualizar antes la spec (P5).

## 3. Algoritmo de racha (RF-3.2, CL-6…CL-11)

```
función current_streak(habit, today):
    días ← habit.done_dates                       # conjunto de fechas
    si today ∈ días:                   cursor ← today
    si no, si (today − 1 día) ∈ días:  cursor ← today − 1 día
    si no:                             devolver 0     # CL-8, CL-9
    racha ← 0
    mientras cursor ∈ días:
        racha ← racha + 1
        cursor ← cursor − 1 día      # aritmética de fechas: fin de mes/año y bisiestos (CL-10, CL-11)
    devolver racha
```

Coste O(longitud de la racha) con búsqueda O(1) en el conjunto: cumple RNF-2.
Las fechas posteriores a `today` (reloj atrasado) se ignoran sin error.

## 4. Contrato de la CLI

Invocación: `python -m habits <comando> [nombre]`. Los nombres con espacios van
entre comillas.

| Comando | Ejemplo | Salida (stdout) | Código | RF |
|---|---|---|---|---|
| `crear <nombre>` | `crear "Leer"` | `Hábito «Leer» creado.` | 0 | RF-1.1, RF-1.2 |
| `hecho <nombre>` | `hecho leer` | `«Leer» marcado como hecho hoy. Racha actual: 3 días.` | 0 | RF-2.1, RF-2.2, RF-2.5 |
| `hecho <nombre>` (repetido) | `hecho leer` | `«Leer» ya estaba marcado hoy. Racha actual: 3 días.` | 0 | RF-2.3 |
| `listar` | `listar` | ver abajo | 0 | RF-3.1, RF-3.2 |
| `listar` (vacío) | `listar` | `No hay hábitos todavía.` | 0 | RF-3.3 |

Formato del listado (alineado por columnas, solo ASCII en el indicador):

```
[x] Leer            racha: 3 días
[ ] Repasar inglés  racha: 1 día
```

Singular y plural: «1 día», «N días».

Errores (stderr):

| Situación | Mensaje | Código | RF |
|---|---|---|---|
| Duplicado | `Error: ya existe un hábito llamado «Leer».` | 1 | RF-1.3 |
| Nombre vacío | `Error: el nombre del hábito no puede estar vacío.` | 1 | RF-1.4 |
| No existe | `Error: no existe el hábito «X». Usa «listar» para ver tus hábitos.` | 1 | RF-2.4, RNF-5 |
| Datos ilegibles | `Error: no se pudo leer el archivo de datos <ruta>. Revísalo o muévelo para empezar de cero.` | 1 | RNF-3, RNF-5 |
| Comando o argumento incorrecto | Texto de uso en español | 2 | RF-4.4 |

Convención de códigos (RF-4.3): 0 = éxito · 1 = error de dominio o de datos ·
2 = uso incorrecto.

## 5. Decisiones técnicas

| # | Decisión | Por qué | Alternativa descartada |
|---|---|---|---|
| D1 | `argparse` con una subclase que sobrescribe `error()` y el texto de uso para mostrarlos en español | Biblioteca estándar (P1); valida argumentos y es el estándar de facto | Parseo manual de `sys.argv`: menos código, pero reinventa validación y ayuda |
| D2 | Comandos en español (`crear`, `hecho`, `listar`) | Son interfaz visible para el usuario (P6, RF-4.2) | `add/done/list`: coherente con el código, pero mezcla idiomas ante el usuario |
| D3 | `today` como parámetro del núcleo; la CLI lo lee una sola vez | Núcleo puro y tests deterministas (P3, RNF-4) | Llamar a `date.today()` dentro de `core`: viola P3 |
| D4 | `done_dates` como lista de fechas ISO (conjunto en memoria) | Legible a mano, sin duplicados, racha recalculable | Guardar la racha como contador: se desincroniza y no se puede recalcular |
| D5 | Escritura atómica con archivo temporal + `os.replace` | Nunca deja el JSON a medias (RNF-3) | Escribir directamente sobre el archivo: corrupción si se interrumpe |
| D6 | Ruta `~/.habits.json`, sobrescribible con `HABITS_FILE` | Un único archivo por usuario (P5), independiente del directorio actual; tests aislados | Archivo en el directorio actual: los datos cambian según dónde se ejecute |
| D7 | Normalizar con `casefold()` | Comparación sin mayúsculas correcta en Unicode (CL-13) | `lower()`: falla en casos como «ß» |
| D8 | Mensajes de usuario solo en `cli.py`; `core` lanza excepciones tipadas | Separa lógica e interfaz (P3) | Mensajes dentro de las excepciones del núcleo |
| D9 | `pyproject.toml` solo con `pythonpath = ["."]` para pytest | `pytest -q` funciona desde la raíz sin instalar el paquete | `conftest.py` que manipula `sys.path`: más frágil |

### Decisiones sobre las dudas abiertas de la spec

Aprobadas e incorporadas a la spec §9 como D-1…D-4 (tarea T00):

- **DP1** (longitud del nombre): sin límite; solo se rechaza el nombre vacío. No
  se filtran saltos de línea ni tabuladores en el MVP.
- **DP2** (datos dañados): error con código 1 sin tocar el archivo (ver tabla de errores).
- **DP3** (medianoche): se usa la fecha leída una vez al inicio del comando (D3).
- **DP4** (indicador «hecho hoy»): `[x]` / `[ ]` en ASCII, válido en cualquier terminal.

## 6. Estrategia de tests

Principio 4: toda función pública de `core.py` tiene tests y `pytest -q` debe
pasar. Las fechas son siempre fijas (p. ej., `date(2026, 10, 14)`), nunca
`date.today()`.

| Archivo | Qué prueba | Cubre |
|---|---|---|
| `test_core.py` | `normalize_name`, `find_habit`, `add_habit` (ok, duplicado, vacío), `mark_done` (nuevo, repetido, inexistente), `is_done_on`; `current_streak` parametrizado con una tabla de casos | RF-1.1–1.4, RF-2.1–2.5, RF-3.2; CL-1–CL-11, CL-13 |
| `test_storage.py` | Con `tmp_path`: archivo inexistente → `[]`; guardar y cargar conserva orden y tildes; JSON corrupto → `StorageError` y archivo intacto; no quedan temporales | RF-4.1, RF-4.5, RNF-3, CL-13 |
| `test_cli.py` | `main([...], today=..., data_path=tmp)` con `capsys`: mensajes exactos, stdout/stderr y código de salida de cada fila del contrato; los errores no modifican el archivo; uso incorrecto → código 2 y texto en español; flujo completo crear → hecho → listar | RF-1…RF-4, CL-4, CL-5, CL-12 |
| `test_cli.py` (smoke) | Un `subprocess` de `python -m habits listar` con `HABITS_FILE` en `tmp_path` | Funcionamiento de extremo a extremo |

Trazabilidad: el nombre o el docstring de cada test indica el RF o CL que cubre
(p. ej., `test_add_habit_rejects_duplicate_rf_1_3`).

## 7. Cobertura de RF

| RF | Secciones del plan |
|---|---|
| RF-1.1–1.4 | §1 core, §2, §4, §6 |
| RF-2.1–2.5 | §1 core, §4, §6 |
| RF-3.1–3.3 | §1 core, §3, §4, §6 |
| RF-4.1, RF-4.5 | §1 storage, §2, §6 |
| RF-4.2–4.4 | §1 cli, §4, D1, D2, §6 |
