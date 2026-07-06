import { useTranslation } from 'react-i18next';
import { WifiOff, RefreshCw } from "lucide-react";
import type { SSEStatus } from "@/hooks/useSSE";

interface Props {
  status: SSEStatus;
  retryAttempt?: number;
}

export function ConnectionBanner({ status, retryAttempt }: Props) {
  const { t } = useTranslation();
  if (status === "connected" || status === "disconnected") return null;

  return (
    <div className="flex items-center gap-2 px-4 py-2 text-xs bg-warning/15 text-warning border-b border-warning/30">
      {status === "reconnecting" ? (
        <>
          <RefreshCw className="h-3.5 w-3.5 animate-spin" />
          <span>{t('connection.reconnecting', { attempt: retryAttempt || 1 })}</span>
        </>
      ) : (
        <>
          <WifiOff className="h-3.5 w-3.5" />
          <span>{t('connection.disconnected')}</span>
        </>
      )}
    </div>
  );
}
