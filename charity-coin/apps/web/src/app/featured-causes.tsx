"use client";

import { CauseCard } from "@/components/causes/cause-card";
import { useCauses } from "@/hooks/useCauses";

export function FeaturedCauses() {
  const { causes } = useCauses();

  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {causes.map((cause) => (
        <CauseCard
          key={cause.symbol}
          name={cause.name}
          symbol={cause.symbol}
          description={cause.description}
          slug={cause.slug}
          totalRaised={cause.totalRaised}
          totalBurned={cause.totalBurned}
          goal={cause.goal}
          icon={cause.icon}
        />
      ))}
    </div>
  );
}
