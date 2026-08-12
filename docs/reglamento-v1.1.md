# Reglamento v1.1 — pasa al compañero

Variante de prueba sobre [v1](reglamento-v1.md).

## Cambio respecto a v1

Si el atacante **pasa de turno** y la defensa **no coloca** Trampa de offside ni Marca personal, la pelota **pasa automáticamente a un compañero** del mismo equipo (sin incrementar pases en la jugada).

En v1 baseline, en ese caso no pasa nada: el mismo jugador retiene la pelota.

## Especificación para el simulador

Archivo: [`reglamentos/v1.1.json`](../reglamentos/v1.1.json) (extiende `v1`).

```json
"reglas": {
  "pasa_turno_sin_respuesta": "pasa_companero"
}
```

## Cómo probar

```bash
python3 -m simulador simular v1.1 --partidos 200
python3 -m simulador comparar v1 v1.1 --partidos 200
```
