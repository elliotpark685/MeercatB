import { apiClient } from './client';

let warmupRequested = false;

/** Starts the Render service without affecting authentication or application UI. */
export function warmupBackend(): void {
  if (import.meta.env.DEV || warmupRequested) return;

  warmupRequested = true;
  void apiClient.get('/api/v1/health', {
    timeout: 70_000,
    headers: { Authorization: undefined },
  }).catch(() => {
    // A warm-up is opportunistic: a failure must remain invisible to the user.
  });
}
