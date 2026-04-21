"use client";

import { useEffect, useRef, useState } from "react";
import { useTranslations } from "next-intl";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  type EnrichActionResult,
  type EnrichSession,
  type GapItem,
  markGapNA,
  respondToEnrich,
  skipGap,
  startEnrichSession,
} from "@/lib/api/enrich";

interface Message {
  role: "assistant" | "user";
  content: string;
}

export interface EnrichmentDrawerProps {
  open: boolean;
  scope?: string;
  onClose: () => void;
}

export function EnrichmentDrawer({ open, scope, onClose }: EnrichmentDrawerProps) {
  const t = useTranslations("enrich");
  const [session, setSession] = useState<EnrichSession | null>(null);
  const [gaps, setGaps] = useState<GapItem[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    setSession(null);
    setGaps([]);
    setMessages([]);
    setAnswer("");
    setDone(false);
    setError("");
    setLoading(true);

    startEnrichSession(scope)
      .then((s) => {
        setSession(s);
        setGaps(s.gaps);
        setMessages([{ role: "assistant", content: s.first_question }]);
      })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Error"))
      .finally(() => setLoading(false));
  }, [open, scope]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const applyResult = (
    result: EnrichActionResult,
    userMessage?: string
  ) => {
    setGaps(result.gaps);
    if (result.done) {
      setDone(true);
      return;
    }
    if (userMessage) {
      setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    }
    if (result.next_question) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: result.next_question! },
      ]);
    }
  };

  const handleSend = async () => {
    if (!session || !answer.trim()) return;
    const text = answer.trim();
    setAnswer("");
    setLoading(true);
    try {
      const result = await respondToEnrich(session.session_id, text);
      applyResult(result, text);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error");
    } finally {
      setLoading(false);
    }
  };

  const handleSkip = async () => {
    if (!session) return;
    setLoading(true);
    try {
      const result = await skipGap(session.session_id);
      applyResult(result);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error");
    } finally {
      setLoading(false);
    }
  };

  const handleNA = async () => {
    if (!session) return;
    setLoading(true);
    try {
      const result = await markGapNA(session.session_id);
      applyResult(result);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error");
    } finally {
      setLoading(false);
    }
  };

  const statusColor: Record<GapItem["status"], string> = {
    pending: "text-muted-foreground",
    active: "text-primary font-medium",
    done: "text-green-500",
    na: "text-muted-foreground line-through",
    skipped: "text-muted-foreground",
  };

  return (
    <Sheet open={open} onOpenChange={(v) => !v && onClose()}>
      <SheetContent
        side="right"
        className="w-[90vw] sm:w-[600px] md:w-[700px] p-0 flex flex-col"
      >
        <SheetHeader className="px-4 py-3 border-b shrink-0">
          <SheetTitle className="text-sm">
            {t("title")}
            {scope && (
              <span className="ml-2 text-xs text-muted-foreground font-normal">
                {scope.split(":").slice(1).join(" @ ")}
              </span>
            )}
          </SheetTitle>
        </SheetHeader>

        {loading && !session && (
          <div className="flex-1 flex items-center justify-center text-muted-foreground text-sm">
            {t("loading")}
          </div>
        )}

        {error && (
          <div className="flex-1 flex items-center justify-center text-destructive text-sm px-4">
            {error}
          </div>
        )}

        {done && (
          <div className="flex-1 flex flex-col items-center justify-center gap-4 text-center px-8">
            <div className="text-2xl">&#10003;</div>
            <p className="text-sm font-medium">{t("done")}</p>
            <Button variant="outline" onClick={onClose}>{t("close")}</Button>
          </div>
        )}

        {session && !done && !error && (
          <div className="flex flex-1 min-h-0">
            {/* Gap list */}
            <div className="w-44 shrink-0 border-r overflow-y-auto p-3 flex flex-col gap-1">
              <p className="text-[10px] uppercase tracking-wide text-muted-foreground mb-2">
                {t("gaps")}
              </p>
              {gaps.map((g) => (
                <div
                  key={g.id}
                  className={cn(
                    "text-xs rounded px-2 py-1.5 leading-tight",
                    g.status === "active" && "bg-primary/10",
                    statusColor[g.status]
                  )}
                >
                  {g.label}
                </div>
              ))}
            </div>

            {/* Chat panel */}
            <div className="flex-1 flex flex-col min-h-0">
              <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
                {messages.map((m, i) => (
                  <div
                    key={i}
                    className={cn(
                      "max-w-[85%] rounded-lg px-3 py-2 text-sm leading-relaxed",
                      m.role === "assistant"
                        ? "self-start bg-muted border-l-2 border-primary"
                        : "self-end bg-primary/10 text-right"
                    )}
                  >
                    {m.content}
                  </div>
                ))}
                <div ref={chatEndRef} />
              </div>

              {/* Input area */}
              <div className="shrink-0 border-t p-3 flex flex-col gap-2">
                <textarea
                  className="w-full resize-none rounded-md border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring min-h-[72px]"
                  placeholder={t("placeholder")}
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) handleSend();
                  }}
                  disabled={loading}
                />
                <div className="flex justify-between items-center">
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-xs h-7"
                      onClick={handleSkip}
                      disabled={loading}
                    >
                      {t("skip")}
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-xs h-7 text-muted-foreground"
                      onClick={handleNA}
                      disabled={loading}
                    >
                      {t("markNA")}
                    </Button>
                  </div>
                  <Button
                    size="sm"
                    onClick={handleSend}
                    disabled={loading || !answer.trim()}
                  >
                    {loading ? t("sending") : t("send")}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}
