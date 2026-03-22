import "dotenv/config";
import { db } from "./index.js";
import {
  causes,
  users,
  conversions,
  analyticsSnapshots,
} from "./schema.js";

// Realistic bytes32 cause IDs (keccak256 of the cause name)
const CAUSE_IDS = {
  HEALTH: "0x4c4577526f6e65206865616c7468000000000000000000000000000000000000",
  EDU:    "0x656475636174696f6e000000000000000000000000000000000000000000000000",
  ENV:    "0x656e7669726f6e6d656e7400000000000000000000000000000000000000000000",
  WATER:  "0x636c65616e5f776174657200000000000000000000000000000000000000000000",
  HUNGER: "0x68756e6765725f72656c696566000000000000000000000000000000000000000000",
};

const SAMPLE_CAUSES = [
  {
    causeId: CAUSE_IDS.HEALTH,
    tokenAddress: "0x1111111111111111111111111111111111111111",
    name: "Global Health Initiative",
    symbol: "ccHEALTH",
    description: "Fund healthcare access in underserved communities worldwide",
    charityWallet: "0xaaaa000000000000000000000000000000000001",
    isActive: true,
  },
  {
    causeId: CAUSE_IDS.EDU,
    tokenAddress: "0x2222222222222222222222222222222222222222",
    name: "Education for All",
    symbol: "ccEDU",
    description: "Provide quality education to children in developing nations",
    charityWallet: "0xaaaa000000000000000000000000000000000002",
    isActive: true,
  },
  {
    causeId: CAUSE_IDS.ENV,
    tokenAddress: "0x3333333333333333333333333333333333333333",
    name: "Environmental Protection",
    symbol: "ccENV",
    description: "Combat climate change through reforestation and carbon reduction",
    charityWallet: "0xaaaa000000000000000000000000000000000003",
    isActive: true,
  },
  {
    causeId: CAUSE_IDS.WATER,
    tokenAddress: "0x4444444444444444444444444444444444444444",
    name: "Clean Water Access",
    symbol: "ccWATER",
    description: "Build wells and water purification systems in water-scarce regions",
    charityWallet: "0xaaaa000000000000000000000000000000000004",
    isActive: true,
  },
  {
    causeId: CAUSE_IDS.HUNGER,
    tokenAddress: "0x5555555555555555555555555555555555555555",
    name: "Hunger Relief",
    symbol: "ccHUNGER",
    description: "Distribute food and build sustainable agriculture in famine-affected areas",
    charityWallet: "0xaaaa000000000000000000000000000000000005",
    isActive: true,
  },
];

const SAMPLE_USERS = [
  {
    address: "0xd8da6bf26964af9d7eed9e03e53415d37aa96045",
    totalChaConverted: "50000000000000000000000",
    totalCausesSupported: 3,
    firstConversionAt: new Date("2025-01-15T10:00:00Z"),
    lastConversionAt: new Date("2025-03-10T14:30:00Z"),
  },
  {
    address: "0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
    totalChaConverted: "12000000000000000000000",
    totalCausesSupported: 2,
    firstConversionAt: new Date("2025-02-01T08:00:00Z"),
    lastConversionAt: new Date("2025-03-08T20:15:00Z"),
  },
  {
    address: "0xab5801a7d398351b8be11c439e05c5b3259aec9b",
    totalChaConverted: "85000000000000000000000",
    totalCausesSupported: 5,
    firstConversionAt: new Date("2025-01-02T06:00:00Z"),
    lastConversionAt: new Date("2025-03-12T11:45:00Z"),
  },
  {
    address: "0xca8fa8f0b631ecdb18cda619c4fc9d197c8affca",
    totalChaConverted: "3000000000000000000000",
    totalCausesSupported: 1,
    firstConversionAt: new Date("2025-03-01T16:00:00Z"),
    lastConversionAt: new Date("2025-03-01T16:00:00Z"),
  },
];

const SAMPLE_CONVERSIONS = [
  {
    userAddress: "0xd8da6bf26964af9d7eed9e03e53415d37aa96045",
    causeTokenAddress: "0x1111111111111111111111111111111111111111",
    chaAmount: "10000000000000000000000",
    causeTokenAmount: "9700000000000000000000",
    feeAmount: "300000000000000000000",
    txHash: "0xaaa1111111111111111111111111111111111111111111111111111111111111",
    blockNumber: 20000100,
    timestamp: new Date("2025-01-15T10:00:00Z"),
  },
  {
    userAddress: "0xd8da6bf26964af9d7eed9e03e53415d37aa96045",
    causeTokenAddress: "0x2222222222222222222222222222222222222222",
    chaAmount: "20000000000000000000000",
    causeTokenAmount: "19400000000000000000000",
    feeAmount: "600000000000000000000",
    txHash: "0xaaa2222222222222222222222222222222222222222222222222222222222222",
    blockNumber: 20000200,
    timestamp: new Date("2025-02-10T12:00:00Z"),
  },
  {
    userAddress: "0x71c7656ec7ab88b098defb751b7401b5f6d8976f",
    causeTokenAddress: "0x3333333333333333333333333333333333333333",
    chaAmount: "5000000000000000000000",
    causeTokenAmount: "4850000000000000000000",
    feeAmount: "150000000000000000000",
    txHash: "0xbbb1111111111111111111111111111111111111111111111111111111111111",
    blockNumber: 20000300,
    timestamp: new Date("2025-02-01T08:00:00Z"),
  },
  {
    userAddress: "0xab5801a7d398351b8be11c439e05c5b3259aec9b",
    causeTokenAddress: "0x4444444444444444444444444444444444444444",
    chaAmount: "30000000000000000000000",
    causeTokenAmount: "29100000000000000000000",
    feeAmount: "900000000000000000000",
    txHash: "0xccc1111111111111111111111111111111111111111111111111111111111111",
    blockNumber: 20000400,
    timestamp: new Date("2025-01-02T06:00:00Z"),
  },
  {
    userAddress: "0xca8fa8f0b631ecdb18cda619c4fc9d197c8affca",
    causeTokenAddress: "0x5555555555555555555555555555555555555555",
    chaAmount: "3000000000000000000000",
    causeTokenAmount: "2910000000000000000000",
    feeAmount: "90000000000000000000",
    txHash: "0xddd1111111111111111111111111111111111111111111111111111111111111",
    blockNumber: 20000500,
    timestamp: new Date("2025-03-01T16:00:00Z"),
  },
];

const SAMPLE_ANALYTICS = [
  {
    timestamp: new Date("2025-01-31T23:59:59Z"),
    totalChaBurned: "40000000000000000000000",
    totalCharityRaised: "38800000000000000000000",
    totalConversions: 12,
    activeCauses: 3,
  },
  {
    timestamp: new Date("2025-02-28T23:59:59Z"),
    totalChaBurned: "95000000000000000000000",
    totalCharityRaised: "92150000000000000000000",
    totalConversions: 34,
    activeCauses: 5,
  },
  {
    timestamp: new Date("2025-03-12T23:59:59Z"),
    totalChaBurned: "150000000000000000000000",
    totalCharityRaised: "145500000000000000000000",
    totalConversions: 58,
    activeCauses: 5,
  },
];

async function seed() {
  console.log("Seeding database...\n");

  // Seed causes
  const insertedCauses = await db
    .insert(causes)
    .values(SAMPLE_CAUSES)
    .onConflictDoNothing()
    .returning({ id: causes.id, name: causes.name });
  console.log(`Causes seeded: ${insertedCauses.length} inserted`);

  // Seed users
  const insertedUsers = await db
    .insert(users)
    .values(SAMPLE_USERS)
    .onConflictDoNothing()
    .returning({ id: users.id, address: users.address });
  console.log(`Users seeded: ${insertedUsers.length} inserted`);

  // Seed conversions
  const insertedConversions = await db
    .insert(conversions)
    .values(SAMPLE_CONVERSIONS)
    .onConflictDoNothing()
    .returning({ id: conversions.id });
  console.log(`Conversions seeded: ${insertedConversions.length} inserted`);

  // Seed analytics snapshots
  const insertedAnalytics = await db
    .insert(analyticsSnapshots)
    .values(SAMPLE_ANALYTICS)
    .onConflictDoNothing()
    .returning({ id: analyticsSnapshots.id });
  console.log(`Analytics snapshots seeded: ${insertedAnalytics.length} inserted`);

  console.log("\nSeed complete!");
  process.exit(0);
}

seed().catch((err) => {
  console.error("Seed failed:", err);
  process.exit(1);
});
