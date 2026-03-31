# Feishu Integration Developer Operations

## Mission
### Feishu Bot Development
- Custom bots: Webhook-based message push bots.
- App bots: Interactive bots built on Feishu apps, supporting commands, conversations, and card callbacks.
- Message types: text, rich text, images, files, interactive message cards.
- Group management: bot joining groups, @bot triggers, group event listeners.
- Default requirement: all bots must implement graceful degradation with friendly error messages on API failures.

### Message Cards and Interactions
- Message card templates using the Card Builder tool or raw JSON.
- Card callbacks for button clicks, dropdown selections, and date picker events.
- Card updates via `message_id`.
- Template messages for reusable card designs.

### Approval Workflow Integration
- Approval definitions via API.
- Approval instances for submit/query/reminders.
- Approval events to drive downstream business logic.
- Approval callbacks for external system triggers.

### Bitable (Multidimensional Spreadsheets)
- Create, query, update, and delete table records.
- Manage custom field types and configuration.
- Create/switch views, filtering, and sorting.
- Bidirectional data sync with external databases or ERP.

### SSO and Identity Authentication
- OAuth 2.0 authorization code flow for web auto-login.
- OIDC integration with enterprise IdPs.
- Feishu QR code login for third-party websites.
- User info synchronization via contact event subscriptions and org sync.

### Feishu Mini Programs
- Use Feishu Mini Program APIs and component library.
- JSAPI calls for user info, geolocation, file selection.
- Account for container differences, API availability, and publishing workflow.
- Offline capabilities and data caching.

## Deliverables
### Feishu App Project Structure
```
feishu-integration/
├── src/
│   ├── config/
│   │   ├── feishu.ts              # Feishu app configuration
│   │   └── env.ts                 # Environment variable management
│   ├── auth/
│   │   ├── token-manager.ts       # Token retrieval and caching
│   │   └── event-verify.ts        # Event subscription verification
│   ├── bot/
│   │   ├── command-handler.ts     # Bot command handler
│   │   ├── message-sender.ts      # Message sending wrapper
│   │   └── card-builder.ts        # Message card builder
│   ├── approval/
│   │   ├── approval-define.ts     # Approval definition management
│   │   ├── approval-instance.ts   # Approval instance operations
│   │   └── approval-callback.ts   # Approval event callbacks
│   ├── bitable/
│   │   ├── table-client.ts        # Bitable CRUD operations
│   │   └── sync-service.ts        # Data synchronization service
│   ├── sso/
│   │   ├── oauth-handler.ts       # OAuth authorization flow
│   │   └── user-sync.ts           # User info synchronization
│   ├── webhook/
│   │   ├── event-dispatcher.ts    # Event dispatcher
│   │   └── handlers/              # Event handlers by type
│   └── utils/
│       ├── http-client.ts         # HTTP request wrapper
│       ├── logger.ts              # Logging utility
│       └── retry.ts               # Retry mechanism
├── tests/
├── docker-compose.yml
└── package.json
```

### Token Management and API Request Wrapper
```typescript
// src/auth/token-manager.ts
import * as lark from '@larksuiteoapi/node-sdk';

const client = new lark.Client({
  appId: process.env.FEISHU_APP_ID!,
  appSecret: process.env.FEISHU_APP_SECRET!,
  disableTokenCache: false, // SDK built-in caching
});

export { client };

// Manual token management scenario (when not using the SDK)
class TokenManager {
  private token: string = '';
  private expireAt: number = 0;

  async getTenantAccessToken(): Promise<string> {
    if (this.token && Date.now() < this.expireAt) {
      return this.token;
    }

    const resp = await fetch(
      'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          app_id: process.env.FEISHU_APP_ID,
          app_secret: process.env.FEISHU_APP_SECRET,
        }),
      }
    );

    const data = await resp.json();
    if (data.code !== 0) {
      throw new Error(`Failed to obtain token: ${data.msg}`);
    }

    this.token = data.tenant_access_token;
    // Expire 5 minutes early to avoid boundary issues
    this.expireAt = Date.now() + (data.expire - 300) * 1000;
    return this.token;
  }
}

export const tokenManager = new TokenManager();
```

### Message Card Builder and Sender
```typescript
// src/bot/card-builder.ts
interface CardAction {
  tag: string;
  text: { tag: string; content: string };
  type: string;
  value: Record<string, string>;
}

// Build an approval notification card
function buildApprovalCard(params: {
  title: string;
  applicant: string;
  reason: string;
  amount: string;
  instanceId: string;
}): object {
  return {
    config: { wide_screen_mode: true },
    header: { title: { tag: 'plain_text', content: params.title } },
    elements: [
      { tag: 'div', text: { tag: 'lark_md', content: `**Applicant**: ${params.applicant}` } },
      { tag: 'div', text: { tag: 'lark_md', content: `**Reason**: ${params.reason}` } },
      { tag: 'div', text: { tag: 'lark_md', content: `**Amount**: ${params.amount}` } },
      {
        tag: 'action',
        actions: [
          {
            tag: 'button',
            text: { tag: 'plain_text', content: 'View Approval' },
            type: 'primary',
            value: { instanceId: params.instanceId },
          } as CardAction,
        ],
      },
    ],
  };
}
```

### Event Subscription and Callback Handling
```typescript
// src/webhook/event-dispatcher.ts
import * as lark from '@larksuiteoapi/node-sdk';
import express from 'express';

const app = express();
const eventDispatcher = new lark.EventDispatcher({
  encryptKey: process.env.FEISHU_ENCRYPT_KEY!,
  verificationToken: process.env.FEISHU_VERIFICATION_TOKEN!,
});

app.post('/feishu/events', (req, res) => {
  eventDispatcher.handleEvent(req, res, async (event) => {
    const { header, event: eventData } = event;

    // Example: Handle approval instance status change
    if (header.event_type === 'approval_instance.status_change') {
      await handleApprovalEvent(eventData);
    }
  });
});
```

### Bitable Operations
```typescript
// src/bitable/table-client.ts
class BitableClient {
  constructor(private client: any) {}

  // Query table records (with filtering and pagination)
  async queryRecords(appToken: string, tableId: string, filter: string) {
    return this.client.bitable.appTableRecord.search({
      path: { app_token: appToken, table_id: tableId },
      data: { filter },
    });
  }

  // Add record
  async addRecord(appToken: string, tableId: string, fields: any) {
    return this.client.bitable.appTableRecord.create({
      path: { app_token: appToken, table_id: tableId },
      data: { fields },
    });
  }
}
```

### Approval Workflow Integration
```typescript
// src/approval/approval-instance.ts
// Create an approval instance via API
async function createApprovalInstance(params: {
  approvalCode: string;
  userId: string;
  form: Array<any>;
}) {
  return client.approval.v4.instance.create({
    data: {
      approval_code: params.approvalCode,
      user_id: params.userId,
      form: params.form,
    },
  });
}
```

### SSO QR Code Login
```typescript
// src/sso/oauth-handler.ts
import { Router } from 'express';
const router = Router();

// Step 1: Redirect to Feishu authorization page
router.get('/feishu/login', (req, res) => {
  const redirectUri = encodeURIComponent(process.env.FEISHU_REDIRECT_URI!);
  const url = `https://open.feishu.cn/open-apis/authen/v1/index?app_id=${process.env.FEISHU_APP_ID}&redirect_uri=${redirectUri}&state=123`;
  res.redirect(url);
});

// Step 2: Handle callback
router.get('/feishu/callback', async (req, res) => {
  const code = req.query.code;

  const tokenResp = await client.authen.accessToken.create({
    data: {
      grant_type: 'authorization_code',
      code: code as string,
    },
  });

  if (tokenResp.code !== 0) {
    return res.status(401).json({ error: 'Authorization failed' });
  }

  const userToken = tokenResp.data!.access_token;

  // Step 3: Retrieve user info
  const userResp = await client.authen.userInfo.get({
    headers: { Authorization: `Bearer ${userToken}` },
  });

  const feishuUser = userResp.data;
  // Bind or create a local user linked to the Feishu user
  const localUser = await bindOrCreateUser({
    openId: feishuUser!.open_id!,
    unionId: feishuUser!.union_id!,
    name: feishuUser!.name!,
    email: feishuUser!.email!,
    avatar: feishuUser!.avatar_url!,
  });

  const jwt = signJwt({ userId: localUser.id });
  res.redirect(`${process.env.FRONTEND_URL}/auth?token=${jwt}`);
});

export default router;
```

## Workflow
### Step 1: Requirements Analysis and App Planning
- Map out business scenarios and determine which Feishu capability modules need integration.
- Create an app on the Feishu Open Platform, choosing the app type (enterprise self-built app vs. ISV app).
- Plan the required permission scopes and list all needed API scopes.
- Evaluate whether event subscriptions, card interactions, approval integration, or other capabilities are needed.

### Step 2: Authentication and Infrastructure Setup
- Configure app credentials and secrets management strategy.
- Implement token retrieval and caching mechanisms.
- Set up the Webhook service, configure the event subscription URL, and complete verification.
- Deploy to a publicly accessible environment (or use tunneling tools like ngrok for local development).

### Step 3: Core Feature Development
- Implement integration modules in priority order (bot > notifications > approvals > data sync).
- Preview and validate message cards in the Card Builder tool before going live.
- Implement idempotency and error compensation for event handling.
- Connect with enterprise internal systems to complete the data flow loop.

### Step 4: Testing and Launch
- Verify each API using the Feishu Open Platform API debugger.
- Test event callback reliability: duplicate delivery, out-of-order events, delayed events.
- Least privilege check: remove excess permissions requested during development.
- Publish the app version and configure the availability scope (all employees / specific departments).
- Set up monitoring alerts: token retrieval failures, API call errors, event processing timeouts.

## Done Criteria
- API call success rate > 99.5%.
- Event processing latency < 2 seconds from Feishu push to business processing completion.
- Message card rendering success rate of 100% (validated in the Card Builder before release).
- Token cache hit rate > 95% to avoid unnecessary token requests.
- Approval workflow end-to-end time reduced by 50%+ versus manual operations.
- Data sync tasks run with zero data loss and automatic error compensation.
