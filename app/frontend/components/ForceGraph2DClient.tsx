"use client";

import { forwardRef, useEffect, useRef } from "react";
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
  const internalRef = useRef<any>();

  useEffect(() => {
    const instance = internalRef.current ?? null;

    if (typeof onEngineRef === "function") {
      onEngineRef(instance);
    }

    if (typeof ref === "function") {
      ref(instance);
    } else if (ref && typeof ref === "object") {
      (ref as any).current = instance;
    }
  }, [onEngineRef, ref]);

  // Bind through an internal mutable ref and mirror it outward so parent
  // controls (zoom/center/fit) still work across dynamic() boundaries.
  return <ForceGraph2D {...rest} ref={internalRef as any} />;
});

export default ForceGraph2DClient;
