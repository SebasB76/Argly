# Despliegue — Argly

Arquitectura de despliegue: **frontend en Vercel** + **backend (FastAPI + ML) en un
host con Python y Postgres** (Render / Railway / Fly.io). El frontend llama al backend
por la variable `VITE_API_BASE`.

```
  Navegador ──> Vercel (React estático) ──fetch /api──> Backend FastAPI ──> Postgres
```

> Vercel no es buen sitio para el backend: filesystem efímero (no persiste SQLite),
> y scikit-learn+scipy pueden exceder el límite de las funciones serverless. Por eso
> el backend va aparte, con **Postgres gestionado** para persistir feedback, estados,
> bitácora y checklist.

---

## 1. Backend (Render — recomendado, con el blueprint incluido)

1. Sube el repo a GitHub.
2. En **Render → New → Blueprint**, selecciona el repo. Render lee `render.yaml` y crea:
   - el servicio web `argly-api` (build con `Dockerfile.backend`), y
   - la base `argly-db` (Postgres), inyectando `DATABASE_URL` automáticamente.
3. Tras el deploy, define en el servicio la variable **`CORS_ORIGINS`** con la URL de
   Vercel (la tendrás en el paso 2). Mientras tanto puedes dejar `*`.
4. Verifica: `https://argly-api.onrender.com/health` → `{"status":"ok"}`.
   En el primer arranque la DB se **siembra sola** con el dataset sintético.

**Alternativas equivalentes**
- **Railway**: New Project → Deploy from Repo → usa `Dockerfile.backend`; añade un
  plugin Postgres (inyecta `DATABASE_URL`); set `CORS_ORIGINS`.
- **Fly.io**: `fly launch` (detecta el Dockerfile), `fly postgres create` y
  `fly postgres attach` (inyecta `DATABASE_URL`); set `CORS_ORIGINS` con `fly secrets set`.
- **Postgres externo** (Neon/Supabase): crea la base, copia su connection string a
  `DATABASE_URL`. El código acepta `postgres://` y lo normaliza a `postgresql+psycopg2://`.

Variables del backend:

| Variable | Obligatoria | Para qué |
|---|---|---|
| `DATABASE_URL` | sí (prod) | Postgres. Sin ella usa SQLite local (no persiste en la nube). |
| `CORS_ORIGINS` | sí | URL(es) del frontend, separadas por coma. Por defecto `*`. |
| `GEMINI_API_KEY` / `LLM_*` | no | Habilita el agente LLM. Sin esto, el núcleo sigue funcionando. |

---

## 2. Frontend (Vercel)

1. En **Vercel → Add New → Project**, importa el mismo repo.
2. Vercel detecta `vercel.json` (compila `frontend/` y publica `frontend/dist`).
   *(Alternativa: dejar `vercel.json` fuera y poner **Root Directory = `frontend`**;
   Vite se autodetecta.)*
3. En **Settings → Environment Variables** añade:
   - `VITE_API_BASE = https://argly-api.onrender.com/api`  (la URL del backend + `/api`)
4. **Deploy**. Copia la URL resultante (`https://argly.vercel.app`) y pégala en
   `CORS_ORIGINS` del backend (paso 1.3); redeploy del backend.

> `VITE_API_BASE` se hornea en build: si la cambias, hay que **redeploy** del front.

---

## 3. Comprobación

- `GET {backend}/health` responde `ok`.
- Abre la URL de Vercel → el Overview carga datos (si no, revisa `VITE_API_BASE` y CORS).
- Marca un caso (veredicto/estado/nota) y recarga: **debe persistir** (Postgres OK).

---

## Notas

- **Primer arranque lento**: el backend entrena el RandomForest al levantar y al primer
  request. En planes free puede tardar; tras eso queda cacheado en memoria.
- **Reset del dataset**: `POST /api/dataset/reset` (o el botón en la vista *Datos*).
- **Migración de esquema**: las tablas de feedback/bitácora/checklist se crean solas; la
  columna `estado` se añade por migración ligera si la DB es antigua.
