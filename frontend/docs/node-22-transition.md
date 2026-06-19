# Node 22 Transition Guide

This frontend is standardized on Node 22. Keep local development and Vercel on the same major version.

## Current pins

- [`frontend/package.json`](../package.json) sets `engines.node` to `22.x`.
- [`frontend/.nvmrc`](../.nvmrc) points to Node 22 for local version managers.

## Local migration steps

1. Install a Node 22 runtime with your version manager of choice.
2. Switch the `frontend` workspace to Node 22.
3. Verify the active runtime:

```powershell
node -v
```

4. Reinstall dependencies after the runtime switch:

```powershell
cd frontend
Remove-Item -Recurse -Force node_modules
npm install
```

5. Start the app again:

```powershell
npm run dev
```

## Vercel alignment

- Keep the Vercel project root pointed at `frontend`.
- Keep the project Node.js version at `22.x`.
- If you raise Node later, update these files together:
  - [`frontend/package.json`](../package.json)
  - [`frontend/.nvmrc`](../.nvmrc)

## Quick check

```powershell
node -v
npm run build
```

The build should complete under Node 22 before you merge any dependency changes.
