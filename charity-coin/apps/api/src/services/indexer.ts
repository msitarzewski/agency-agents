import "dotenv/config";
import {
  createPublicClient,
  http,
  parseAbiItem,
  type Address,
  type Log,
} from "viem";
import { base } from "viem/chains";
import { db } from "../db/index.js";
import { causes, conversions, users } from "../db/schema.js";
import { eq, sql } from "drizzle-orm";

// ABI event signatures
const CONVERTED_EVENT = parseAbiItem(
  "event Converted(address indexed user, address indexed causeToken, uint256 chaAmount, uint256 causeTokenAmount, uint256 feeAmount)"
);

const FEES_DISTRIBUTED_EVENT = parseAbiItem(
  "event FeesDistributed(address indexed causeToken, uint256 charityAmount, uint256 treasuryAmount, uint256 burnAmount)"
);

const CAUSE_CREATED_EVENT = parseAbiItem(
  "event CauseCreated(bytes32 indexed causeId, address indexed tokenAddress, string name, string symbol, address charityWallet)"
);

let lastIndexedBlock = 0;

function getContracts(): {
  conversionEngine: Address;
  feeRouter: Address;
  causeTokenFactory: Address;
  rpcUrl: string;
} {
  const conversionEngine = process.env.CONVERSION_ENGINE_ADDRESS as Address;
  const feeRouter = process.env.FEE_ROUTER_ADDRESS as Address;
  const causeTokenFactory = process.env.CAUSE_TOKEN_FACTORY_ADDRESS as Address;
  const rpcUrl = process.env.BASE_RPC_URL || "https://mainnet.base.org";

  if (!conversionEngine || !feeRouter || !causeTokenFactory) {
    throw new Error(
      "Contract addresses must be set: CONVERSION_ENGINE_ADDRESS, FEE_ROUTER_ADDRESS, CAUSE_TOKEN_FACTORY_ADDRESS"
    );
  }

  return { conversionEngine, feeRouter, causeTokenFactory, rpcUrl };
}

/**
 * Handle a Converted event by upserting a conversion record and updating user stats.
 */
async function handleConvertedEvent(log: Log<bigint, number, false, typeof CONVERTED_EVENT>): Promise<void> {
  const { user, causeToken, chaAmount, causeTokenAmount, feeAmount } =
    log.args as {
      user: Address;
      causeToken: Address;
      chaAmount: bigint;
      causeTokenAmount: bigint;
      feeAmount: bigint;
    };

  const txHash = log.transactionHash!;
  const blockNumber = Number(log.blockNumber);
  const now = new Date();

  try {
    // Insert conversion record
    await db
      .insert(conversions)
      .values({
        userAddress: user.toLowerCase(),
        causeTokenAddress: causeToken.toLowerCase(),
        chaAmount: chaAmount.toString(),
        causeTokenAmount: causeTokenAmount.toString(),
        feeAmount: feeAmount.toString(),
        txHash,
        blockNumber,
        timestamp: now,
      })
      .onConflictDoNothing({ target: conversions.txHash });

    // Upsert user record
    await db
      .insert(users)
      .values({
        address: user.toLowerCase(),
        totalChaConverted: chaAmount.toString(),
        totalCausesSupported: 1,
        firstConversionAt: now,
        lastConversionAt: now,
      })
      .onConflictDoUpdate({
        target: users.address,
        set: {
          totalChaConverted: sql`${users.totalChaConverted}::numeric + ${chaAmount.toString()}::numeric`,
          lastConversionAt: now,
        },
      });

    // Update unique causes supported count for the user
    const causesCount = await db
      .select({
        count: sql<number>`COUNT(DISTINCT ${conversions.causeTokenAddress})::int`,
      })
      .from(conversions)
      .where(sql`LOWER(${conversions.userAddress}) = ${user.toLowerCase()}`);

    if (causesCount[0]) {
      await db
        .update(users)
        .set({ totalCausesSupported: causesCount[0].count })
        .where(eq(users.address, user.toLowerCase()));
    }

    console.log(
      `Indexed Converted event: user=${user}, causeToken=${causeToken}, chaAmount=${chaAmount}, tx=${txHash}`
    );
  } catch (err) {
    console.error("Error handling Converted event:", err);
  }
}

/**
 * Handle a CauseCreated event by inserting a new cause record.
 */
async function handleCauseCreatedEvent(log: Log<bigint, number, false, typeof CAUSE_CREATED_EVENT>): Promise<void> {
  const { causeId, tokenAddress, name, symbol, charityWallet } = log.args as {
    causeId: `0x${string}`;
    tokenAddress: Address;
    name: string;
    symbol: string;
    charityWallet: Address;
  };

  try {
    await db
      .insert(causes)
      .values({
        causeId: causeId,
        tokenAddress: tokenAddress.toLowerCase(),
        name,
        symbol,
        charityWallet: charityWallet.toLowerCase(),
        isActive: true,
      })
      .onConflictDoNothing();

    console.log(
      `Indexed CauseCreated event: causeId=${causeId}, name=${name}, token=${tokenAddress}`
    );
  } catch (err) {
    console.error("Error handling CauseCreated event:", err);
  }
}

/**
 * Handle FeesDistributed event (logging only for now).
 */
async function handleFeesDistributedEvent(log: Log<bigint, number, false, typeof FEES_DISTRIBUTED_EVENT>): Promise<void> {
  const { causeToken, charityAmount, treasuryAmount, burnAmount } =
    log.args as {
      causeToken: Address;
      charityAmount: bigint;
      treasuryAmount: bigint;
      burnAmount: bigint;
    };

  console.log(
    `Indexed FeesDistributed: causeToken=${causeToken}, charity=${charityAmount}, treasury=${treasuryAmount}, burn=${burnAmount}`
  );
}

/**
 * Process historical logs from a given block to the current block.
 */
async function processHistoricalLogs(
  client: ReturnType<typeof createPublicClient>,
  contracts: ReturnType<typeof getContracts>,
  fromBlock: bigint
): Promise<bigint> {
  const currentBlock = await client.getBlockNumber();

  if (fromBlock >= currentBlock) {
    return currentBlock;
  }

  // Process in chunks of 2000 blocks
  const chunkSize = 2000n;
  let start = fromBlock;

  while (start < currentBlock) {
    const end =
      start + chunkSize > currentBlock ? currentBlock : start + chunkSize;

    try {
      // Fetch Converted events
      const convertedLogs = await client.getLogs({
        address: contracts.conversionEngine,
        event: CONVERTED_EVENT,
        fromBlock: start,
        toBlock: end,
      });

      for (const log of convertedLogs) {
        await handleConvertedEvent(log);
      }

      // Fetch CauseCreated events
      const causeCreatedLogs = await client.getLogs({
        address: contracts.causeTokenFactory,
        event: CAUSE_CREATED_EVENT,
        fromBlock: start,
        toBlock: end,
      });

      for (const log of causeCreatedLogs) {
        await handleCauseCreatedEvent(log);
      }

      // Fetch FeesDistributed events
      const feesLogs = await client.getLogs({
        address: contracts.feeRouter,
        event: FEES_DISTRIBUTED_EVENT,
        fromBlock: start,
        toBlock: end,
      });

      for (const log of feesLogs) {
        await handleFeesDistributedEvent(log);
      }

      console.log(`Processed blocks ${start} to ${end}`);
    } catch (err) {
      console.error(`Error processing blocks ${start}-${end}:`, err);
      // Wait before retrying
      await new Promise((resolve) => setTimeout(resolve, 5000));
      continue;
    }

    start = end + 1n;
  }

  return currentBlock;
}

/**
 * Start the on-chain event indexer.
 * Processes historical events from the configured start block,
 * then watches for new events in real-time.
 */
export async function startIndexer(): Promise<void> {
  let contracts: ReturnType<typeof getContracts>;

  try {
    contracts = getContracts();
  } catch (err) {
    console.warn("Indexer not started:", (err as Error).message);
    return;
  }

  const client = createPublicClient({
    chain: base,
    transport: http(contracts.rpcUrl),
  });

  const startBlock = BigInt(process.env.INDEXER_START_BLOCK || "0");

  console.log(`Starting indexer from block ${startBlock}...`);

  // Process historical logs
  try {
    lastIndexedBlock = Number(
      await processHistoricalLogs(client, contracts, startBlock)
    );
    console.log(`Historical sync complete up to block ${lastIndexedBlock}`);
  } catch (err) {
    console.error("Error during historical sync:", err);
  }

  // Watch for new Converted events
  client.watchEvent({
    address: contracts.conversionEngine,
    event: CONVERTED_EVENT,
    onLogs: (logs) => {
      for (const log of logs) {
        handleConvertedEvent(log).catch((err) =>
          console.error("Error in Converted handler:", err)
        );
      }
    },
    onError: (err) => console.error("Converted event watch error:", err),
  });

  // Watch for new CauseCreated events
  client.watchEvent({
    address: contracts.causeTokenFactory,
    event: CAUSE_CREATED_EVENT,
    onLogs: (logs) => {
      for (const log of logs) {
        handleCauseCreatedEvent(log).catch((err) =>
          console.error("Error in CauseCreated handler:", err)
        );
      }
    },
    onError: (err) => console.error("CauseCreated event watch error:", err),
  });

  // Watch for new FeesDistributed events
  client.watchEvent({
    address: contracts.feeRouter,
    event: FEES_DISTRIBUTED_EVENT,
    onLogs: (logs) => {
      for (const log of logs) {
        handleFeesDistributedEvent(log).catch((err) =>
          console.error("Error in FeesDistributed handler:", err)
        );
      }
    },
    onError: (err) =>
      console.error("FeesDistributed event watch error:", err),
  });

  console.log("Event watchers started for real-time indexing");
}
