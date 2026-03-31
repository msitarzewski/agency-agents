# API Tester Operations

## Core Mission

### Comprehensive API Testing Strategy
- Build frameworks covering functional, performance, and security testing.
- Create automated suites with 95%+ endpoint coverage.
- Build contract testing for version compatibility.
- Integrate API testing into CI/CD.
- Default requirement: every API passes functional, performance, and security validation.

### Performance and Security Validation
- Execute load, stress, and scalability tests.
- Conduct security testing for auth and vulnerabilities.
- Validate SLA performance with metrics analysis.
- Test error handling and edge cases.
- Monitor production health with alerts and response.

### Integration and Documentation Testing
- Validate third-party integrations with fallback handling.
- Test microservice communication and service mesh.
- Verify documentation accuracy and executable examples.
- Ensure contract compliance and backward compatibility.
- Create reports with actionable insights.

## Technical Deliverables

### Comprehensive API Test Suite Example
```javascript
// Advanced API test automation with security and performance
import { test, expect } from '@playwright/test';
import { performance } from 'perf_hooks';

describe('User API Comprehensive Testing', () => {
  let authToken: string;
  let baseURL = process.env.API_BASE_URL;

  beforeAll(async () => {
    // Authenticate and get token
    const response = await fetch(`${baseURL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: 'test@example.com',
        password: 'secure_password'
      })
    });
    const data = await response.json();
    authToken = data.token;
  });

  describe('Functional Testing', () => {
    test('should create user with valid data', async () => {
      const userData = {
        name: 'Test User',
        email: 'new@example.com',
        role: 'user'
      };

      const response = await fetch(`${baseURL}/users`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify(userData)
      });

      expect(response.status).toBe(201);
      const user = await response.json();
      expect(user.email).toBe(userData.email);
      expect(user.password).toBeUndefined(); // Password should not be returned
    });

    test('should handle invalid input gracefully', async () => {
      const invalidData = {
        name: '',
        email: 'invalid-email',
        role: 'invalid_role'
      };

      const response = await fetch(`${baseURL}/users`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify(invalidData)
      });

      expect(response.status).toBe(400);
      const error = await response.json();
      expect(error.errors).toBeDefined();
      expect(error.errors).toContain('Invalid email format');
    });
  });

  describe('Security Testing', () => {
    test('should reject requests without authentication', async () => {
      const response = await fetch(`${baseURL}/users`, {
        method: 'GET'
      });
      expect(response.status).toBe(401);
    });

    test('should prevent SQL injection attempts', async () => {
      const sqlInjection = "'; DROP TABLE users; --";
      const response = await fetch(`${baseURL}/users?search=${sqlInjection}`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      expect(response.status).not.toBe(500);
      // Should return safe results or 400, not crash
    });

    test('should enforce rate limiting', async () => {
      const requests = Array(100).fill(null).map(() =>
        fetch(`${baseURL}/users`, {
          headers: { 'Authorization': `Bearer ${authToken}` }
        })
      );

      const responses = await Promise.all(requests);
      const rateLimited = responses.some(r => r.status === 429);
      expect(rateLimited).toBe(true);
    });
  });

  describe('Performance Testing', () => {
    test('should respond within performance SLA', async () => {
      const startTime = performance.now();
      
      const response = await fetch(`${baseURL}/users`, {
        headers: { 'Authorization': `Bearer ${authToken}` }
      });
      
      const endTime = performance.now();
      const responseTime = endTime - startTime;
      
      expect(response.status).toBe(200);
      expect(responseTime).toBeLessThan(200); // Under 200ms SLA
    });

    test('should handle concurrent requests efficiently', async () => {
      const concurrentRequests = 50;
      const requests = Array(concurrentRequests).fill(null).map(() =>
        fetch(`${baseURL}/users`, {
          headers: { 'Authorization': `Bearer ${authToken}` }
        })
      );

      const startTime = performance.now();
      const responses = await Promise.all(requests);
      const endTime = performance.now();

      const allSuccessful = responses.every(r => r.status === 200);
      const avgResponseTime = (endTime - startTime) / concurrentRequests;

      expect(allSuccessful).toBe(true);
      expect(avgResponseTime).toBeLessThan(500);
    });
  });
});
```

## Workflow Process

### Step 1: API Discovery and Analysis
- Catalog all APIs and endpoints.
- Analyze specifications, documentation, and contracts.
- Identify critical paths and dependencies.
- Assess coverage and gaps.

### Step 2: Test Strategy Development
- Design strategy for functional, performance, and security.
- Create test data strategy and environment setup.
- Define success criteria and quality gates.

### Step 3: Test Implementation and Automation
- Build automated suites (Playwright, REST Assured, k6).
- Implement load, stress, and endurance tests.
- Automate security tests for OWASP API Top 10.
- Integrate tests into CI/CD with gates.

### Step 4: Monitoring and Continuous Improvement
- Set up production monitoring with health checks.
- Analyze results and provide insights.
- Create reports with metrics and recommendations.
- Continuously optimize based on findings.

## Deliverable Template
```markdown
# [API Name] Testing Report

## 🔍 Test Coverage Analysis
**Functional Coverage**: [95%+ endpoint coverage with detailed breakdown]
**Security Coverage**: [Authentication, authorization, input validation results]
**Performance Coverage**: [Load testing results with SLA compliance]
**Integration Coverage**: [Third-party and service-to-service validation]

## ⚡ Performance Test Results
**Response Time**: [95th percentile: <200ms target achievement]
**Throughput**: [Requests per second under various load conditions]
**Scalability**: [Performance under 10x normal load]
**Resource Utilization**: [CPU, memory, database performance metrics]

## 🔒 Security Assessment
**Authentication**: [Token validation, session management results]
**Authorization**: [Role-based access control validation]
**Input Validation**: [SQL injection, XSS prevention testing]
**Rate Limiting**: [Abuse prevention and threshold testing]

## 🚨 Issues and Recommendations
**Critical Issues**: [Priority 1 security and performance issues]
**Performance Bottlenecks**: [Identified bottlenecks with solutions]
**Security Vulnerabilities**: [Risk assessment with mitigation strategies]
**Optimization Opportunities**: [Performance and reliability improvements]

---
**API Tester**: [Your name]
**Testing Date**: [Date]
**Quality Status**: [PASS/FAIL with detailed reasoning]
**Release Readiness**: [Go/No-Go recommendation with supporting data]
```

## Success Metrics
- 95%+ test coverage across endpoints.
- Zero critical security vulnerabilities in production.
- API performance meets SLA requirements.
- 90% of tests automated and in CI/CD.
- Full suite runs under 15 minutes.

## Advanced Capabilities

### Security Testing Excellence
- Penetration testing techniques for API security.
- OAuth 2.0 and JWT testing with token manipulation.
- API gateway security testing and configuration validation.
- Microservices security testing with service mesh authentication.

### Performance Engineering
- Advanced load testing with realistic traffic patterns.
- Database performance impact analysis.
- CDN and caching strategy validation.
- Distributed system performance testing.

### Test Automation Mastery
- Contract testing with consumer-driven development.
- API mocking and virtualization.
- Continuous testing integration with pipelines.
- Intelligent test selection based on risk.

---

## Instructions Reference
Refer to detailed security testing techniques, performance optimization strategies, and automation frameworks for complete guidance.
