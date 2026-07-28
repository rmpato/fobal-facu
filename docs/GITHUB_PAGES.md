# Publicar en GitHub Pages

El sitio está en la carpeta `docs/` (`index.html` + assets).

## Pasos

1. **Subí el repo a GitHub** (si todavía no está):

   ```bash
   git init
   git add .
   git commit -m "Sitio y simulador fobal-facu"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/fobal-facu.git
   git push -u origin main
   ```

2. **Activá GitHub Pages** en el repo:
   - GitHub → **Settings** → **Pages**
   - **Source:** Deploy from a branch
   - **Branch:** `main` → carpeta **`/docs`**
   - Save

3. **Esperá 1–2 minutos.** El sitio queda en:

   ```
   https://TU_USUARIO.github.io/fobal-facu/
   ```

## Contenido del sitio

| Página | Qué muestra |
|--------|-------------|
| `index.html` | Inicio, reglas confirmadas, resumen reciente |
| `reglas.html` | Reglamentos v0/v1, mazos, dados |
| `resultados.html` | IA estratégica, acciones %, variantes, histórico |
| `como-funciona.html` | Motor, IA, dados, métricas, limitaciones |
| `simulador.html` | Comandos CLI, perfiles IA, variantes JSON |
| `crear-reglamento.html` | Cómo crear v1.2 / v2 / v3 — JSON, push, cuándo tocar código |

Los `.md` del repo siguen disponibles como links directos (ej. `resultados-iniciales.md`).

## Actualizar resultados

1. Corré simulaciones: `python3 -m simulador compare`
2. Actualizá `docs/resultados-iniciales.md`
3. Actualizá los números en `docs/resultados.html` (y opcionalmente `index.html`)
4. Commit + push → GitHub Pages se actualiza solo

## Notas

- El archivo `docs/.nojekyll` evita que Jekyll procese el sitio (HTML estático puro).
- No hace falta GitHub Actions para este setup.
