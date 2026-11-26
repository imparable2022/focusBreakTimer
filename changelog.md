# Cambios

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
