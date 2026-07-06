import i18n from "@/i18n";
import { Component, type ReactNode } from "react";
import { AlertTriangle } from "lucide-react";

interface Props { children: ReactNode; fallback?: ReactNode; }
interface State { hasError: boolean; error?: Error; }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback ?? (
        <div className="flex items-center gap-2 p-4 rounded-lg border border-destructive/30 bg-destructive/5 text-sm text-destructive">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <span>{this.state.error?.message || i18n.t("errorBoundary.somethingWrong")}</span>
        </div>
      );
    }
    return this.props.children;
  }
}
