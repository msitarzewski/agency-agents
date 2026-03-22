# Charity Coin -- API Reference

**Base URL**: `http://localhost:3001/api`

All responses are JSON. Timestamps are ISO 8601 strings. Token amounts are returned as decimal strings (wei precision). The API uses Redis-based response caching; cache TTLs are noted per section.

---

## Table of Contents

1. [Health Check](#health-check)
2. [Causes](#causes)
3. [Analytics](#analytics)
4. [User](#user)
5. [Admin](#admin)
6. [Error Handling](#error-handling)

---

## Health Check

### `GET /api/health`

Returns the API server status.

**Cache**: None

**Response** `200 OK`

```json
{
  "status": "ok",
  "timestamp": "2026-03-22T12:00:00.000Z"
}
```

---

## Causes

All cause endpoints are cached with a **30-second TTL**.

### `GET /api/causes`

List all active causes with metadata and analytics.

**Response** `200 OK`

```json
{
  "causes": [
    {
      "id": 1,
      "causeId": "0xabc123...",
      "tokenAddress": "0x1234...abcd",
      "name": "CharityCoin Health",
      "symbol": "chHEALTH",
      "description": "Supporting healthcare access and medical research worldwide",
      "charityWallet": "0x5678...ef01",
      "isActive": true,
      "createdAt": "2026-03-01T00:00:00.000Z",
      "analytics": {
        "totalRaised": "150000000000000000000000",
        "totalBurned": "2850000000000000000000000",
        "supporterCount": 342,
        "totalConversions": 1205
      }
    }
  ]
}
```

---

### `GET /api/causes/:id`

Get a single cause by its `causeId` with detailed analytics.

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | The `causeId` (bytes32 hex string) |

**Response** `200 OK`

```json
{
  "cause": {
    "id": 1,
    "causeId": "0xabc123...",
    "tokenAddress": "0x1234...abcd",
    "name": "CharityCoin Health",
    "symbol": "chHEALTH",
    "description": "Supporting healthcare access and medical research worldwide",
    "charityWallet": "0x5678...ef01",
    "isActive": true,
    "createdAt": "2026-03-01T00:00:00.000Z",
    "analytics": {
      "totalRaised": "150000000000000000000000",
      "totalBurned": "2850000000000000000000000",
      "uniqueSupporters": 342,
      "totalConversions": 1205
    }
  }
}
```

**Response** `404 Not Found`

```json
{
  "error": "Cause not found"
}
```

---

### `GET /api/causes/:id/leaderboard`

Top 50 converters for a specific cause, sorted by total conversion amount.

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | The `causeId` (bytes32 hex string) |

**Response** `200 OK`

```json
{
  "causeId": "0xabc123...",
  "leaderboard": [
    {
      "address": "0xuser1...abcd",
      "totalAmount": "50000000000000000000000",
      "conversionCount": 15
    },
    {
      "address": "0xuser2...ef01",
      "totalAmount": "25000000000000000000000",
      "conversionCount": 8
    }
  ]
}
```

**Response** `404 Not Found`

```json
{
  "error": "Cause not found"
}
```

---

### `GET /api/causes/:id/conversions`

Recent conversions for a cause, paginated.

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | The `causeId` (bytes32 hex string) |

**Query Parameters**

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `page` | integer | 1 | -- | Page number |
| `limit` | integer | 20 | 100 | Results per page |

**Response** `200 OK`

```json
{
  "causeId": "0xabc123...",
  "conversions": [
    {
      "id": 1,
      "userAddress": "0xuser1...abcd",
      "causeTokenAddress": "0x1234...abcd",
      "chaAmount": "1000000000000000000000",
      "causeTokenAmount": "950000000000000000000",
      "feeAmount": "50000000000000000000",
      "txHash": "0xtx123...",
      "blockNumber": 12345678,
      "timestamp": "2026-03-20T14:30:00.000Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1205,
    "totalPages": 61
  }
}
```

**Response** `404 Not Found`

```json
{
  "error": "Cause not found"
}
```

---

## Analytics

All analytics endpoints are cached with a **60-second TTL**.

### `GET /api/analytics/overview`

Platform-wide statistics.

**Response** `200 OK`

```json
{
  "totalChaBurned": "95000000000000000000000000",
  "totalRaisedForCharity": "2500000000000000000000000",
  "totalConversions": 15420,
  "activeCauses": 5,
  "volume24h": "1200000000000000000000000"
}
```

---

### `GET /api/analytics/cause/:id`

Cause-specific analytics including 30-day daily volume.

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | The `causeId` (bytes32 hex string) |

**Response** `200 OK`

```json
{
  "causeId": "0xabc123...",
  "causeName": "CharityCoin Health",
  "totalRaised": "150000000000000000000000",
  "totalBurned": "2850000000000000000000000",
  "uniqueSupporters": 342,
  "totalConversions": 1205,
  "dailyVolume": [
    {
      "date": "2026-03-20",
      "volume": "45000000000000000000000"
    },
    {
      "date": "2026-03-19",
      "volume": "38000000000000000000000"
    }
  ]
}
```

**Response** `404 Not Found`

```json
{
  "error": "Cause not found"
}
```

---

### `GET /api/analytics/chart/burns`

Time-series data of CHA burned per day. Used for charting.

**Query Parameters**

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `days` | integer | 90 | 365 | Number of days of history |

**Response** `200 OK`

```json
{
  "period": "90 days",
  "data": [
    {
      "date": "2026-03-20",
      "burned": "500000000000000000000000"
    },
    {
      "date": "2026-03-19",
      "burned": "420000000000000000000000"
    }
  ]
}
```

---

### `GET /api/analytics/chart/conversions`

Time-series data of conversion volume per day. Used for charting.

**Query Parameters**

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `days` | integer | 90 | 365 | Number of days of history |

**Response** `200 OK`

```json
{
  "period": "90 days",
  "data": [
    {
      "date": "2026-03-20",
      "conversions": 85,
      "volume": "520000000000000000000000"
    },
    {
      "date": "2026-03-19",
      "conversions": 72,
      "volume": "440000000000000000000000"
    }
  ]
}
```

---

## User

All user endpoints are cached with a **15-second TTL**.

### `GET /api/user/:address/portfolio`

User's aggregated conversion stats and per-cause breakdown.

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `address` | string | Ethereum address (case-insensitive) |

**Response** `200 OK` (user found)

```json
{
  "address": "0xuser1...abcd",
  "totalChaConverted": "75000000000000000000000",
  "totalCausesSupported": 3,
  "firstConversionAt": "2026-03-05T10:15:00.000Z",
  "lastConversionAt": "2026-03-20T14:30:00.000Z",
  "causeBreakdown": [
    {
      "causeTokenAddress": "0x1234...abcd",
      "totalChaAmount": "50000000000000000000000",
      "totalCauseTokenAmount": "47500000000000000000000",
      "conversionCount": 12,
      "lastConversion": "2026-03-20T14:30:00.000Z",
      "causeName": "CharityCoin Health",
      "causeSymbol": "chHEALTH",
      "causeId": "0xabc123..."
    },
    {
      "causeTokenAddress": "0x5678...ef01",
      "totalChaAmount": "25000000000000000000000",
      "totalCauseTokenAmount": "23750000000000000000000",
      "conversionCount": 5,
      "lastConversion": "2026-03-18T09:00:00.000Z",
      "causeName": "CharityCoin Education",
      "causeSymbol": "chEDU",
      "causeId": "0xdef456..."
    }
  ]
}
```

**Response** `200 OK` (user not found -- returns empty portfolio)

```json
{
  "address": "0xnewuser...1234",
  "totalChaConverted": "0",
  "totalCausesSupported": 0,
  "firstConversionAt": null,
  "lastConversionAt": null,
  "causeBreakdown": []
}
```

---

### `GET /api/user/:address/history`

Paginated transaction history for a user, enriched with cause metadata.

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `address` | string | Ethereum address (case-insensitive) |

**Query Parameters**

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `page` | integer | 1 | -- | Page number |
| `limit` | integer | 20 | 100 | Results per page |

**Response** `200 OK`

```json
{
  "address": "0xuser1...abcd",
  "history": [
    {
      "id": 42,
      "causeTokenAddress": "0x1234...abcd",
      "chaAmount": "1000000000000000000000",
      "causeTokenAmount": "950000000000000000000",
      "feeAmount": "50000000000000000000",
      "txHash": "0xtx123...",
      "blockNumber": 12345678,
      "timestamp": "2026-03-20T14:30:00.000Z",
      "causeName": "CharityCoin Health",
      "causeSymbol": "chHEALTH",
      "causeId": "0xabc123..."
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 17,
    "totalPages": 1
  }
}
```

---

## Admin

All admin endpoints require API key authentication via the `X-API-Key` header (or as configured in the `adminAuth` middleware). There is no response caching on admin routes.

### `POST /api/admin/causes`

Register a new cause in the off-chain database. This is typically called after the cause has been created on-chain via the CauseTokenFactory.

**Headers**

| Header | Required | Description |
|--------|----------|-------------|
| `X-API-Key` | Yes | Admin API key |
| `Content-Type` | Yes | `application/json` |

**Request Body**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `causeId` | string | Yes | The bytes32 causeId from the on-chain CauseTokenFactory |
| `tokenAddress` | string | Yes | Deployed CauseToken contract address |
| `name` | string | Yes | Human-readable cause name |
| `symbol` | string | Yes | ERC-20 token symbol |
| `description` | string | No | Cause description (defaults to empty string) |
| `charityWallet` | string | Yes | Charity wallet address |

**Response** `201 Created`

```json
{
  "cause": {
    "id": 6,
    "causeId": "0xnew456...",
    "tokenAddress": "0xnewtok...1234",
    "name": "CharityCoin Animals",
    "symbol": "chANIMAL",
    "description": "Supporting animal welfare organizations",
    "charityWallet": "0xcharity...5678",
    "isActive": true,
    "createdAt": "2026-03-22T12:00:00.000Z"
  }
}
```

**Response** `400 Bad Request`

```json
{
  "error": "Validation failed",
  "details": {
    "fieldErrors": {
      "causeId": ["causeId is required"]
    },
    "formErrors": []
  }
}
```

**Response** `409 Conflict`

```json
{
  "error": "Cause with this causeId already exists"
}
```

---

### `PATCH /api/admin/causes/:id`

Update cause metadata. Only the provided fields are updated.

**Headers**

| Header | Required | Description |
|--------|----------|-------------|
| `X-API-Key` | Yes | Admin API key |
| `Content-Type` | Yes | `application/json` |

**Path Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | string | The `causeId` (bytes32 hex string) |

**Request Body** (all fields optional, at least one required)

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Updated cause name |
| `description` | string | Updated description |
| `isActive` | boolean | Enable or disable the cause |

**Response** `200 OK`

```json
{
  "cause": {
    "id": 1,
    "causeId": "0xabc123...",
    "tokenAddress": "0x1234...abcd",
    "name": "CharityCoin Health - Updated",
    "symbol": "chHEALTH",
    "description": "Updated description",
    "charityWallet": "0x5678...ef01",
    "isActive": true,
    "createdAt": "2026-03-01T00:00:00.000Z"
  }
}
```

**Response** `400 Bad Request`

```json
{
  "error": "No fields to update"
}
```

**Response** `404 Not Found`

```json
{
  "error": "Cause not found"
}
```

---

### `GET /api/admin/stats`

Admin dashboard statistics covering conversions, causes, users, and 24-hour activity.

**Headers**

| Header | Required | Description |
|--------|----------|-------------|
| `X-API-Key` | Yes | Admin API key |

**Response** `200 OK`

```json
{
  "conversions": {
    "total": 15420,
    "totalChaBurned": "95000000000000000000000000",
    "totalFeesCollected": "5000000000000000000000000",
    "uniqueUsers": 2340
  },
  "causes": {
    "total": 5,
    "active": 5
  },
  "users": {
    "total": 2340
  },
  "last24h": {
    "conversions": 85,
    "volume": "1200000000000000000000000"
  }
}
```

---

## Error Handling

All error responses follow a consistent format:

```json
{
  "error": "Human-readable error message"
}
```

Validation errors include additional detail:

```json
{
  "error": "Validation failed",
  "details": {
    "fieldErrors": { ... },
    "formErrors": [ ... ]
  }
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| `200` | Success |
| `201` | Created (new resource) |
| `400` | Bad request (validation error or missing fields) |
| `401` | Unauthorized (missing or invalid API key on admin routes) |
| `404` | Resource not found |
| `409` | Conflict (duplicate resource) |
| `500` | Internal server error |

### 404 Handler

Any request to an undefined route returns:

```json
{
  "error": "Not found"
}
```
