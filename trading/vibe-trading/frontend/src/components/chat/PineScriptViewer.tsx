import { useTranslation } from 'react-i18next';
import { memo, useState, useCallback } from "react";
import { X, Copy, Check, ExternalLink } from "lucide-react";

interface Props {
  code: string;
  onClose: () => void;
}

export const PineScriptViewer = memo(function PineScriptViewer({ code, onClose }: Props) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for older browsers
      const textarea = document.createElement("textarea");
      textarea.value = code;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }, [code]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm" onClick={onClose}>
      <div
        className="relative w-full max-w-3xl max-h-[80vh] mx-4 rounded-xl border bg-background shadow-2xl flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold">{t("pineViewer.pineScript")}</span>
            <span className="text-xs text-muted-foreground">strategy.pine</span>
          </div>
          <div className="flex items-center gap-1.5">
            <button
              onClick={handleCopy}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-primary text-primary-foreground hover:opacity-90 transition-opacity"
            >
              {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
              {copied ? t("pineViewer.copied") : t("pineViewer.copy")}
            </button>
            <a
              href="https://www.tradingview.com/pine-script-docs/welcome/"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 px-2 py-1.5 rounded-lg text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              <ExternalLink className="h-3 w-3" />
              {t("pineViewer.docs")}
            </a>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Code */}
        <div className="flex-1 overflow-auto p-4">
          <pre className="text-xs leading-relaxed font-mono whitespace-pre-wrap break-words text-foreground/90">
            {code}
          </pre>
        </div>

        {/* Footer */}
        <div className="px-4 py-2.5 border-t bg-muted/30">
          <p className="text-xs text-muted-foreground">
            {t("pineViewer.footer")}
          </p>
        </div>
      </div>
    </div>
  );
});
