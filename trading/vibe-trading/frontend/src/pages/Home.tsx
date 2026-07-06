import { Link } from "react-router-dom";
import { ArrowRight, Bot, BarChart3, Zap, UserCircle2 } from "lucide-react";
import { useTranslation } from "react-i18next";

export function Home() {
  const { t } = useTranslation();

  const FEATURES = [
    { icon: Bot, title: t("home.featureAgent"), desc: t("home.featureAgentDesc") },
    { icon: BarChart3, title: t("home.featureBacktest"), desc: t("home.featureBacktestDesc") },
    { icon: Zap, title: t("home.featureStreaming"), desc: t("home.featureStreamingDesc") },
    { icon: UserCircle2, title: t("home.featureReplay"), desc: t("home.featureReplayDesc") },
  ];

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8">
      <div className="max-w-2xl text-center space-y-6">
        <h1 className="text-4xl font-bold tracking-tight">{t("home.title")}</h1>
        <p className="text-lg text-muted-foreground">{t("home.subtitle")}</p>
        <Link
          to="/agent"
          className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-primary text-primary-foreground font-medium hover:opacity-90 transition"
        >
          {t("home.startResearch")} <ArrowRight className="h-4 w-4" />
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-16 max-w-5xl w-full">
        {FEATURES.map(({ icon: Icon, title, desc }) => (
          <div key={title} className="border rounded-lg p-6 space-y-3">
            <Icon className="h-8 w-8 text-primary" />
            <h3 className="font-semibold">{title}</h3>
            <p className="text-sm text-muted-foreground">{desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
