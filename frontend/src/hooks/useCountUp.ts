import { useEffect, useRef, useState } from 'react';

export function useCountUp(target: number, duration = 900) {
  const [count, setCount] = useState(0);
  const prevTarget = useRef<number>(0);

  useEffect(() => {
    if (target === prevTarget.current) return;
    prevTarget.current = target;

    if (target === 0) {
      setCount(0);
      return;
    }

    const startTime = Date.now();
    const startVal = count;

    const tick = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // cubic ease-out
      const eased = 1 - Math.pow(1 - progress, 3);
      setCount(Math.round(startVal + (target - startVal) * eased));
      if (progress < 1) requestAnimationFrame(tick);
    };

    requestAnimationFrame(tick);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [target, duration]);

  return count;
}
