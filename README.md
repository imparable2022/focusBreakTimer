# Focus Break Timer para NVDA

Proyecto fuente del complemento `focusBreakTimer`.

Convierte el script original de temporizador 30/5 en un Global Plugin de NVDA. No abre una consola ni ejecuta un Python externo. La lógica del temporizador está separada de la integración con NVDA en `focusBreakTimerCore.py` y dispone de pruebas unitarias.

## Capa de comandos

El complemento usa una capa de comandos inspirada en el patrón de **Instant Translate**.

Pulse **NVDA+Alt+E** y después una de estas teclas:

- **I**: inicia el temporizador.
- **Shift+I**: reinicia el temporizador desde el comienzo.
- **D**: detiene el temporizador.
- **T**: informa la fase, el ciclo y el tiempo restante.
- **R**: activa o desactiva la repetición indefinida.
- **O**: abre directamente **Preferencias > Opciones > Temporizador de enfoque**.

La capa termina después de ejecutar una orden. Una tecla no reconocida produce un tono de error y también cierra la capa. La entrada a la capa aparece en **Gestos de entrada > Temporizador de enfoque** y puede remapearse si fuera necesario.

Al desactivar la repetición con **R**, se recupera el último número finito de ciclos configurado (4 por defecto). Si el temporizador ya está funcionando, el cambio se aplica inmediatamente. Al volver a activar la repetición, el ciclo pasa a ser indefinido sin reiniciar el período actual.

## Configuración

La configuración está en **Preferencias > Opciones > Temporizador de enfoque**. Allí se puede configurar:

- duración del enfoque, en minutos;
- duración del descanso, en minutos;
- repetir los ciclos indefinidamente;
- o, si la repetición indefinida está desactivada, el número exacto de ciclos;
- activar o no Input Lock durante el descanso;
- casilla para anunciar automáticamente el tiempo restante;
- intervalo entre esos anuncios, expresado en minutos;
- sonidos al cambiar entre enfoque y descanso.

Los valores predeterminados siguen siendo **30 minutos de enfoque, 5 minutos de descanso y repetición indefinida**. Los cambios se guardan en la configuración de NVDA y se aplican al iniciar o reiniciar el temporizador.

## Input Lock

La integración es opcional y se diseñó contra Input Lock 26.1. El comando **Toggle input lock** de Input Lock debe tener un gesto de teclado asignado. Focus Break Timer localiza ese gesto en los mapeos de NVDA y llama al propio script de Input Lock; no simula CapsLock+Alt+T ni presupone cuál es la tecla NVDA.

El temporizador conserva como token de propiedad el objeto de gesto exacto que Input Lock almacena al bloquear. Si el usuario desbloquea o desbloquea y vuelve a bloquear manualmente, ese token deja de coincidir y Focus Break Timer no modifica el nuevo bloqueo.

## Estado de validación

Esta es una **compilación de prueba 0.3.2**. El usuario confirmó que la versión 0.3.1 funciona en su NVDA real. Para 0.3.2 se comprobaron de forma automatizada el motor, la capa de comandos, el nuevo control de anuncios, la apertura directa de Opciones, la integración con Input Lock, sintaxis, estructura y paquete. El cambio específico de 0.3.2 todavía debe probarse en el NVDA real antes de considerarlo validado en runtime o listo para publicación en Add-on Store.

El manifiesto mantiene de forma conservadora `lastTestedNVDAVersion = 2025.3.0`; no se eleva a 2026.2 sólo a partir de análisis estático.

### Nota sobre NVDA+Alt+E

El gesto se incluyó exactamente como fue solicitado. Existen otros complementos públicos que también pueden usar **NVDA+Alt+E**; por ejemplo Date Parser e Invisinote lo publican como gesto predeterminado. Si alguno de ellos está habilitado en la misma instalación, deberá remapearse uno de los comandos desde Gestos de entrada. La auditoría completa contra los complementos habilitados y `gestures.ini` reales debe hacerse dentro del NVDA del usuario.
