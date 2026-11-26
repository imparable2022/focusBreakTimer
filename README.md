# Focus Break Timer para NVDA

**Focus Break Timer** es un complemento para NVDA que desarrollé desde cero con la idea de poder organizar mejor los tiempos de estudio o de trabajo, alternando momentos de concentración con descansos.

Por ejemplo, si estás estudiando, podés configurar el complemento para que te avise cuando hayan pasado 30 minutos, descanses durante 5 minutos y después vuelvas a estudiar otros 30 minutos. Todo esto se puede hacer de forma automática y sin tener que salir del programa que estés usando.

El complemento está escrito en Python, funciona directamente desde NVDA y ha sido probado con el lector de pantalla.

## ¿Qué podés hacer con este complemento?

- **Elegir tus tiempos:** Podés configurar cuántos minutos querés dedicar a concentrarte y cuántos querés descansar.
- **Repetir los ciclos:** Podés elegir cuántas veces querés repetirlos o hacer que se repitan hasta que decidas detener el temporizador.
- **Consultar el tiempo restante:** Podés hacerlo cuando quieras o configurar NVDA para que te lo anuncie cada cierta cantidad de minutos.
- **Recibir avisos:** NVDA te avisa cuando termina el tiempo de concentración o de descanso. También podés activar los avisos sonoros.
- **Bloquear el teclado durante los descansos:** Si tenés instalado Input Lock, podés hacer que el complemento bloquee el teclado durante el descanso y lo desbloquee cuando sea momento de continuar.
- **Iniciar el temporizador automáticamente:** Si querés, podés hacer que comience cada vez que iniciás NVDA.
- **Elegir un horario de suspensión:** Por ejemplo, podés hacer que el temporizador deje de funcionar a las 22:00 y continúe a las 06:00 del día siguiente, sin perder el tiempo que te quedaba.

## Cómo usarlo

Presioná **NVDA+Alt+E** y después una de estas teclas, según lo que quieras hacer:

- **I:** iniciar el temporizador.
- **Shift+I:** reiniciar el temporizador desde el principio.
- **D:** detenerlo.
- **T:** escuchar en qué período estás, el ciclo actual y cuánto tiempo queda.
- **R:** activar o desactivar la repetición indefinida.
- **O:** abrir las opciones del complemento.

Después de ejecutar un comando vas a poder seguir usando el teclado normalmente. Si presionás una tecla que no corresponde a ningún comando, vas a escuchar un sonido y también vas a salir de la capa de comandos.

Si otro complemento utiliza NVDA+Alt+E, podés cambiar este atajo desde **Preferencias > Gestos de entrada > Temporizador de enfoque**.

## Cómo configurarlo

Desde **Preferencias > Opciones > Temporizador de enfoque**, o presionando NVDA+Alt+E y después O, vas a poder cambiar todas las opciones.

Por defecto, el complemento viene configurado con 30 minutos de concentración, 5 minutos de descanso y repetición indefinida. El inicio automático y la suspensión por horario están desactivados.

Si desactivás la repetición indefinida, se recupera la cantidad de ciclos que hayas configurado anteriormente (4 por defecto). Podés cambiar esta opción incluso mientras el temporizador está funcionando, sin tener que empezar de nuevo.

## Cómo descargarlo

Podés consultar las versiones del complemento en [GitHub Releases](https://github.com/imparable2022/focusBreakTimer/releases) y las compilaciones automáticas en [GitHub Actions](https://github.com/imparable2022/focusBreakTimer/actions).

## Sobre Input Lock

No necesitás tener Input Lock instalado para usar el temporizador. Es una opción más para quienes quieran dejar de usar el teclado durante sus descansos.

Si querés usar esta función, necesitás tener asignado un atajo al comando de bloqueo de Input Lock. El temporizador detecta ese comando automáticamente. Si bloqueás el teclado por tu cuenta, el complemento no va a quitar ese bloqueo como si lo hubiera iniciado él.

## Para programadores

La lógica del temporizador está separada de la integración con NVDA en `focusBreakTimerCore.py`. El proyecto dispone de pruebas unitarias y de un flujo de GitHub Actions para probar y empaquetar el complemento en Windows.

La integración con Input Lock se desarrolló tomando como referencia la versión 26.1. La capa de comandos utiliza un patrón inspirado en Instant Translate.

## Versiones y pruebas

La versión actual es la 0.4.0. Las versiones 0.3.x fueron probadas con NVDA y la versión 0.4.0 cuenta con 46 pruebas automatizadas superadas. El inicio automático y la suspensión por horario incorporados en esta última versión todavía requieren una comprobación específica con NVDA antes de considerarlos completamente validados.

Podés consultar los cambios de cada versión en el [historial de cambios](changelog.md).

Si el complemento te sirve o tenés alguna sugerencia sobre algo que te gustaría que le agregue, podés dejarme un mensaje en la sección de [Issues](https://github.com/imparable2022/focusBreakTimer/issues).
