import { memo, useEffect, useState, useCallback } from "react";
import { cn } from "@/lib/utils";
import type { AgentMessage } from "@/types/agent";

interface Props {
  messages: AgentMessage[];
  containerRef: React.RefObject<HTMLDivElement | null>;
}

export const ConversationTimeline = memo(function ConversationTimeline({ messages, containerRef }: Props) {
  const [activeIdx, setActiveIdx] = useState(-1);

  const userIndices = messages
    .map((m, i) => m.type === "user" ? i : -1)
    .filter(i => i >= 0);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || userIndices.length === 0) return;

    const onScroll = () => {
      const rect = container.getBoundingClientRect();
      const mid = rect.top + rect.height / 2;
      let closest = userIndices[0];
      let minDist = Infinity;
      for (const idx of userIndices) {
        const el = container.querySelector(`[data-msg-idx="${idx}"]`);
        if (!el) continue;
        const elRect = el.getBoundingClientRect();
        const dist = Math.abs(elRect.top - mid);
        if (dist < minDist) { minDist = dist; closest = idx; }
      }
      setActiveIdx(closest);
    };

    container.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => container.removeEventListener("scroll", onScroll);
  }, [containerRef, userIndices]);

  const scrollTo = useCallback((idx: number) => {
    const container = containerRef.current;
    if (!container) return;
    const el = container.querySelector(`[data-msg-idx="${idx}"]`);
    if (el) el.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [containerRef]);

  if (userIndices.length < 2) return null;

  return (
    <div className="fixed right-3 top-1/2 -translate-y-1/2 h-2/3 flex flex-col justify-between items-center z-20 py-4">
      {userIndices.map((idx) => (
        <button
          key={idx}
          onClick={() => scrollTo(idx)}
          className={cn(
            "rounded-full transition-all shrink-0",
            idx === activeIdx
              ? "w-3 h-3 bg-primary shadow-sm shadow-primary/30"
              : "w-2 h-2 bg-muted-foreground/25 hover:bg-muted-foreground/50"
          )}
          title={messages[idx].content.slice(0, 40)}
        />
      ))}
    </div>
  );
});
