import { useTranslation } from "react-i18next";
import { Bot, TrendingUp, Globe, Sparkles, Users, UserCircle2, NotebookPen, Landmark } from "lucide-react";

interface Example {
  titleKey: string;
  descKey: string;
  promptKey: string;
}

interface Category {
  labelKey: string;
  icon: React.ReactNode;
  color: string;
  examples: Example[];
}

const CATEGORIES: Category[] = [
  {
    labelKey: "welcome.categories.multiMarketBacktest",
    icon: <TrendingUp className="h-4 w-4" />,
    color: "text-red-400 border-red-500/30 hover:border-red-500/60 hover:bg-red-500/5",
    examples: [
      {
        titleKey: "welcome.examples.crossMarketPortfolio",
        descKey: "welcome.examples.crossMarketPortfolioDesc",
        promptKey: "welcome.examples.crossMarketPortfolioPrompt",
      },
      {
        titleKey: "welcome.examples.btcMacd",
        descKey: "welcome.examples.btcMacdDesc",
        promptKey: "welcome.examples.btcMacdPrompt",
      },
      {
        titleKey: "welcome.examples.usTechMaxDiv",
        descKey: "welcome.examples.usTechMaxDivDesc",
        promptKey: "welcome.examples.usTechMaxDivPrompt",
      },
    ],
  },
  {
    labelKey: "welcome.categories.researchAnalysis",
    icon: <Sparkles className="h-4 w-4" />,
    color: "text-amber-400 border-amber-500/30 hover:border-amber-500/60 hover:bg-amber-500/5",
    examples: [
      {
        titleKey: "welcome.examples.multiFactorAlpha",
        descKey: "welcome.examples.multiFactorAlphaDesc",
        promptKey: "welcome.examples.multiFactorAlphaPrompt",
      },
      {
        titleKey: "welcome.examples.optionsGreeks",
        descKey: "welcome.examples.optionsGreeksDesc",
        promptKey: "welcome.examples.optionsGreeksPrompt",
      },
    ],
  },
  {
    labelKey: "welcome.categories.swarmTeams",
    icon: <Users className="h-4 w-4" />,
    color: "text-violet-400 border-violet-500/30 hover:border-violet-500/60 hover:bg-violet-500/5",
    examples: [
      {
        titleKey: "welcome.examples.investmentCommittee",
        descKey: "welcome.examples.investmentCommitteeDesc",
        promptKey: "welcome.examples.investmentCommitteePrompt",
      },
      {
        titleKey: "welcome.examples.quantStrategyDesk",
        descKey: "welcome.examples.quantStrategyDeskDesc",
        promptKey: "welcome.examples.quantStrategyDeskPrompt",
      },
    ],
  },
  {
    labelKey: "welcome.categories.docWebResearch",
    icon: <Globe className="h-4 w-4" />,
    color: "text-blue-400 border-blue-500/30 hover:border-blue-500/60 hover:bg-blue-500/5",
    examples: [
      {
        titleKey: "welcome.examples.earningsReport",
        descKey: "welcome.examples.earningsReportDesc",
        promptKey: "welcome.examples.earningsReportPrompt",
      },
      {
        titleKey: "welcome.examples.macroResearch",
        descKey: "welcome.examples.macroResearchDesc",
        promptKey: "welcome.examples.macroResearchPrompt",
      },
    ],
  },
  {
    labelKey: "welcome.categories.tradeJournal",
    icon: <NotebookPen className="h-4 w-4" />,
    color: "text-orange-400 border-orange-500/30 hover:border-orange-500/60 hover:bg-orange-500/5",
    examples: [
      {
        titleKey: "welcome.examples.analyzeBrokerExport",
        descKey: "welcome.examples.analyzeBrokerExportDesc",
        promptKey: "welcome.examples.analyzeBrokerExportPrompt",
      },
      {
        titleKey: "welcome.examples.diagnoseBehavior",
        descKey: "welcome.examples.diagnoseBehaviorDesc",
        promptKey: "welcome.examples.diagnoseBehaviorPrompt",
      },
    ],
  },
  {
    labelKey: "welcome.categories.tradingConnectors",
    icon: <Landmark className="h-4 w-4" />,
    color: "text-cyan-400 border-cyan-500/30 hover:border-cyan-500/60 hover:bg-cyan-500/5",
    examples: [
      {
        titleKey: "welcome.examples.checkConnector",
        descKey: "welcome.examples.checkConnectorDesc",
        promptKey: "welcome.examples.checkConnectorPrompt",
      },
      {
        titleKey: "welcome.examples.analyzePortfolio",
        descKey: "welcome.examples.analyzePortfolioDesc",
        promptKey: "welcome.examples.analyzePortfolioPrompt",
      },
      {
        titleKey: "welcome.examples.quoteTrend",
        descKey: "welcome.examples.quoteTrendDesc",
        promptKey: "welcome.examples.quoteTrendPrompt",
      },
    ],
  },
  {
    labelKey: "welcome.categories.shadowAccount",
    icon: <UserCircle2 className="h-4 w-4" />,
    color: "text-emerald-400 border-emerald-500/30 hover:border-emerald-500/60 hover:bg-emerald-500/5",
    examples: [
      {
        titleKey: "welcome.examples.trainShadow",
        descKey: "welcome.examples.trainShadowDesc",
        promptKey: "welcome.examples.trainShadowPrompt",
      },
      {
        titleKey: "welcome.examples.shadowDelta",
        descKey: "welcome.examples.shadowDeltaDesc",
        promptKey: "welcome.examples.shadowDeltaPrompt",
      },
      {
        titleKey: "welcome.examples.shadowReport",
        descKey: "welcome.examples.shadowReportDesc",
        promptKey: "welcome.examples.shadowReportPrompt",
      },
    ],
  },
];

const CAPABILITY_CHIP_KEYS = [
  "financeSkills",
  "swarmTeams",
  "autoTools",
  "markets",
  "connectors",
  "timeframes",
  "optimizers",
  "riskMetrics",
  "options",
  "pdfWeb",
  "factorML",
  "journalAnalyzer",
  "shadowBacktest",
  "memory",
  "sessionSearch",
];

interface Props {
  onExample: (s: string) => void;
}

export function WelcomeScreen({ onExample }: Props) {
  const { t } = useTranslation();
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-8 text-center">
      {/* Header */}
      <div className="space-y-3">
        <div className="h-16 w-16 mx-auto rounded-2xl bg-gradient-to-br from-primary/80 to-info/80 flex items-center justify-center shadow-lg">
          <Bot className="h-8 w-8 text-white" />
        </div>
        <div>
          <h2 className="text-2xl font-bold tracking-tight">{t('welcome.title')}</h2>
          <p className="text-xs text-muted-foreground mt-1 max-w-sm mx-auto leading-relaxed">
            {t('welcome.subtitle')}
          </p>
          <p className="text-sm text-muted-foreground mt-2 max-w-md leading-relaxed mx-auto">
            {t('welcome.describePrompt')}
          </p>
        </div>
      </div>

      {/* Capability chips */}
      <div className="flex flex-wrap justify-center gap-2 max-w-lg">
        {CAPABILITY_CHIP_KEYS.map((key) => (
          <span
            key={key}
            className="px-2.5 py-1 text-xs rounded-full border border-border/60 text-muted-foreground bg-muted/30"
          >
            {t(`welcome.capabilities.${key}`)}
          </span>
        ))}
      </div>

      {/* Example categories grid */}
      <div className="w-full max-w-2xl text-left space-y-4">
        <p className="text-xs text-muted-foreground px-1">{t('welcome.tryExample')}</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {CATEGORIES.map((cat) => (
            <div key={cat.labelKey} className="space-y-2">
              <div className={`flex items-center gap-1.5 text-xs font-medium px-1 ${cat.color.split(" ").filter(c => c.startsWith("text-")).join(" ")}`}>
                {cat.icon}
                <span>{t(cat.labelKey)}</span>
              </div>
              <div className="space-y-1.5">
                {cat.examples.map((ex) => (
                  <button
                    key={ex.titleKey}
                    onClick={() => onExample(t(ex.promptKey))}
                    className={`block w-full text-left px-3 py-2.5 rounded-xl border transition-colors ${cat.color}`}
                  >
                    <span className="text-sm font-medium text-foreground leading-snug">
                      {t(ex.titleKey)}
                    </span>
                    <span className="block text-xs text-muted-foreground mt-0.5 leading-snug">
                      {t(ex.descKey)}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
