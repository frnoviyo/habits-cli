# Constitución — habits-cli

Principios innegociables. Cualquier excepción requiere modificar antes este documento.

1. **Stack mínimo**: Python 3.12+ y solo biblioteca estándar; pytest es la única dependencia, y solo para tests.
2. **Spec primero**: ningún cambio de comportamiento se implementa sin una spec aprobada en `specs/`; si código y spec discrepan, manda la spec.
3. **Núcleo puro**: `habits/core.py` no hace I/O (ni `print`, ni `input`, ni archivos, ni reloj del sistema); la CLI y el almacenamiento lo invocan, nunca al revés.
4. **Tests obligatorios**: toda función pública de `core.py` tiene tests; `pytest -q` debe pasar antes de dar por terminada cualquier tarea.
5. **Persistencia JSON local**: los datos viven en un único archivo JSON gestionado solo por `habits/storage.py`; su formato no cambia sin actualizar antes la spec.
6. **Idioma**: identificadores, nombres de archivo y comentarios en inglés; todo mensaje visible al usuario, en español.
