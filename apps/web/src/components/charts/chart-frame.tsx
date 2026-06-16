"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";

type ChartFrameProps = {
  children: (size: { width: number; height: number }) => ReactNode;
};

const CHART_HEIGHT = 288;

export function ChartFrame({ children }: ChartFrameProps) {
  const frameRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(0);

  useEffect(() => {
    const element = frameRef.current;

    if (!element) {
      return;
    }

    const updateReady = () => {
      setWidth(element.clientWidth);
    };
    const observer = new ResizeObserver(updateReady);

    updateReady();
    observer.observe(element);

    return () => observer.disconnect();
  }, []);

  return (
    <div ref={frameRef} className="h-72 w-full min-w-0">
      {width > 0 ? (
        children({ width, height: CHART_HEIGHT })
      ) : (
        <div className="h-full w-full rounded-md bg-muted/20" />
      )}
    </div>
  );
}
