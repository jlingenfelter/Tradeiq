"use client";

import { useEffect, useRef, useState } from "react";

interface AnimatedCounterProps {
  value: number;
  prefix?: string;
  decimals?: number;
  duration?: number;
  className?: string;
}

function easeOutExpo(t: number): number {
  return t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
}

function formatWithCommas(n: number, decimals: number): string {
  const parts = n.toFixed(decimals).split(".");
  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return parts.join(".");
}

export function AnimatedCounter({
  value,
  prefix = "$",
  decimals = 0,
  duration = 1200,
  className = "",
}: AnimatedCounterProps) {
  const [display, setDisplay] = useState("0");
  const rafRef = useRef<number>(0);
  const startRef = useRef<number>(0);

  useEffect(() => {
    if (value === 0) {
      setDisplay(formatWithCommas(0, decimals));
      return;
    }

    const start = performance.now();
    startRef.current = start;

    function tick(now: number) {
      const elapsed = now - startRef.current;
      const progress = Math.min(elapsed / duration, 1);
      const easedProgress = easeOutExpo(progress);
      const current = easedProgress * value;

      setDisplay(formatWithCommas(current, decimals));

      if (progress < 1) {
        rafRef.current = requestAnimationFrame(tick);
      }
    }

    rafRef.current = requestAnimationFrame(tick);

    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
    };
  }, [value, decimals, duration]);

  return (
    <span className={className}>
      {prefix}{display}
    </span>
  );
}
