# habits-cli

CLI en Python para registrar hábitos de estudio y ver la **racha** de días
consecutivos de cada uno. Sin dependencias: solo la biblioteca estándar.

Proyecto construido con *Spec-Driven Development*: la spec, el plan y las
tareas están en [`specs/001-habits-mvp/`](specs/001-habits-mvp/) y los
principios del proyecto en [`docs/constitution.md`](docs/constitution.md).

## Requisitos

- Python 3.12 o superior
- `pytest`, solo para ejecutar los tests

## Uso

Desde la raíz del proyecto:

```console
$ python -m habits crear "Repasar inglés"
Hábito «Repasar inglés» creado.

$ python -m habits hecho "repasar inglés"
«Repasar inglés» marcado como hecho hoy. Racha actual: 1 día.

$ python -m habits listar
[x] Leer            racha: 3 días
[ ] Repasar inglés  racha: 1 día
```

| Comando | Qué hace |
|---|---|
| `crear <nombre>` | Crea un hábito. Los nombres con espacios van entre comillas. |
| `hecho <nombre>` | Marca el hábito como hecho **hoy** (solo se puede marcar el día actual). |
| `listar` | Muestra los hábitos en orden de creación, si están hechos hoy (`[x]`/`[ ]`) y su racha. |

- Los nombres no distinguen mayúsculas ni espacios en los extremos: `hecho LEER`
  marca «Leer», y no se puede crear «leer» si ya existe «Leer».
- **Racha**: días consecutivos marcados que terminan hoy o, si hoy aún no está
  marcado, ayer. Si no está marcado ni hoy ni ayer, la racha es 0.

### Códigos de salida

| Código | Significado |
|---|---|
| 0 | Éxito (incluido marcar un hábito que ya estaba marcado hoy) |
| 1 | Error de dominio o de datos: duplicado, nombre vacío, hábito inexistente o archivo ilegible |
| 2 | Uso incorrecto: comando desconocido o faltan argumentos |

## Datos

Los hábitos se guardan en `~/.habits.json`. Para usar otro archivo (por
ejemplo, para hacer pruebas sin tocar tus datos), define `HABITS_FILE`:

```powershell
$env:HABITS_FILE = "$env:TEMP\habits-prueba.json"   # PowerShell
```

```bash
export HABITS_FILE=/tmp/habits-prueba.json          # bash
```

La escritura es atómica: un fallo nunca deja el archivo a medias. Si el
archivo está dañado, la app no lo modifica y muestra un error indicando su ruta.

## Desarrollo

```console
$ python -m pytest -q
```

```
habits/
├── core.py      # lógica pura: modelo, normalización, marcar y racha (sin I/O)
├── storage.py   # único módulo que lee y escribe el JSON
├── cli.py       # argparse en español, mensajes y códigos de salida
└── __main__.py  # punto de entrada de `python -m habits`
tests/           # un archivo por módulo; cada test nombra el RF o CL que cubre
```
