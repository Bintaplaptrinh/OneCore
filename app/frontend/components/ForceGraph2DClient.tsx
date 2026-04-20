"use client";

import { forwardRef, useCallback } from "react";
// eslint-disable-next-line @typescript-eslint/no-var-requires
import ForceGraph2D from "react-force-graph-2d";

/**
 * Client-only wrapper around `react-force-graph-2d` that *explicitly* forwards
 * the imperative ref through Next.js' `dynamic()` boundary.
 *
 * Why this exists:
 * `next/dynamic(() => import("react-force-graph-2d"), { ssr: false })` does
 * not always forward refs through to the underlying forwardRef component in
 * the App Router, so `fgRef.current.zoom()` ends up undefined and zoom
 * controls silently fail. Wrapping the component in our own `forwardRef`
 * ensures the ref always points at the live ForceGraph instance.
 */
const ForceGraph2DClient = forwardRef<any, any>(function ForceGraph2DClient(
  props,
  ref
) {
  const { onEngineRef, ...rest } = props;

  const bindRef = useCallback(
    (instance: any | null) => {
      if (typeof onEngineRef === "function") {
        onEngineRef(instance);
      }
      if (typeof ref === "function") {
        ref(instance);
      } else if (ref && typeof ref === "object") {
        (ref as any).current = instance;
      }
    },
    [onEngineRef, ref]
  );

  // We bind instance through a callback ref so parent can still control zoom
  // even when dynamic() does not forward the ref reliably.
  return <ForceGraph2D {...rest} ref={bindRef} />;
});

export default ForceGraph2DClient;
