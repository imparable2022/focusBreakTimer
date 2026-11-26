# 0.4.0

- Nueva casilla **Iniciar el temporizador al iniciar NVDA**, desactivada por defecto.
- Nuevo **horario de suspensión** opcional, también desactivado por defecto.
- Valores iniciales del horario: **22:00 → 06:00**.
- El horario admite franjas que cruzan medianoche.
- Al comenzar la franja, un temporizador activo se pausa y se libera únicamente el bloqueo de Input Lock propiedad del complemento.
- Al terminar la franja, el mismo ciclo se reanuda desde el tiempo restante que tenía.
- Si NVDA se inicia dentro de la franja con inicio automático activado, el temporizador espera hasta el final de la suspensión para comenzar.
- Iniciar o reiniciar manualmente durante la franja queda bloqueado con un aviso de la hora de reanudación.
- El comando de estado informa cuando el inicio está pendiente o el temporizador está suspendido por horario.

# 0.3.2

- Nueva casilla **Anunciar automáticamente el tiempo restante**, desactivada por defecto.
- El intervalo de anuncios se mantiene configurable, pero ahora se muestra en **minutos** en lugar de segundos.
- El valor predeterminado visible del intervalo es **5 minutos**.
- Cuando los anuncios automáticos están desactivados, el control del intervalo queda deshabilitado.
- Se conserva compatibilidad con valores guardados por versiones anteriores: por ejemplo, 300 segundos se presentan como 5 minutos.
- El comando **NVDA+Alt+E, T** sigue informando el tiempo restante aunque los anuncios automáticos estén desactivados.

# 0.3.1

- La capa separa iniciar y reiniciar: **I** inicia el temporizador y **Shift+I** lo reinicia desde el comienzo.
- Si se pulsa **I** mientras el temporizador ya está activo, no se reinicia accidentalmente y NVDA indica que se use **Shift+I** para reiniciar.

# Cambios

## 0.3.0 — capa de comandos

- Nuevo gesto predeterminado **NVDA+Alt+E** para activar la capa del complemento.
- **I** inicia o reinicia el temporizador.
- **D** detiene el temporizador.
- **T** informa el estado y el tiempo restante.
- **R** activa o desactiva la repetición indefinida y aplica el cambio al temporizador en curso.
- **O** abre directamente la categoría **Temporizador de enfoque** en las Opciones de NVDA.
- La capa se cierra después de una orden; una tecla desconocida produce un tono y también sale de la capa.
- Se conserva el último número finito de ciclos para que `R` pueda alternar entre repetición indefinida y una configuración finita sin perder ese valor.
- La apertura de Opciones usa `gui.mainFrame.popupSettingsDialog`, API pública actual de NVDA, en lugar de `_popupSettingsDialog` deprecada que todavía aparece en Instant Translate.
- Añadidas pruebas específicas de la capa y del cambio de repetición en caliente.

## 0.2.0 — configuración completa en Opciones de NVDA

- La categoría **Temporizador de enfoque** expone la configuración principal directamente en Preferencias > Opciones de NVDA.
- Duración del enfoque y del descanso configurables en minutos.
- Casilla **Repetir los ciclos indefinidamente**; al desmarcarla se habilita **Número de ciclos**.
- Nueva casilla para activar o desactivar Input Lock durante el descanso.
- Se mantienen configurables los anuncios periódicos y los sonidos.
- Los valores predeterminados siguen siendo 30 minutos de enfoque, 5 minutos de descanso y repetición indefinida.
- Actualizada la importación de `NVDASettingsDialog` para usar `gui.settingsDialogs`.
- Añadidas pruebas del panel de opciones y de la preferencia de Input Lock.

## 0.1.0 — compilación de prueba

- Primera conversión del script independiente a Global Plugin de NVDA.
- Motor puro de enfoque/descanso con pruebas unitarias.
- Configuración de enfoque, descanso, ciclos, anuncios periódicos y sonidos.
- Cuatro comandos remapeables desde Gestos de entrada y sin gestos predeterminados.
- Integración opcional con Input Lock 26.1 mediante el gesto que tenga asignado el usuario.
- El bloqueo iniciado por el temporizador se identifica por el objeto de gesto exacto almacenado por Input Lock, evitando quitar un bloqueo manual posterior.
- Planificación interna mediante `core.callLater`.
