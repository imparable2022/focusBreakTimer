# Validación — Focus Break Timer 0.2.0

Fecha: 2026-09-04

## Cambio solicitado

La configuración del ciclo 30/5 deja de ser un detalle técnico y queda expuesta como una categoría propia dentro de **Preferencias > Opciones > Temporizador de enfoque** de NVDA.

Controles incluidos:

- **Duración del enfoque, en minutos**. Predeterminado: 30.
- **Duración del descanso, en minutos**. Predeterminado: 5.
- **Repetir los ciclos indefinidamente**. Predeterminado: marcado.
- **Número de ciclos**. Se habilita únicamente cuando la repetición indefinida está desmarcada.
- **Activar Input Lock durante el descanso**. Predeterminado: marcado.
- **Anunciar tiempo restante cada N segundos**. 0 lo desactiva; predeterminado: 300.
- **Reproducir sonidos al cambiar de período**. Predeterminado: marcado.

Los valores se guardan mediante `config.conf` de NVDA. El motor lee la configuración al iniciar o reiniciar el temporizador, por lo que una ejecución que ya está en curso conserva sus parámetros hasta el siguiente inicio/reinicio.

## Decisión de extensión

**Global Plugin**. La función debe operar en cualquier aplicación mientras NVDA está activo. El motor de temporización permanece separado de la capa NVDA.

## Skill aplicada

`nvda-addon-development` v1.6. Se aplicaron sus gates de Global Plugin, lógica pura separada, auditoría AST de gestos, pruebas, revisión de APIs, ciclo de vida y validación del paquete.

## Fuente oficial revisada

- La rama estable pública de NVDA al 2026-09-04 es 2026.2.
- Se verificó el patrón actual de `SettingsPanel` / `NVDASettingsDialog` y se importa desde `gui.settingsDialogs`.
- La interfaz del panel usa controles wx nativos y `guiHelper.BoxSizerHelper`, preservando etiquetas accesibles y navegación normal por Tab.

## Compatibilidad del manifiesto

- `minimumNVDAVersion = 2025.3.0`.
- `lastTestedNVDAVersion = 2025.3.0` se conserva sin elevarlo por análisis estático.
- La revisión contra fuentes actuales de NVDA 2026.2 no sustituye una prueba real dentro de NVDA.

## Gestos

El add-on no declara gestos predeterminados. Los cuatro scripts siguen disponibles para remapeo desde Gestos de entrada.

Auditor `assets/nvda_gesture_audit.py` de la skill v1.6 ejecutado sobre `addon/` con contexto `global_plugin`:

- estado: `clean`;
- bindings estáticos: 0;
- colisiones contextuales: 0;
- diagnósticos dinámicos/no parseables: 0;
- runtime mapping: pendiente, porque no hay proceso NVDA vivo en este entorno.

## Pruebas automatizadas

Resultado: **18/18 OK** con `unittest`.

Además de las pruebas anteriores del motor e Input Lock, se añadieron pruebas para:

- valores predeterminados 30/5 visibles en el panel;
- repetición indefinida marcada por defecto;
- control de número de ciclos deshabilitado cuando la repetición es indefinida;
- guardado de duraciones personalizadas;
- guardado de número finito de ciclos;
- persistencia de repetición indefinida como ciclo ilimitado;
- activación/desactivación de Input Lock desde las opciones.

## Sintaxis / paquete

- `py_compile`: OK.
- AST de Python empaquetado: OK.
- ZIP `.nvda-addon`: íntegro.
- Entradas requeridas: OK.
- Código Python empaquetado idéntico al código fuente usado para construir: OK.
- SHA-256 del paquete: `6321cbf8f39b655659a8f436a16996a8b6ebde76b49b9ac0268ff1d5cf9265df`.

## Ciclo de vida

El panel se registra sólo si aún no está registrado y `terminate()` lo elimina. El scheduler sigue usando una generación lógica de `core.callLater`; detener o terminar invalida callbacks anteriores. Si el temporizador posee un bloqueo de Input Lock, sólo intenta liberar ese bloqueo exacto.

## Pendiente en NVDA real

1. Instalar la build 0.2.0 y reiniciar NVDA.
2. Abrir **Preferencias > Opciones > Temporizador de enfoque**.
3. Recorrer todos los controles con Tab y confirmar sus nombres/estados hablados.
4. Probar, por ejemplo, 1 minuto de enfoque + 1 minuto de descanso + 2 ciclos.
5. Probar repetición indefinida y verificar que **Número de ciclos** quede no disponible.
6. Desmarcar **Activar Input Lock durante el descanso** y confirmar que los descansos no bloqueen la entrada.
7. Volver a marcarla y repetir las pruebas de propiedad segura de Input Lock.
8. Sólo después de la prueba real considerar elevar `lastTestedNVDAVersion`.
