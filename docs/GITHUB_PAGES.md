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

| Sección | Qué muestra |
|---------|-------------|
| Reglas confirmadas | 2 vs 2, 2-2 → penales, Trampa/Marca |
| Reglamentos | Pestañas v0 / v1 |
| Mazos | Composición de cada mazo |
| Resultados | Gráficos y tablas de simulación |
| Hallazgos | v0 estancado, v1 dinámico, preguntas abiertas |
| Simulador | Comandos para correr localmente |

Los `.md` del repo siguen disponibles como links directos (ej. `resultados-iniciales.md`).

## Actualizar resultados

1. Corré simulaciones: `python3 -m simulador compare`
2. Actualizá `docs/resultados-iniciales.md`
3. Actualizá los números en `docs/index.html` (sección `#resultados`)
4. Commit + push → GitHub Pages se actualiza solo

## Notas

- El archivo `docs/.nojekyll` evita que Jekyll procese el sitio (HTML estático puro).
- No hace falta GitHub Actions para este setup.
