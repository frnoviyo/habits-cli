# Tareas 001 — MVP de habits-cli

Spec: `spec.md` · Plan: `plan.md` · Estado: completada · Fecha: 2026-10-14 · Revisión 2026-10-15: Fase 5 (spec RF-5)

Reglas:
- Orden de dependencia: no empieces una tarea hasta que estén hechas las anteriores de la que depende (columna «Depende de»).
- Cada tarea cabe en 20–30 minutos. Si crece, divídela antes de seguir.
- Al cerrar cada tarea: `pytest -q` pasa (desde T02).
- Tests primero: en cada pareja «tests → implementación», los tests deben fallar antes de implementar.

## Fase 0 — Preparación

- [x] **T00 — Cerrar las dudas abiertas de la spec**
  Aprobar (o cambiar) DP1–DP4 del plan y trasladarlas a `spec.md` §9 como decisiones, con sus criterios EARS.
  Depende de: — · Cubre: RF-1.4, RF-3.1, RF-4.3, RNF-3
  Hecho cuando: `spec.md` no contiene ningún «[NECESITA ACLARACIÓN]» sin decisión o aplazamiento explícito.

- [x] **T01 — Entorno de desarrollo**
  Instalar Python 3.12+ y pytest; comprobar versiones.
  Depende de: — · Cubre: —
  Hecho cuando: `python --version` muestra 3.12 o superior y `python -m pytest --version` responde.

- [x] **T02 — Esqueleto del proyecto**
  Crear `pyproject.toml` (solo `pythonpath = ["."]`), `habits/__init__.py`, `habits/core.py`, `habits/storage.py`, `habits/cli.py` vacíos y `tests/` con un test trivial.
  Depende de: T01 · Cubre: —
  Hecho cuando: `pytest -q` se ejecuta desde la raíz y pasa 1 test.

## Fase 1 — Núcleo (`core.py`)

- [x] **T03 — Modelo y normalización**
  Tests y código de `Habit`, la jerarquía `HabitError` y `normalize_name`.
  Depende de: T02 · Cubre: RF-2.2 · CL-1, CL-3, CL-13
  Hecho cuando: hay tests que demuestran que `normalize_name(" Leer ") == normalize_name("LEER")` y que conserva tildes, y pasan.

- [x] **T04 — Crear hábitos**
  Tests y código de `find_habit` y `add_habit` (alta, duplicado, nombre vacío, nombre guardado sin espacios en los extremos).
  Depende de: T03 · Cubre: RF-1.1, RF-1.2, RF-1.3, RF-1.4, RF-2.2 · CL-1, CL-2
  Hecho cuando: los 4 casos de RF-1 tienen test propio que pasa y un duplicado o vacío no altera la lista.

- [x] **T05 — Marcar como hecho**
  Tests y código de `mark_done` e `is_done_on` (primera marca, marca repetida devuelve `False` sin cambios, hábito inexistente lanza `HabitNotFoundError`).
  Depende de: T04 · Cubre: RF-2.1, RF-2.3, RF-2.4, RF-2.5 · CL-3, CL-4, CL-5
  Hecho cuando: los tests de los 3 casos pasan y `mark_done` solo acepta la fecha recibida como `today`.

- [x] **T06 — Cálculo de racha**
  Test parametrizado de `current_streak` con una tabla de casos y código según el pseudocódigo del plan §3.
  Depende de: T05 · Cubre: RF-3.2 · CL-6, CL-7, CL-8, CL-9, CL-10, CL-11
  Hecho cuando: la tabla incluye al menos un caso por CL-6…CL-11 más «fecha futura ignorada» y todos pasan.

- [x] **T07 — Verificar la pureza del núcleo**
  Revisar `core.py` contra el Principio 3.
  Depende de: T06 · Cubre: RNF-4
  Hecho cuando: buscar `print|input|open|today()|now()|import os|import json` en `core.py` no devuelve resultados y toda función pública tiene type hints y test.

## Fase 2 — Persistencia (`storage.py`)

- [x] **T08 — Ruta de datos**
  Tests y código de `default_path()` (con y sin `HABITS_FILE`, usando `monkeypatch`).
  Depende de: T02 · Cubre: RF-4.1
  Hecho cuando: los dos tests pasan sin tocar el `~/.habits.json` real.

- [x] **T09 — Cargar datos**
  Tests y código de `load_habits`: archivo inexistente → `[]`; JSON válido → lista en orden; JSON corrupto o con esquema incorrecto → `StorageError`.
  Depende de: T04, T08 · Cubre: RF-4.1, RF-4.5 · RNF-3
  Hecho cuando: los 3 casos tienen test con `tmp_path` y pasan; el archivo corrupto queda byte a byte igual.

- [x] **T10 — Guardar datos de forma atómica**
  Tests y código de `save_habits`: formato del plan §2, UTF-8 sin escapar, fechas ordenadas, temporal + `os.replace`.
  Depende de: T09 · Cubre: RF-4.1 · RNF-3 · CL-13
  Hecho cuando: guardar y volver a cargar devuelve los mismos hábitos (orden y tildes), el JSON coincide con el ejemplo del plan y no queda ningún archivo temporal.

## Fase 3 — Interfaz (`cli.py`)

- [x] **T11 — Parser en español**
  Subclase de `argparse` con los subcomandos `crear <nombre>`, `hecho <nombre>`, `listar`; texto de uso y errores en español; `main()` devuelve 2 en uso incorrecto.
  Depende de: T02 · Cubre: RF-4.2, RF-4.3, RF-4.4
  Hecho cuando: hay tests de comando inexistente, sin comando y `crear` sin nombre que comprueban código 2 y que stderr no contiene «usage» ni «error: argument».

- [x] **T12 — Comando `crear`**
  Conectar parser → `load_habits` → `add_habit` → `save_habits`; mensajes del contrato (plan §4).
  Depende de: T04, T10, T11 · Cubre: RF-1.1, RF-1.2, RF-1.3, RF-1.4, RF-4.3, RF-4.5
  Hecho cuando: los tests con `main([...], today=..., data_path=tmp)` comprueban el mensaje exacto y el código (0/1) de alta, duplicado y vacío, y el archivo no cambia en los errores.

- [x] **T13 — Comando `hecho`**
  Conectar `mark_done` y `current_streak`; mensajes de marca nueva, ya marcado e inexistente; guardar solo si hubo cambios.
  Depende de: T05, T06, T12 · Cubre: RF-2.1, RF-2.2, RF-2.3, RF-2.4, RF-2.5, RF-4.3 · CL-3, CL-4, CL-5
  Hecho cuando: los tests comprueban los 3 mensajes del contrato con sus códigos (0, 0, 1) y que la marca repetida no reescribe el archivo.

- [x] **T14 — Comando `listar`**
  Formato `[x]`/`[ ]`, columnas alineadas, «1 día»/«N días», orden de creación y mensaje de lista vacía.
  Depende de: T06, T12 · Cubre: RF-3.1, RF-3.2, RF-3.3 · CL-6, CL-9, CL-12, CL-13
  Hecho cuando: un test compara la salida completa con el ejemplo del plan §4 y otro comprueba «No hay hábitos todavía.» con código 0.

- [x] **T15 — Datos ilegibles en la CLI**
  Traducir `StorageError` al mensaje del contrato con código 1 en los tres comandos.
  Depende de: T09, T12 · Cubre: RF-4.3 · RNF-3, RNF-5
  Hecho cuando: un test con JSON corrupto comprueba el mensaje, el código 1 y que el archivo no cambia.

- [x] **T16 — Punto de entrada `python -m habits`**
  Crear `habits/__main__.py` y un test smoke con `subprocess` y `HABITS_FILE` en `tmp_path`.
  Depende de: T14 · Cubre: RF-4.1, RF-4.5
  Hecho cuando: el test ejecuta `crear` → `hecho` → `listar` en procesos separados y la última salida muestra la racha 1.

## Fase 4 — Cierre

- [x] **T17 — Trazabilidad y finalización**
  Comprobar que cada RF y cada CL tiene al menos un test que lo nombra; repasar la constitución; probar a mano los tres comandos.
  Depende de: T07, T13, T14, T15, T16 · Cubre: todos (spec §8)
  Hecho cuando: `pytest -q` pasa, una búsqueda de cada `rf_x_y`/`cl_n` en `tests/` encuentra al menos un resultado para todos los de la spec y se marcan todos los criterios de la spec §8.

## Fase 5 — Marcar ayer (spec RF-5, plan D10/D11)

- [x] **T18 — Núcleo: marcar ayer**
  Tests y código de `mark_done(..., yesterday=True)`: marca `today − 1 día`, repetido devuelve `False` sin cambios, inexistente lanza `HabitNotFoundError`, no toca `today`, funciona con un hábito sin días (creado hoy) y en cambio de año o bisiesto.
  Depende de: T05 · Cubre: RF-2.5, RF-5.1, RF-5.2, RF-5.3, RF-5.4, RF-5.6 · CL-14, CL-19, CL-20, CL-21, CL-22
  Hecho cuando: cada caso tiene un test que pasa, los tests de T05 siguen pasando sin cambios y `mark_done` no acepta ninguna fecha que no sea `today` o `today − 1 día`.

- [x] **T19 — Racha tras marcar ayer**
  Test parametrizado «estado inicial → `mark_done(..., yesterday=True)` → `current_streak`» con los casos de la spec. No se espera código nuevo (plan §3); si algún caso falla, corregir el núcleo.
  Depende de: T06, T18 · Cubre: RF-5.5 · CL-15, CL-16, CL-17, CL-18
  Hecho cuando: la tabla incluye un caso por CL-15…CL-18 con la racha exacta de la spec (1, 2, 4 y 3) y todos pasan.

- [x] **T20 — Parser: opción `--ayer`**
  Añadir `--ayer` solo al subcomando `hecho` (antes o después del nombre), `allow_abbrev=False` y la línea nueva en el texto de uso.
  Depende de: T11 · Cubre: RF-4.2, RF-4.4
  Hecho cuando: hay tests que comprueban que `--ayer` en `crear` o `listar` devuelve 2, que `hecho --ayer` sin nombre muestra «Error: falta el nombre del hábito.» con código 2, que `--ay` no se acepta y que el uso muestra `hecho <nombre> --ayer`.

- [x] **T21 — Comando `hecho --ayer`**
  Conectar `--ayer` con `mark_done(..., yesterday=True)`; mensajes de marca nueva y ya marcado ayer del contrato (plan §4); guardar solo si hubo cambios.
  Depende de: T13, T18, T20 · Cubre: RF-5.1, RF-5.2, RF-5.3, RF-5.4, RF-4.3 · CL-14, CL-15, CL-20
  Hecho cuando: los tests comprueban los mensajes exactos y los códigos (0, 0, 1), que la marca repetida no reescribe el archivo, que el inexistente no lo modifica y que después `listar` sigue mostrando `[ ]` si hoy no estaba marcado.

- [x] **T22 — Extremo a extremo, documentación y cierre de RF-5**
  Test smoke con `subprocess` (`crear` → `hecho --ayer` → `listar`); actualizar el `README.md` con `--ayer`; repetir la comprobación de trazabilidad de T17 para RF-5 y CL-14…CL-22; probar a mano.
  Depende de: T19, T21 · Cubre: RF-5 completo (spec §8)
  Hecho cuando: `pytest -q` pasa, la búsqueda de cada `rf_5_y`/`cl_14`…`cl_22` en `tests/` encuentra al menos un resultado, se marcan de nuevo los criterios de la spec §8 y el estado de este archivo vuelve a «completada».

## Matriz RF → tareas

| RF | Tareas |
|---|---|
| RF-1.1–1.4 | T04, T12 |
| RF-2.1–2.5 | T05, T13 (RF-2.2 también T03; RF-2.5 también T18) |
| RF-3.1, RF-3.3 | T14 |
| RF-3.2 | T06, T14 |
| RF-4.1 | T08, T09, T10, T16 |
| RF-4.2, RF-4.4 | T11, T20 |
| RF-4.3 | T11, T12, T13, T15, T21 |
| RF-4.5 | T09, T12, T16 |
| RF-5.1–5.4 | T18, T21, T22 |
| RF-5.5 | T19 |
| RF-5.6 | T18 |
