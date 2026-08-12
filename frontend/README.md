# Frontend — Sports League Management UI

React 18 + Vite + Tailwind v3 + React Router v6 + TanStack Query v5 +
Zustand v5 + axios, per the Argo onboarding stack. See the root `README.md`
for the full three-part picture and the one-command Docker setup.

## Setup (manual, no Docker)

Requires the backend running first (see `../backend/README.md`).

```bash
npm install
cp .env.example .env       # VITE_API_BASE_URL, defaults to http://localhost:8020/api/v1
npm run dev
```

Open http://localhost:5173. The login page shows all six seeded demo
accounts as quick-pick buttons (password for all: `Password123!`).

## Project layout

```
src/
├── main.jsx, App.jsx        # entry point + router
├── index.css                 # Tailwind + small reusable component classes
├── lib/
│   ├── api.js                 # axios instance + per-resource endpoint wrappers
│   ├── permissions.js          # UI-side mirror of backend RBAC (display only)
│   └── statusMachines.js        # UI-side mirror of backend status transitions
├── store/
│   └── authStore.js              # JWT + role, persisted to localStorage
├── components/                    # Layout, DataTable, Modal, Badge, etc.
└── pages/                          # one file per nav item
```

## How auth works here

`POST /auth/login` returns a JWT + role. The token is stored in
`authStore` (persisted) and attached to every request by an axios
interceptor (`src/lib/api.js`). A 401 response anywhere logs the user out
automatically. `src/lib/permissions.js` mirrors the backend's RBAC matrix
so buttons the current role can't use don't render — but this is UI polish
only; the backend re-checks every permission on every request regardless.

## Build for production

```bash
npm run build      # outputs to dist/
npm run preview    # serve the production build locally
```

The Docker image currently runs the Vite **dev** server (fine for a module
demo). For a real deployment, switch `frontend/Dockerfile`'s `CMD` to build
+ serve `dist/` with nginx or similar.
