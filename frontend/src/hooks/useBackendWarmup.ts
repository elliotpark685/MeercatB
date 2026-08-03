import { useEffect } from 'react';

import { warmupBackend } from '../api/health';

export function useBackendWarmup(): void {
  useEffect(() => {
    warmupBackend();
  }, []);
}
