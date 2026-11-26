# Validación — Focus Break Timer 0.4.0

Fecha: 2026-09-04

## Cambios solicitados

Se añadieron dos opciones a **Preferencias > Opciones > Temporizador de enfoque**:

- **Iniciar el temporizador al iniciar NVDA**: desactivada por defecto.
- **Suspender el temporizador automáticamente en un horario**: desactivada por defecto.

El horario viene precargado con:

- desde **22:00**;
- hasta **06:00**.

Los controles de hora y minutos quedan deshabilitados mientras la casilla del horario esté desmarcada.

## Semántica del horario

La franja es una suspensión del temporizador, no un cambio de duración:

- admite cruce de medianoche (`22:00 -> 06:00`);
- al entrar en la franja, si el temporizador está en enfoque o descanso, se pausa conservando el tiempo restante;
- si el complemento había activado Input Lock durante un descanso, libera únicamente ese bloqueo propio antes de quedar suspendido;
- un bloqueo manual del usuario nunca se reclama ni se libera;
- al salir de la franja, el mismo ciclo se reanuda desde el punto conservado;
- iniciar o reiniciar manualmente dentro de la franja se rechaza y NVDA informa la hora de reanudación;
- si NVDA arranca dentro de la franja con inicio automático activado, el inicio queda pendiente hasta el final de la suspensión;
- detener manualmente cancela un inicio automático pendiente.

## Diseño

Se mantiene el **Global Plugin**. La lógica pura para determinar si una hora cae dentro de una franja diaria se añadió a `focusBreakTimerCore.py`, separada de la capa NVDA.

La vigilancia horaria se realiza con `core.callLater`. El bucle normal del temporizador también comprueba el horario antes de avanzar de fase, evitando que en el límite de las 22:00 llegue a iniciar un descanso/bloqueo justo antes de que actúe el vigilante horario.

## Skill aplicada

`nvda-addon-development` v1.6.

## Pruebas automatizadas

Resultado: **46/46 OK**.

Incluyen:

- franja normal diurna;
- franja cruzando medianoche 22:00 -> 06:00;
- límites exactos: 22:00 incluido, 06:00 excluido;
- configuración predeterminada desactivada con 22:00 y 06:00 precargados;
- habilitación/deshabilitación accesible de los controles horarios;
- persistencia de horas y minutos;
- bloqueo de inicio manual dentro de la franja;
- pausa al entrar y reanudación al salir;
- liberación segura de Input Lock al comenzar la suspensión;
- inicio automático inmediato fuera de la franja;
- inicio automático diferido cuando NVDA arranca dentro de la franja;
- cancelación del inicio diferido mediante Detener;
- todas las pruebas previas del motor, Input Lock, anuncios y capa de comandos.

## Gestos

No se cambió ningún gesto respecto de 0.3.2. El auditor AST de la skill v1.6 sobre `addon/` informa `clean` y reconoce:

- `NVDA+Alt+E`;
- `I`, `Shift+I`, `D`, `T`, `R` y `O` dentro de la capa.

La auditoría runtime contra los complementos habilitados y `gestures.ini` reales debe hacerse dentro del NVDA del usuario.

## Sintaxis y paquete

- `py_compile` de todos los Python del complemento y pruebas: OK.
- Integridad ZIP del `.nvda-addon`: OK.
- `manifest.ini` en la raíz: OK.
- documentación `doc/es/readme.html` y `doc/es/changelog.html`: incluida.

## Validación runtime

El usuario confirmó previamente el funcionamiento de la rama 0.3.x en su NVDA real. Las funciones nuevas de 0.4.0 (inicio automático y horario de suspensión) todavía requieren la prueba real en esa instalación. No se presenta la validación estática como sustituto de esa prueba.

## Compatibilidad NVDA

- `minimumNVDAVersion = 2025.3.0`.
- `lastTestedNVDAVersion = 2025.3.0` se mantiene conservador.
- 0.4.0 no introduce dependencias de terceros ni APIs privadas nuevas de NVDA.
