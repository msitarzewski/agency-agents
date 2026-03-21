import { http, createConfig } from "wagmi";
import { base } from "wagmi/chains";
import { getDefaultConfig } from "@rainbow-me/rainbowkit";

const walletConnectProjectId =
  process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID || "";

export const config = getDefaultConfig({
  appName: "Charity Coin",
  projectId: walletConnectProjectId,
  chains: [base],
  transports: {
    [base.id]: http(
      process.env.NEXT_PUBLIC_BASE_RPC_URL || "https://mainnet.base.org"
    ),
  },
  ssr: true,
});

declare module "wagmi" {
  interface Register {
    config: typeof config;
  }
}
