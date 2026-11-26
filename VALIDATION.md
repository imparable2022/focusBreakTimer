# Validación — Focus Break Timer 0.3.0

Fecha: 2026-09-04

## Cambio solicitado

Se añadió una capa de comandos con entrada predeterminada **NVDA+Alt+E**:

- **I**: iniciar o reiniciar el temporizador.
- **D**: detenerlo.
- **T**: informar fase, ciclo y tiempo restante.
- **R**: activar o desactivar la repetición indefinida.
- **O**: abrir directamente **Preferencias > Opciones > Temporizador de enfoque**.

La capa ejecuta una sola orden y luego restaura el gesto base. Una tecla no reconocida emite un tono y también cierra la capa.

## Patrón estudiado: Instant Translate

Se revisó `nvdaaddons/instantTranslate`, archivo `addon/globalPlugins/instantTranslate/__init__.py`.

El patrón observado usa:

- un booleano de estado para saber si la capa está activa;
- `getScript` para interceptar el siguiente gesto mientras la capa está activa;
- `bindGestures` para enlazar temporalmente las letras de la capa;
- `clearGestureBindings` al finalizar;
- restauración del gesto de entrada;
- tono ante una tecla no reconocida;
- salida de la capa después de ejecutar un comando.

Focus Break Timer adopta ese patrón de una sola orden, pero no copia la apertura de ajustes de Instant Translate. El código actual de Instant Translate todavía usa `_popupSettingsDialog`; la fuente actual de NVDA marca ese método como deprecado y ofrece `popupSettingsDialog`. Esta versión usa `gui.mainFrame.popupSettingsDialog(NVDASettingsDialog, FocusBreakSettingsPanel)` para abrir directamente la categoría del complemento.

## Repetición con R

La configuración histórica utiliza `cycles = 0` para repetición indefinida. Se añadió `finiteCycles` (predeterminado 4) para conservar el último número finito elegido.

Comportamiento:

- si la repetición está activada, **R** la desactiva y recupera `finiteCycles`;
- si está desactivada, **R** guarda el número finito actual y activa repetición indefinida;
- si el temporizador está corriendo, el motor cambia su objetivo sin reiniciar la fase actual;
- si al desactivar la repetición el ciclo actual ya alcanzó/superó el objetivo finito guardado, se detiene al terminar el ciclo actual.

## Decisión de extensión

**Global Plugin**. La funcionalidad opera en cualquier aplicación mientras NVDA está activo.

## Skill aplicada

`nvda-addon-development` v1.6.

## Fuente oficial NVDA revisada

- NVDA estable público: 2026.2 al 2026-09-04.
- `gui.mainFrame.popupSettingsDialog` existe como API pública actual.
- `_popupSettingsDialog` está deprecado.
- `NVDASettingsDialog` admite una clase de panel inicial y selecciona esa categoría en su lista.

## Auditoría de gestos

Auditor AST `assets/nvda_gesture_audit.py` de la skill v1.6 sobre `addon/`:

- estado: `clean`;
- gesto base detectado: `kb:NVDA+alt+e` → `timerLayer`;
- gestos temporales detectados: `i`, `d`, `t`, `r`, `o`;
- colisiones internas: 0;
- diagnósticos dinámicos/no parseables: 0;
- runtime mapping: pendiente porque no hay proceso NVDA vivo en este entorno.

No fue posible auditar los complementos **habilitados** ni los `gestures.ini` reales de la instalación Windows del usuario. Además, una búsqueda pública detectó que otros complementos publicados, como Date Parser e Invisinote, también anuncian **NVDA+Alt+E** como gesto predeterminado. El gesto se conserva porque fue solicitado explícitamente; si alguno de esos complementos estuviera habilitado, debe remapearse uno desde Gestos de entrada.

## Pruebas automatizadas

Resultado: **29/29 OK**.

Incluyen:

- motor 30/5 y ciclos finitos/infinitos;
- cambio del objetivo de repetición durante una ejecución;
- entrada de la capa con NVDA+Alt+E;
- I inicia y cierra la capa;
- D detiene y cierra la capa;
- T informa el tiempo;
- R alterna repetición y conserva el último número finito;
- R modifica el motor activo sin reiniciarlo;
- O abre directamente `FocusBreakSettingsPanel`;
- tecla desconocida sale de la capa;
- panel de Opciones;
- integración y propiedad segura de Input Lock.

## Sintaxis / paquete

- `py_compile`: OK.
- AST de todos los Python empaquetados: OK.
- Build por `build.py`: OK.
- ZIP `.nvda-addon`: íntegro.
- `manifest.ini` en la raíz: OK.
- documentación declarada presente: OK.
- código Python empaquetado idéntico al fuente de construcción: OK.
- SHA-256 del paquete: `81bb4de99d49066bcb3e4ba16ba108c1cb2b31a3a6d9d689fe1d2c29bab8d976`.

## Compatibilidad

- `minimumNVDAVersion = 2025.3.0`.
- `lastTestedNVDAVersion = 2025.3.0` se mantiene conservador.
- La revisión estática contra NVDA 2026.2 no se presenta como prueba runtime.

## Pendiente en NVDA real

1. Instalar la 0.3.0 y reiniciar NVDA.
2. Pulsar NVDA+Alt+E y luego I; confirmar inicio.
3. Pulsar NVDA+Alt+E y luego T; confirmar tiempo/fase/ciclo.
4. Pulsar NVDA+Alt+E y luego R dos veces; confirmar mensajes de repetición desactivada/activada.
5. Pulsar NVDA+Alt+E y luego O; confirmar que se abre directamente la categoría Temporizador de enfoque.
6. Pulsar NVDA+Alt+E y luego D; confirmar detención.
7. Probar una tecla no definida dentro de la capa; confirmar tono y salida.
8. Ejecutar auditoría contra complementos habilitados y los mapas de gestos reales de esa instalación.
