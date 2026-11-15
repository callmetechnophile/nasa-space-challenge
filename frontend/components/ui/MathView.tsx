"use client";

import React, { useMemo } from "react";
import katex from "katex";

interface MathViewProps {
  math: string;
  display?: boolean;
  className?: string;
  label?: string;
  caption?: string;
}

/**
 * MathView: Renders mathematical equations and expressions in Cambria Math.
 * Uses KaTeX to generate MathML and semantic HTML, styled with:
 * font-family: "Cambria Math", "STIX Two Math", "Latin Modern Math", serif;
 */
export function MathView({
  math,
  display = false,
  className = "",
  label,
  caption,
}: MathViewProps) {
  const renderedHtml = useMemo(() => {
    try {
      return katex.renderToString(math, {
        displayMode: display,
        throwOnError: false,
        output: "htmlAndMathml",
        strict: false,
      });
    } catch {
      return `<span class="math-fallback">${math}</span>`;
    }
  }, [math, display]);

  if (display) {
    return (
      <div className={`scientific-equation my-6 ${className}`}>
        <div className="flex items-center justify-between gap-4 overflow-x-auto py-2">
          <div
            className="math-display text-slate-100 flex-1 text-center"
            dangerouslySetInnerHTML={{ __html: renderedHtml }}
          />
          {label && (
            <span className="text-xs font-mono text-cyan-400 shrink-0 font-semibold px-2 py-1 rounded bg-slate-900/60 border border-slate-800">
              {label}
            </span>
          )}
        </div>
        {caption && (
          <div className="text-xs text-slate-400 mt-2 pt-2 border-t border-slate-800/60 font-mono">
            {caption}
          </div>
        )}
      </div>
    );
  }

  return (
    <span
      className={`math-inline align-baseline ${className}`}
      dangerouslySetInnerHTML={{ __html: renderedHtml }}
    />
  );
}

export function MathInline({ math, className = "" }: { math: string; className?: string }) {
  return <MathView math={math} display={false} className={className} />;
}

export function MathDisplay({
  math,
  label,
  caption,
  className = "",
}: {
  math: string;
  label?: string;
  caption?: string;
  className?: string;
}) {
  return <MathView math={math} display={true} label={label} caption={caption} className={className} />;
}
