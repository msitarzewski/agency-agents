// ============================================================
// Contract Addresses (Base Mainnet) - Replace with deployed addresses
// ============================================================

export const CONTRACT_ADDRESSES = {
  CharityCoin: "0x0000000000000000000000000000000000000001" as `0x${string}`,
  ConversionEngine:
    "0x0000000000000000000000000000000000000002" as `0x${string}`,
  CauseTokenFactory:
    "0x0000000000000000000000000000000000000003" as `0x${string}`,
  FeeRouter: "0x0000000000000000000000000000000000000004" as `0x${string}`,
} as const;

// ============================================================
// Cause Token Addresses (placeholder)
// ============================================================

export const CAUSE_TOKEN_ADDRESSES: Record<string, `0x${string}`> = {
  HEALTH: "0x0000000000000000000000000000000000000010",
  EDU: "0x0000000000000000000000000000000000000011",
  ENV: "0x0000000000000000000000000000000000000012",
  WATER: "0x0000000000000000000000000000000000000013",
  HUNGER: "0x0000000000000000000000000000000000000014",
};

// ============================================================
// ABIs (simplified for frontend use)
// ============================================================

export const CHARITY_COIN_ABI = [
  {
    type: "function",
    name: "balanceOf",
    inputs: [{ name: "account", type: "address" }],
    outputs: [{ name: "", type: "uint256" }],
    stateMutability: "view",
  },
  {
    type: "function",
    name: "totalSupply",
    inputs: [],
    outputs: [{ name: "", type: "uint256" }],
    stateMutability: "view",
  },
  {
    type: "function",
    name: "approve",
    inputs: [
      { name: "spender", type: "address" },
      { name: "amount", type: "uint256" },
    ],
    outputs: [{ name: "", type: "bool" }],
    stateMutability: "nonpayable",
  },
  {
    type: "function",
    name: "allowance",
    inputs: [
      { name: "owner", type: "address" },
      { name: "spender", type: "address" },
    ],
    outputs: [{ name: "", type: "uint256" }],
    stateMutability: "view",
  },
  {
    type: "function",
    name: "decimals",
    inputs: [],
    outputs: [{ name: "", type: "uint8" }],
    stateMutability: "view",
  },
  {
    type: "function",
    name: "symbol",
    inputs: [],
    outputs: [{ name: "", type: "string" }],
    stateMutability: "view",
  },
  {
    type: "function",
    name: "name",
    inputs: [],
    outputs: [{ name: "", type: "string" }],
    stateMutability: "view",
  },
  {
    type: "function",
    name: "totalBurned",
    inputs: [],
    outputs: [{ name: "", type: "uint256" }],
    stateMutability: "view",
  },
] as const;

export const CONVERSION_ENGINE_ABI = [
  {
    type: "function",
    name: "convert",
    inputs: [
      { name: "causeToken", type: "address" },
      { name: "chaAmount", type: "uint256" },
    ],
    outputs: [],
    stateMutability: "nonpayable",
  },
  {
    type: "function",
    name: "getConversionBreakdown",
    inputs: [{ name: "chaAmount", type: "uint256" }],
    outputs: [
      { name: "burnAmount", type: "uint256" },
      { name: "charityFee", type: "uint256" },
      { name: "liquidityFee", type: "uint256" },
      { name: "opsFee", type: "uint256" },
      { name: "causeTokensOut", type: "uint256" },
    ],
    stateMutability: "view",
  },
  {
    type: "function",
    name: "totalConversions",
    inputs: [],
    outputs: [{ name: "", type: "uint256" }],
    stateMutability: "view",
  },
  {
    type: "event",
    name: "Conversion",
    inputs: [
      { name: "user", type: "address", indexed: true },
      { name: "causeToken", type: "address", indexed: true },
      { name: "chaAmount", type: "uint256", indexed: false },
      { name: "causeTokensReceived", type: "uint256", indexed: false },
      { name: "chaBurned", type: "uint256", indexed: false },
    ],
  },
] as const;

export const CAUSE_TOKEN_FACTORY_ABI = [
  {
    type: "function",
    name: "getCauseCount",
    inputs: [],
    outputs: [{ name: "", type: "uint256" }],
    stateMutability: "view",
  },
  {
    type: "function",
    name: "getCauseByIndex",
    inputs: [{ name: "index", type: "uint256" }],
    outputs: [
      { name: "tokenAddress", type: "address" },
      { name: "name", type: "string" },
      { name: "symbol", type: "string" },
      { name: "charityWallet", type: "address" },
      { name: "isActive", type: "bool" },
    ],
    stateMutability: "view",
  },
  {
    type: "function",
    name: "createCauseToken",
    inputs: [
      { name: "name", type: "string" },
      { name: "symbol", type: "string" },
      { name: "charityWallet", type: "address" },
    ],
    outputs: [{ name: "tokenAddress", type: "address" }],
    stateMutability: "nonpayable",
  },
  {
    type: "function",
    name: "owner",
    inputs: [],
    outputs: [{ name: "", type: "address" }],
    stateMutability: "view",
  },
] as const;

export const FEE_ROUTER_ABI = [
  {
    type: "function",
    name: "charityFeeBps",
    inputs: [],
    outputs: [{ name: "", type: "uint256" }],
    stateMutability: "view",
  },
  {
    type: "function",
    name: "liquidityFeeBps",
    inputs: [],
    outputs: [{ name: "", type: "uint256" }],
    stateMutability: "view",
  },
  {
    type: "function",
    name: "opsFeeBps",
    inputs: [],
    outputs: [{ name: "", type: "uint256" }],
    stateMutability: "view",
  },
  {
    type: "function",
    name: "totalFeesCollected",
    inputs: [],
    outputs: [{ name: "", type: "uint256" }],
    stateMutability: "view",
  },
] as const;

export const CAUSE_TOKEN_ABI = [
  {
    type: "function",
    name: "balanceOf",
    inputs: [{ name: "account", type: "address" }],
    outputs: [{ name: "", type: "uint256" }],
    stateMutability: "view",
  },
  {
    type: "function",
    name: "totalSupply",
    inputs: [],
    outputs: [{ name: "", type: "uint256" }],
    stateMutability: "view",
  },
  {
    type: "function",
    name: "symbol",
    inputs: [],
    outputs: [{ name: "", type: "string" }],
    stateMutability: "view",
  },
  {
    type: "function",
    name: "name",
    inputs: [],
    outputs: [{ name: "", type: "string" }],
    stateMutability: "view",
  },
  {
    type: "function",
    name: "decimals",
    inputs: [],
    outputs: [{ name: "", type: "uint8" }],
    stateMutability: "view",
  },
] as const;
