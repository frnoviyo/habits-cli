# Spec 001 — MVP de habits-cli

Estado: aprobada · Fecha: 2026-10-14

## 1. Contexto y objetivo

Quien estudia de forma autodidacta suele abandonar sus rutinas porque no ve su
constancia. Este MVP permite registrar hábitos de estudio, marcar cada día los
que se han cumplido y ver la racha de días consecutivos de cada uno, para que
mantener la racha funcione como motivación.

Objetivo: una herramienta de línea de comandos con tres operaciones (crear un
hábito, marcarlo como hecho hoy y listar los hábitos con su racha) que sea
fiable, predecible y fácil de mantener por un desarrollador junior.

## 2. Usuarios

- **Estudiante (usuario principal)**: una sola persona en su propio equipo, que
  usa la terminal con soltura básica. No hay multiusuario ni sincronización.
- **Desarrollador junior (mantenedor)**: debe poder entender y ampliar el
  comportamiento a partir de esta spec.

## 3. Historias de usuario

- **HU-1**: Como estudiante, quiero crear un hábito con un nombre para empezar a
  registrar su cumplimiento.
- **HU-2**: Como estudiante, quiero marcar un hábito como hecho hoy para que
  cuente en mi racha.
- **HU-3**: Como estudiante, quiero listar mis hábitos con su racha actual y si
  ya los hice hoy para saber qué me falta y cómo voy.

## 4. Requisitos funcionales

Los criterios de aceptación usan EARS en español:
*El sistema DEBERÁ…* (siempre) · *CUANDO <evento>, el sistema DEBERÁ…* ·
*MIENTRAS <estado>, el sistema DEBERÁ…* · *SI <condición no deseada>, ENTONCES el sistema DEBERÁ…*

### Definiciones

- **Nombre normalizado**: el nombre sin espacios al principio ni al final y sin
  distinguir mayúsculas de minúsculas. Dos hábitos son el mismo si sus nombres
  normalizados coinciden.
- **Hoy**: la fecha del calendario local del equipo del usuario en el momento de
  ejecutar el comando.
- **Racha actual**: número de días consecutivos marcados que termina hoy o, si
  hoy no está marcado, ayer. Si no están marcados ni hoy ni ayer, la racha es 0.

### RF-1 — Crear un hábito (HU-1)

- RF-1.1: CUANDO el usuario crea un hábito con un nombre válido y no duplicado,
  el sistema DEBERÁ guardarlo con racha 0, sin días marcados, y confirmar la
  creación con un mensaje.
- RF-1.2: El sistema DEBERÁ conservar el nombre tal como lo escribió el usuario,
  sin los espacios de los extremos, para mostrarlo en el listado.
- RF-1.3: SI el nombre normalizado coincide con el de un hábito existente,
  ENTONCES el sistema DEBERÁ rechazar la creación con un mensaje de error, salir
  con un código distinto de 0 y no modificar los datos.
- RF-1.4: SI el nombre está vacío o solo contiene espacios, ENTONCES el sistema
  DEBERÁ rechazar la creación con un mensaje de error, salir con un código
  distinto de 0 y no modificar los datos.

### RF-2 — Marcar un hábito como hecho hoy (HU-2)

- RF-2.1: CUANDO el usuario marca un hábito existente que no estaba marcado hoy,
  el sistema DEBERÁ registrar hoy como día cumplido y confirmarlo con un mensaje
  que incluya la racha actual resultante.
- RF-2.2: El sistema DEBERÁ localizar el hábito por su nombre normalizado.
- RF-2.3: MIENTRAS el hábito ya esté marcado hoy, CUANDO el usuario lo marque de
  nuevo, el sistema DEBERÁ dejar los datos sin cambios, avisar con un mensaje del
  tipo «Ya estaba marcado hoy» y salir con código 0.
- RF-2.4: SI no existe ningún hábito con ese nombre normalizado, ENTONCES el
  sistema DEBERÁ mostrar un mensaje de error, salir con un código distinto de 0
  y no crear ni modificar ningún hábito.
- RF-2.5: El sistema DEBERÁ permitir marcar únicamente el día de hoy.

### RF-3 — Listar hábitos con su racha (HU-3)

- RF-3.1: CUANDO el usuario lista los hábitos, el sistema DEBERÁ mostrar una
  línea por hábito, en orden de creación, con el nombre, la racha actual y si
  está hecho hoy.
- RF-3.2: El sistema DEBERÁ calcular la racha actual según la definición de este
  documento, en el momento de listar.
- RF-3.3: SI no hay ningún hábito, ENTONCES el sistema DEBERÁ mostrar el mensaje
  «No hay hábitos todavía» y salir con código 0.

### RF-4 — Comportamiento general

- RF-4.1: El sistema DEBERÁ conservar los hábitos y sus días marcados entre
  ejecuciones.
- RF-4.2: El sistema DEBERÁ mostrar todos los mensajes al usuario en español.
- RF-4.3: CUANDO un comando termina con éxito, el sistema DEBERÁ salir con
  código 0; SI termina con error, ENTONCES DEBERÁ salir con un código distinto
  de 0.
- RF-4.4: SI el usuario invoca un comando inexistente o sin los argumentos
  necesarios, ENTONCES el sistema DEBERÁ mostrar un mensaje de uso en español y
  salir con un código distinto de 0.
- RF-4.5: CUANDO se ejecuta por primera vez sin datos previos, el sistema DEBERÁ
  comportarse como si no hubiera hábitos, sin error.

## 5. Requisitos no funcionales

- RNF-1: Funciona sin conexión a internet y sin servicios externos.
- RNF-2: Cada comando responde en menos de 1 segundo con hasta 100 hábitos y
  3 años de historial.
- RNF-3: Una operación fallida nunca deja los datos guardados a medias ni
  corruptos.
- RNF-4: El cálculo de rachas es determinista y verificable con pruebas
  automáticas sin depender de la fecha real del sistema.
- RNF-5: Los mensajes de error indican qué falló y, cuando aplica, cómo
  corregirlo.

## 6. Casos límite

| # | Situación | Resultado esperado |
|---|-----------|--------------------|
| CL-1 | Crear «Leer» existiendo « leer » | Error de duplicado (RF-1.3) |
| CL-2 | Crear con nombre «   » | Error de nombre vacío (RF-1.4) |
| CL-3 | Marcar «LEER» existiendo «Leer» | Marca «Leer» (RF-2.2) |
| CL-4 | Marcar dos veces el mismo día | Aviso, código 0, sin cambios (RF-2.3) |
| CL-5 | Marcar un hábito inexistente | Error, no se crea (RF-2.4) |
| CL-6 | Marcado ayer y anteayer, hoy no | Racha 2, «no hecho hoy» |
| CL-7 | Marcado hoy, ayer no, anteayer sí | Racha 1 |
| CL-8 | Último día marcado hace 2 días o más | Racha 0 |
| CL-9 | Hábito recién creado | Racha 0, «no hecho hoy» |
| CL-10 | Racha que cruza cambio de mes o de año (31-dic → 1-ene) | Se cuenta como consecutiva |
| CL-11 | Racha que incluye el 29 de febrero | Se cuenta como consecutiva |
| CL-12 | Listar sin hábitos | «No hay hábitos todavía», código 0 |
| CL-13 | Nombre con tildes o eñes («Repasar inglés») | Se acepta y se muestra tal cual |

## 7. Fuera de alcance (MVP)

- Borrar o renombrar hábitos.
- Desmarcar un día ya marcado.
- Marcar días pasados o futuros.
- Racha máxima histórica, totales u otras estadísticas.
- Frecuencias distintas de la diaria (p. ej., «3 veces por semana»).
- Varios usuarios, sincronización o acceso remoto.
- Recordatorios o notificaciones.

## 8. Criterios de finalización

- [x] Todos los criterios de RF-1 a RF-4 y todos los casos límite CL-1 a CL-13 están
  cubiertos por pruebas automáticas que pasan.
- [x] Los tres comandos funcionan de extremo a extremo desde la terminal.
- [x] Se cumplen los principios de `docs/constitution.md`.
- [x] No quedan dudas abiertas sin resolver o se han aplazado explícitamente a otra
  spec.

## 9. Dudas resueltas

Las dudas abiertas del borrador se resolvieron el 2026-10-14 (decisiones DP1–DP4
del plan) y quedan como requisitos:

- **D-1 — Longitud y caracteres del nombre** (antes [NECESITA ACLARACIÓN]):
  - El sistema DEBERÁ aceptar nombres de cualquier longitud que no estén vacíos
    tras quitar los espacios de los extremos.
  - Restringir caracteres como saltos de línea o tabuladores queda aplazado a una
    spec posterior (fuera del MVP).
- **D-2 — Datos guardados dañados** (antes [NECESITA ACLARACIÓN]):
  - SI los datos guardados están dañados o son ilegibles, ENTONCES el sistema
    DEBERÁ mostrar un mensaje de error que indique dónde están los datos y cómo
    empezar de cero, salir con un código distinto de 0 y no modificar los datos.
- **D-3 — Cambio de día durante la ejecución** (antes [NECESITA ACLARACIÓN]):
  - CUANDO se ejecuta un comando, el sistema DEBERÁ determinar «hoy» una única
    vez al inicio y usar esa fecha durante toda la ejecución.
- **D-4 — Indicador «hecho hoy» en el listado** (antes [NECESITA ACLARACIÓN]):
  - El sistema DEBERÁ indicar «hecho hoy» con `[x]` y «no hecho hoy» con `[ ]`,
    usando solo caracteres ASCII para que se vea en cualquier terminal.
