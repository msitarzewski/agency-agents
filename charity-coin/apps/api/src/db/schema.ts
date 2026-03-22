import {
  pgTable,
  serial,
  text,
  numeric,
  integer,
  timestamp,
  boolean,
  uniqueIndex,
  index,
} from "drizzle-orm/pg-core";

export const causes = pgTable(
  "causes",
  {
    id: serial("id").primaryKey(),
    causeId: text("cause_id").notNull(), // bytes32 hex string
    tokenAddress: text("token_address").notNull(),
    name: text("name").notNull(),
    symbol: text("symbol").notNull(),
    description: text("description").notNull().default(""),
    charityWallet: text("charity_wallet").notNull(),
    createdAt: timestamp("created_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
    isActive: boolean("is_active").notNull().default(true),
  },
  (table) => [
    uniqueIndex("causes_cause_id_idx").on(table.causeId),
    uniqueIndex("causes_token_address_idx").on(table.tokenAddress),
  ]
);

export const conversions = pgTable(
  "conversions",
  {
    id: serial("id").primaryKey(),
    userAddress: text("user_address").notNull(),
    causeTokenAddress: text("cause_token_address").notNull(),
    chaAmount: numeric("cha_amount", { precision: 78, scale: 0 }).notNull(),
    causeTokenAmount: numeric("cause_token_amount", {
      precision: 78,
      scale: 0,
    }).notNull(),
    feeAmount: numeric("fee_amount", { precision: 78, scale: 0 })
      .notNull()
      .default("0"),
    txHash: text("tx_hash").notNull(),
    blockNumber: integer("block_number").notNull(),
    timestamp: timestamp("timestamp", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (table) => [
    index("conversions_user_address_idx").on(table.userAddress),
    index("conversions_cause_token_address_idx").on(table.causeTokenAddress),
    index("conversions_timestamp_idx").on(table.timestamp),
    uniqueIndex("conversions_tx_hash_idx").on(table.txHash),
  ]
);

export const users = pgTable(
  "users",
  {
    id: serial("id").primaryKey(),
    address: text("address").notNull(),
    totalChaConverted: numeric("total_cha_converted", {
      precision: 78,
      scale: 0,
    })
      .notNull()
      .default("0"),
    totalCausesSupported: integer("total_causes_supported").notNull().default(0),
    firstConversionAt: timestamp("first_conversion_at", {
      withTimezone: true,
    }),
    lastConversionAt: timestamp("last_conversion_at", { withTimezone: true }),
  },
  (table) => [uniqueIndex("users_address_idx").on(table.address)]
);

export const analyticsSnapshots = pgTable(
  "analytics_snapshots",
  {
    id: serial("id").primaryKey(),
    timestamp: timestamp("timestamp", { withTimezone: true })
      .notNull()
      .defaultNow(),
    totalChaBurned: numeric("total_cha_burned", { precision: 78, scale: 0 })
      .notNull()
      .default("0"),
    totalCharityRaised: numeric("total_charity_raised", {
      precision: 78,
      scale: 0,
    })
      .notNull()
      .default("0"),
    totalConversions: integer("total_conversions").notNull().default(0),
    activeCauses: integer("active_causes").notNull().default(0),
  },
  (table) => [index("analytics_snapshots_timestamp_idx").on(table.timestamp)]
);

export const governanceProposals = pgTable(
  "governance_proposals",
  {
    id: serial("id").primaryKey(),
    proposalId: text("proposal_id").notNull(), // on-chain proposal ID
    title: text("title").notNull(),
    description: text("description").notNull().default(""),
    proposer: text("proposer").notNull(),
    status: text("status").notNull().default("pending"),
    votesFor: numeric("votes_for", { precision: 78, scale: 0 })
      .notNull()
      .default("0"),
    votesAgainst: numeric("votes_against", { precision: 78, scale: 0 })
      .notNull()
      .default("0"),
    startBlock: integer("start_block").notNull(),
    endBlock: integer("end_block").notNull(),
    createdAt: timestamp("created_at", { withTimezone: true })
      .notNull()
      .defaultNow(),
  },
  (table) => [
    uniqueIndex("governance_proposals_proposal_id_idx").on(table.proposalId),
  ]
);

// Type exports for use in application code
export type Cause = typeof causes.$inferSelect;
export type NewCause = typeof causes.$inferInsert;
export type Conversion = typeof conversions.$inferSelect;
export type NewConversion = typeof conversions.$inferInsert;
export type User = typeof users.$inferSelect;
export type NewUser = typeof users.$inferInsert;
export type AnalyticsSnapshot = typeof analyticsSnapshots.$inferSelect;
export type GovernanceProposal = typeof governanceProposals.$inferSelect;
