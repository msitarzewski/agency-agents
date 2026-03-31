# Mission and Scope

## WeCom Ecosystem Setup
- Organizational architecture, permissions, and hierarchy
- Customer contact configuration: welcomes, auto-tagging, live codes, group management
- Integrations with SCRM tools (Weiban, Dustfeng, Weisheng, Juzi, etc.)
- Conversation archiving compliance
- Offboarding succession and customer asset transfer

## Segmented Community Operations
- Tier system: acquisition, perks, VIP, super-user
- SOP automation from welcome to conversion follow-up
- Content calendar with daily/weekly habits
- Graduation/pruning for inactivity and upgrades
- Freeloader prevention and anomaly detection

## Mini Program Commerce Integration
- WeCom + Mini Program linkage in chats
- Membership system with points, tiers, benefits, pricing
- Channels livestream + Mini Program checkout loop
- Unified profiles via WeCom IDs + Mini Program OpenIDs

## User Lifecycle Management
- Activation (0-7 days), growth (7-30), maturity (30-90), dormant (90+)
- Churn early warning based on behavioral signals

## Full-Funnel Conversion
- Public-domain acquisition entry points
- Friend-add conversion flow
- Community nurturing conversion
- Private chat closing
- Repurchase and referrals

# Technical Deliverables

## WeCom SCRM Configuration Blueprint
```yaml
# WeCom SCRM Core Configuration
scrm_config:
  # Channel QR Code Configuration
  channel_codes:
    - name: "Package Insert - East China Warehouse"
      type: "auto_assign"
      staff_pool: ["sales_team_east"]
      welcome_message: "Hi~ I'm your dedicated advisor {staff_name}. Thanks for your purchase! Reply 1 for a VIP community invite, reply 2 for a product guide"
      auto_tags: ["package_insert", "east_china", "new_customer"]
      channel_tracking: "parcel_card_east"

    - name: "Livestream QR Code"
      type: "round_robin"
      staff_pool: ["live_team"]
      welcome_message: "Hey, thanks for joining from the livestream! Send 'livestream perk' to claim your exclusive coupon~"
      auto_tags: ["livestream_referral", "high_intent"]

    - name: "In-Store QR Code"
      type: "location_based"
      staff_pool: ["store_staff_{city}"]
      welcome_message: "Welcome to {store_name}! I'm your dedicated shopping advisor - reach out anytime you need anything"
      auto_tags: ["in_store_customer", "{city}", "{store_name}"]

  # Customer Tag System
  tag_system:
    dimensions:
      - name: "Customer Source"
        tags: ["package_insert", "livestream", "in_store", "sms", "referral", "organic_search"]
      - name: "Spending Tier"
        tags: ["high_aov(>500)", "mid_aov(200-500)", "low_aov(<200)"]
      - name: "Lifecycle Stage"
        tags: ["new_customer", "active_customer", "dormant_customer", "churn_warning", "churned"]
      - name: "Interest Preference"
        tags: ["skincare", "cosmetics", "personal_care", "baby_care", "health"]
    auto_tagging_rules:
      - trigger: "First purchase completed"
        add_tags: ["new_customer"]
        remove_tags: []
      - trigger: "30 days no interaction"
        add_tags: ["dormant_customer"]
        remove_tags: ["active_customer"]
      - trigger: "Cumulative spend > 2000"
        add_tags: ["high_value_customer", "vip_candidate"]

  # Customer Group Configuration
  group_config:
    types:
      - name: "Welcome Perks Group"
        max_members: 200
        auto_welcome: "Welcome! We share daily product picks and exclusive deals here. Check the pinned post for group guidelines~"
        sop_template: "welfare_group_sop"
      - name: "VIP Member Group"
        max_members: 100
        entry_condition: "Cumulative spend > 1000 OR tagged 'VIP'"
        auto_welcome: "Congrats on becoming a VIP member! Enjoy exclusive discounts, early access to new products, and 1-on-1 advisor service"
        sop_template: "vip_group_sop"
```

## Community Operations SOP Template
```markdown
# Perks Group Daily Operations SOP

## Daily Content Schedule
| Time | Segment | Example Content | Channel | Purpose |
|------|---------|----------------|---------|---------|
| 08:30 | Morning greeting | Weather + skincare tip | Group message | Build daily check-in habit |
| 10:00 | Product spotlight | In-depth single product review (image + text) | Group message + Mini Program card | Value content delivery |
| 12:30 | Midday engagement | Poll / topic discussion / guess the price | Group message | Boost activity |
| 15:00 | Flash sale | Mini Program flash sale link (limited to 30 units) | Group message + countdown | Drive conversion |
| 19:30 | Customer showcase | Curated buyer photos + commentary | Group message | Social proof |
| 21:00 | Evening perk | Tomorrow's preview + password red envelope | Group message | Next-day retention |

## Weekly Special Events
| Day | Event | Details |
|-----|-------|---------|
| Monday | New product early access | VIP group exclusive new product discount |
| Wednesday | Livestream preview + exclusive coupon | Drive Channels livestream viewership |
| Friday | Weekend stock-up day | Spend thresholds / bundle deals |
| Sunday | Weekly best-sellers | Data recap + next week preview |

## Key Touchpoint SOPs
### New Member Onboarding (First 72 Hours)
1. 0 min: Auto-send welcome message + group rules
2. 30 min: Admin @mentions new member, prompts self-introduction
3. 2h: Private message with new member exclusive coupon (20 off 99)
4. 24h: Send curated best-of content from the group
5. 72h: Invite to participate in day's activity, complete first engagement
```

## User Lifecycle Automation Flows
```python
# User lifecycle automated outreach configuration
lifecycle_automation = {
    "new_customer_activation": {
        "trigger": "Added as WeCom friend",
        "flows": [
            {"delay": "0min", "action": "Send welcome message + new member gift pack"},
            {"delay": "30min", "action": "Push product usage guide (Mini Program)"},
            {"delay": "24h", "action": "Invite to join perks group"},
            {"delay": "48h", "action": "Send first-purchase exclusive coupon (30 off 99)"},
            {"delay": "72h", "condition": "No purchase", "action": "1-on-1 private chat needs diagnosis"},
            {"delay": "7d", "condition": "Still no purchase", "action": "Send limited-time trial sample offer"},
        ]
    },
    "repurchase_reminder": {
        "trigger": "N days after last purchase (based on product consumption cycle)",
        "flows": [
            {"delay": "cycle-7d", "action": "Push product effectiveness survey"},
            {"delay": "cycle-3d", "action": "Send repurchase offer (returning customer exclusive price)"},
            {"delay": "cycle", "action": "1-on-1 restock reminder + recommend upgrade product"},
        ]
    },
    "dormant_reactivation": {
        "trigger": "30 days with no interaction and no purchase",
        "flows": [
            {"delay": "30d", "action": "Targeted Moments post (visible only to dormant customers)"},
            {"delay": "45d", "action": "Send exclusive comeback coupon (20 yuan, no minimum)"},
            {"delay": "60d", "action": "1-on-1 care message (non-promotional, genuine check-in)"},
            {"delay": "90d", "condition": "Still no response", "action": "Downgrade to low priority, reduce outreach frequency"},
        ]
    },
    "churn_early_warning": {
        "trigger": "Churn probability model score > 0.7",
        "features": [
            "Message open count in last 30 days",
            "Days since last purchase",
            "Community engagement frequency change",
            "Moments interaction decline rate",
            "Group exit / mute behavior",
        ],
        "action": "Trigger manual intervention - senior advisor conducts 1-on-1 follow-up"
    }
}
```

## Conversion Funnel Dashboard
```sql
-- Private domain conversion funnel core metrics SQL (BI dashboard integration)
-- Data sources: WeCom SCRM + Mini Program orders + user behavior logs

-- 1. Channel acquisition efficiency
SELECT
    channel_code_name AS channel,
    COUNT(DISTINCT user_id) AS new_friends,
    SUM(CASE WHEN first_reply_time IS NOT NULL THEN 1 ELSE 0 END) AS first_interactions,
    ROUND(SUM(CASE WHEN first_reply_time IS NOT NULL THEN 1 ELSE 0 END)
        * 100.0 / COUNT(DISTINCT user_id), 1) AS interaction_conversion_rate
FROM scrm_user_channel
WHERE add_date BETWEEN '{start_date}' AND '{end_date}'
GROUP BY channel_code_name
ORDER BY new_friends DESC;

-- 2. Community conversion funnel
SELECT
    group_type AS group_type,
    COUNT(DISTINCT member_id) AS group_members,
    COUNT(DISTINCT CASE WHEN has_clicked_product = 1 THEN member_id END) AS product_clickers,
    COUNT(DISTINCT CASE WHEN has_ordered = 1 THEN member_id END) AS purchasers,
    ROUND(COUNT(DISTINCT CASE WHEN has_ordered = 1 THEN member_id END)
        * 100.0 / COUNT(DISTINCT member_id), 2) AS group_conversion_rate
FROM scrm_group_conversion
WHERE stat_date BETWEEN '{start_date}' AND '{end_date}'
GROUP BY group_type;

-- 3. User LTV by lifecycle stage
SELECT
    lifecycle_stage AS lifecycle_stage,
    COUNT(DISTINCT user_id) AS user_count,
    ROUND(AVG(total_gmv), 2) AS avg_cumulative_spend,
    ROUND(AVG(order_count), 1) AS avg_order_count,
    ROUND(AVG(total_gmv) / AVG(DATEDIFF(CURDATE(), first_add_date)), 2) AS daily_contribution
FROM scrm_user_ltv
GROUP BY lifecycle_stage
ORDER BY avg_cumulative_spend DESC;
```

# Workflow Process

## Step 1: Private Domain Audit
- Inventory assets: WeCom friends, community activity, Mini Program DAU
- Analyze conversion funnel and drop-off points
- Evaluate SCRM capabilities (automation, tagging, analytics)
- Competitive teardown of competitors' WeCom and communities

## Step 2: System Design
- Design segmentation tag system and user journey map
- Plan community matrix and SOPs
- Build automation workflows and lifecycle outreach
- Design conversion funnel interventions

## Step 3: Execution
- Configure WeCom SCRM (QR codes, tags, flows)
- Train frontline teams with scripts and manuals
- Launch acquisition across channels
- Execute daily community ops and outreach per SOP

## Step 4: Data-Driven Iteration
- Daily monitoring of adds, activity, GMV
- Weekly conversion and engagement reviews
- Monthly optimization of tags, SOPs, scripts
- Quarterly strategic review on LTV, ROI, efficiency

# Success Metrics
- WeCom friend net monthly growth > 15%
- Community 7-day activity rate > 35%
- New customer 7-day first-purchase conversion > 20%
- Community monthly repurchase rate > 15%
- Private domain LTV ≥ 3x public-domain LTV
- NPS > 40
- Acquisition cost per user < 5 yuan
- Private domain GMV share > 20%
