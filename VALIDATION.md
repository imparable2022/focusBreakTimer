# Validación — Focus Break Timer 0.3.2

Fecha: 2026-09-04

## Cambio solicitado

La configuración de anuncios periódicos queda formada por dos controles en **Preferencias > Opciones > Temporizador de enfoque**:

- **Anunciar automáticamente el tiempo restante**: casilla desactivada por defecto.
- **Anunciar tiempo restante cada, en minutos**: control numérico, 5 minutos por defecto.

Cuando la casilla está desmarcada, el control de intervalo queda deshabilitado y no se producen anuncios automáticos como “Enfoque: quedan 30 minutos”. El comando bajo demanda **NVDA+Alt+E, T** permanece independiente y sigue informando fase, ciclo y tiempo restante.

## Compatibilidad de configuración

El almacenamiento histórico `announceEverySeconds` se conserva internamente para no romper preferencias existentes. La interfaz convierte el valor a minutos al mostrarlo y vuelve a segundos al guardarlo. Ejemplo validado: 600 segundos existentes se presentan como 10 minutos.

## Decisión de extensión

**Global Plugin**, sin cambios respecto de 0.3.1.

## Skill aplicada

`nvda-addon-development` v1.6.

## Gestos

No se modificaron gestos respecto de 0.3.1. El auditor AST de la skill v1.6 sobre `addon/` informa `clean` y reconoce:

- `NVDA+Alt+E` para entrar a la capa;
- `I`, `Shift+I`, `D`, `T`, `R` y `O` dentro de la capa.

La auditoría completa contra complementos habilitados y `gestures.ini` reales sólo puede completarse dentro de la instalación NVDA del usuario.

## Pruebas automatizadas

Resultado: **35/35 OK**.

Incluyen, además de las pruebas existentes:

- casilla de anuncios automáticos desactivada por defecto;
- intervalo visible de 5 minutos por defecto;
- control de intervalo deshabilitado cuando la casilla está desmarcada;
- habilitación del intervalo al marcar la casilla;
- guardado de 10 minutos como 600 segundos para compatibilidad;
- conversión de 600 segundos existentes a 10 minutos visibles;
- supresión del anuncio automático cuando la casilla está desactivada;
- emisión del anuncio automático cuando está activada.

## Validación runtime

El usuario confirmó que la versión 0.3.1 funciona en su NVDA real. La modificación específica de 0.3.2 todavía debe probarse en ese runtime; no se presenta la prueba estática como sustituto de esa comprobación.

## Compatibilidad NVDA

- `minimumNVDAVersion = 2025.3.0`.
- `lastTestedNVDAVersion = 2025.3.0` se mantiene conservador en el manifiesto.
- Esta modificación no introduce APIs NVDA nuevas respecto de 0.3.1.

## Paquete generado

- `focusBreakTimer-0.3.2.nvda-addon`
- SHA-256: `1fca70f46cf731da2a6ef43fd11333a6d1e3402297100edbc408aae85a499a68`
- ZIP íntegro y con `manifest.ini`, código y documentación esperados.
