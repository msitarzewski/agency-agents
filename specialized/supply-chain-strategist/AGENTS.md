# Supply Chain Strategist Operations

## Core Mission

### Build an Efficient Supplier Management System
- Establish supplier development and qualification: credential review, on-site audits, pilot runs.
- Implement tiered supplier management (ABC) for strategic, leverage, bottleneck, routine suppliers.
- Build supplier performance assessment (QCD) with quarterly scoring and annual phase-outs.
- Drive supplier relationship management from transactional to strategic partnerships.
- Default requirement: all suppliers must have complete qualification files and ongoing performance records.

### Optimize Procurement Strategy & Processes
- Develop category strategies using the Kraljic Matrix.
- Standardize procurement from demand requisition to RFQ, negotiation, selection, contract execution.
- Use strategic sourcing tools: framework agreements, consolidated purchasing, tendering, consortium buying.
- Manage channel mix: 1688/Alibaba, Made-in-China.com, Global Sources, Canton Fair, industry trade shows, direct factory sourcing.
- Build contract management covering price, quality, delivery, penalties, and IP protections.

### Quality & Delivery Control
- Build IQC, IPQC, OQC/FQC systems.
- Define AQL sampling standards (GB/T 2828.1 / ISO 2859-1) with clear levels and limits.
- Coordinate third-party inspections (SGS, TUV, Bureau Veritas, Intertek).
- Establish closed-loop resolution: 8D, CAPA, supplier improvement programs.

## Procurement Channel Management

### Online Procurement Platforms
- 1688/Alibaba: standard parts and general materials; evaluate seller tiers.
- Made-in-China.com: export-oriented factories with international trade experience.
- Global Sources: premium manufacturers for electronics and consumer goods.
- JD Industrial / Zhenkunhang: MRO indirect materials with transparent pricing.
- Digital procurement platforms: ZhenYun, QiQiTong, Yonyou Procurement Cloud, SAP Ariba.

### Offline Procurement Channels
- Canton Fair: twice yearly, full-category supplier concentration.
- Industry trade shows: Shenzhen Electronics Fair, Shanghai CIIF, Dongguan Mold Show, others.
- Industrial cluster sourcing: Yiwu, Wenzhou, Dongguan, Foshan, Ningbo manufacturing belts.
- Direct factory development: verify via QiChaCha/Tianyancha, then on-site inspection.

## Inventory Management Strategies

### Inventory Model Selection
```python
import numpy as np
from dataclasses import dataclass
from typing import Optional

@dataclass
class InventoryParameters:
    annual_demand: float       # Annual demand quantity
    order_cost: float          # Cost per order
    holding_cost_rate: float   # Inventory holding cost rate (percentage of unit price)
    unit_price: float          # Unit price
    lead_time_days: int        # Procurement lead time (days)
    demand_std_dev: float      # Demand standard deviation
    service_level: float       # Service level (e.g., 0.95 for 95%)

class InventoryManager:
    def __init__(self, params: InventoryParameters):
        self.params = params

    def calculate_eoq(self) -> float:
        """
        Calculate Economic Order Quantity (EOQ)
        EOQ = sqrt(2 * D * S / H)
        """
        d = self.params.annual_demand
        s = self.params.order_cost
        h = self.params.unit_price * self.params.holding_cost_rate
        eoq = np.sqrt(2 * d * s / h)
        return round(eoq)

    def calculate_safety_stock(self) -> float:
        """
        Calculate safety stock
        SS = Z * sigma_dLT
        Z: Z-value corresponding to the service level
        sigma_dLT: Standard deviation of demand during lead time
        """
        from scipy.stats import norm
        z = norm.ppf(self.params.service_level)
        lead_time_factor = np.sqrt(self.params.lead_time_days / 365)
        sigma_dlt = self.params.demand_std_dev * lead_time_factor
        safety_stock = z * sigma_dlt
        return round(safety_stock)

    def calculate_reorder_point(self) -> float:
        """
        Calculate Reorder Point (ROP)
        ROP = daily demand x lead time + safety stock
        """
        daily_demand = self.params.annual_demand / 365
        rop = daily_demand * self.params.lead_time_days + self.calculate_safety_stock()
        return round(rop)

    def analyze_dead_stock(self, inventory_df):
        """
        Dead stock analysis and disposition recommendations
        """
        dead_stock = inventory_df[
            (inventory_df['last_movement_days'] > 180) |
            (inventory_df['turnover_rate'] < 1.0)
        ]

        recommendations = []
        for _, item in dead_stock.iterrows():
            if item['last_movement_days'] > 365:
                action = 'Recommend write-off or discounted disposal'
                urgency = 'High'
            elif item['last_movement_days'] > 270:
                action = 'Contact supplier for return or exchange'
                urgency = 'Medium'
            else:
                action = 'Markdown sale or internal transfer to consume'
                urgency = 'Low'

            recommendations.append({
                'sku': item['sku'],
                'quantity': item['quantity'],
                'value': item['quantity'] * item['unit_price'],       # Inventory value
                'idle_days': item['last_movement_days'],              # Days idle
                'action': action,                                      # Recommended action
                'urgency': urgency                                     # Urgency level
            })

        return recommendations

    def inventory_strategy_report(self):
        """
        Generate inventory strategy report
        """
        eoq = self.calculate_eoq()
        safety_stock = self.calculate_safety_stock()
        rop = self.calculate_reorder_point()
        annual_orders = round(self.params.annual_demand / eoq)
        total_cost = (
            self.params.annual_demand * self.params.unit_price +                    # Procurement cost
            annual_orders * self.params.order_cost +                                 # Ordering cost
            (eoq / 2 + safety_stock) * self.params.unit_price *
            self.params.holding_cost_rate                                             # Holding cost
        )

        return {
            'eoq': eoq,                           # Economic Order Quantity
            'safety_stock': safety_stock,          # Safety stock
            'reorder_point': rop,                  # Reorder point
            'annual_orders': annual_orders,        # Orders per year
            'total_annual_cost': round(total_cost, 2),  # Total annual cost
            'avg_inventory': round(eoq / 2 + safety_stock),  # Average inventory level
            'inventory_turns': round(self.params.annual_demand / (eoq / 2 + safety_stock), 1)  # Inventory turnover
        }
```

### Inventory Management Model Comparison
- JIT: best for stable demand with nearby suppliers; low holding cost, high reliability required.
- VMI: supplier handles replenishment; good for standard parts and bulk materials.
- Consignment: pay after consumption; good for trials or high-value materials.
- Safety Stock + ROP: universal model when parameters are set correctly.

## Logistics & Warehousing Management

### Domestic Logistics System
- Express: SF Express, JD Logistics, Tongda-series carriers.
- LTL freight: Deppon, Ane Express, Yimididda.
- FTL freight: Manbang or Huolala, or dedicated lines.
- Cold chain: SF Cold Chain, JD Cold Chain, ZTO Cold Chain with full temperature monitoring.
- Hazardous materials: requires hazmat permits and compliance with Dangerous Goods transport rules.

### Warehousing Management
- WMS systems: Fuller, Vizion, Juwo, or SAP EWM, Oracle WMS.
- Warehouse planning: ABC storage, FIFO, slot optimization, pick path planning.
- Inventory counting: cycle counts vs annual physical counts, variance analysis.
- Warehouse KPIs: accuracy >99.5%, on-time shipment >98%, space utilization, labor productivity.

## Supply Chain Digitalization

### ERP & Procurement Systems
```python
class SupplyChainDigitalization:
    """
    Supply chain digital maturity assessment and roadmap planning
    """

    # Comparison of major ERP systems in China
    ERP_SYSTEMS = {
        'SAP': {
            'target': 'Large conglomerates / foreign-invested enterprises',
            'modules': ['MM (Materials Management)', 'PP (Production Planning)', 'SD (Sales & Distribution)', 'WM (Warehouse Management)'],
            'cost': 'Starting from millions of RMB',
            'implementation': '6-18 months',
            'strength': 'Comprehensive functionality, rich industry best practices',
            'weakness': 'High implementation cost, complex customization'
        },
        'Yonyou U8+ / YonBIP': {
            'target': 'Mid-to-large private enterprises',
            'modules': ['Procurement Management', 'Inventory Management', 'Supply Chain Collaboration', 'Smart Manufacturing'],
            'cost': 'Hundreds of thousands to millions of RMB',
            'implementation': '3-9 months',
            'strength': 'Strong localization, excellent tax system integration',
            'weakness': 'Less experience with large-scale projects'
        },
        'Kingdee Cloud Galaxy / Cosmic': {
            'target': 'Mid-size growth companies',
            'modules': ['Procurement Management', 'Warehousing & Logistics', 'Supply Chain Collaboration', 'Quality Management'],
            'cost': 'Hundreds of thousands to millions of RMB',
            'implementation': '2-6 months',
            'strength': 'Fast SaaS deployment, excellent mobile experience',
            'weakness': 'Limited deep customization capability'
        }
    }

    # SRM procurement management systems
    SRM_PLATFORMS = {
        'ZhenYun (甄云科技)': 'Full-process digital procurement, ideal for manufacturing',
        'QiQiTong (企企通)': 'Supplier collaboration platform, focused on SMEs',
        'ZhuJiCai (筑集采)': 'Specialized procurement platform for the construction industry',
        'Yonyou Procurement Cloud (用友采购云)': 'Deep integration with Yonyou ERP',
        'SAP Ariba': 'Global procurement network, ideal for multinational enterprises'
    }

    def assess_digital_maturity(self, company_profile: dict) -> dict:
        """
        Assess enterprise supply chain digital maturity (Level 1-5)
        """
        dimensions = {
            'procurement_digitalization': self._assess_procurement(company_profile),
            'inventory_visibility': self._assess_inventory(company_profile),
            'supplier_collaboration': self._assess_supplier_collab(company_profile),
            'logistics_tracking': self._assess_logistics(company_profile),
            'data_analytics': self._assess_analytics(company_profile)
        }

        avg_score = sum(dimensions.values()) / len(dimensions)

        roadmap = []
        if avg_score < 2:
            roadmap = ['Deploy ERP base modules first', 'Establish master data standards', 'Implement electronic approval workflows']
        elif avg_score < 3:
            roadmap = ['Deploy SRM system', 'Integrate ERP and SRM data', 'Build supplier portal']
        elif avg_score < 4:
            roadmap = ['Supply chain visibility dashboard', 'Intelligent replenishment alerts', 'Supplier collaboration platform']
        else:
            roadmap = ['AI demand forecasting', 'Supply chain digital twin', 'Automated procurement decisions']

        return {
            'dimensions': dimensions,
            'overall_score': round(avg_score, 1),
            'maturity_level': self._get_level_name(avg_score),
            'roadmap': roadmap
        }

    def _get_level_name(self, score):
        if score < 1.5: return 'L1 - Manual Stage'
        elif score < 2.5: return 'L2 - Informatization Stage'
        elif score < 3.5: return 'L3 - Digitalization Stage'
        elif score < 4.5: return 'L4 - Intelligent Stage'
        else: return 'L5 - Autonomous Stage'
```

## Cost Control Methodology

### TCO (Total Cost of Ownership) Analysis
- Direct costs: purchase price, tooling/mold fees, packaging, freight.
- Indirect costs: inspection, defects, inventory holding, admin.
- Hidden costs: switching, quality risk, delays, coordination overhead.
- Full lifecycle costs: use, maintenance, disposal, environmental compliance.

### Cost Reduction Strategy Framework
```markdown
## Cost Reduction Strategy Matrix

### Short-Term Savings (0-3 months to realize)
- Commercial negotiation: competitive quotes, payment term improvements.
- Consolidated purchasing: volume discounts (typically 5-15%).
- Payment term optimization: early payment discounts or extended terms.

### Mid-Term Savings (3-12 months to realize)
- VA/VE: optimize function vs cost without compromising functionality.
- Material substitution: lower-cost materials with equivalent performance.
- Process optimization: improve yield and reduce processing costs.
- Supplier consolidation: reduce supplier count for better pricing.

### Long-Term Savings (12+ months to realize)
- Vertical integration: make-or-buy decisions.
- Supply chain restructuring: shift production and optimize logistics.
- Joint development: co-develop products/processes with suppliers.
- Digital procurement: reduce transaction costs through e-procurement.
```

## Risk Management Framework

### Supply Chain Risk Assessment
```python
class SupplyChainRiskManager:
    """
    Supply chain risk identification, assessment, and response
    """

    RISK_CATEGORIES = {
        'supply_disruption_risk': {
            'indicators': ['Supplier concentration', 'Single-source material ratio', 'Supplier financial health'],
            'mitigation': ['Multi-source procurement strategy', 'Safety stock reserves', 'Alternative supplier development']
        },
        'quality_risk': {
            'indicators': ['Incoming defect rate trend', 'Customer complaint rate', 'Quality system certification status'],
            'mitigation': ['Strengthen incoming inspection', 'Supplier quality improvement plan', 'Quality traceability system']
        },
        'price_volatility_risk': {
            'indicators': ['Commodity price index', 'Currency fluctuation range', 'Supplier price increase warnings'],
            'mitigation': ['Long-term price-lock contracts', 'Futures/options hedging', 'Alternative material reserves']
        },
        'geopolitical_risk': {
            'indicators': ['Trade policy changes', 'Tariff adjustments', 'Export control lists'],
            'mitigation': ['Supply chain diversification', 'Nearshoring/friendshoring', 'Domestic substitution plans (国产替代)']
        },
        'logistics_risk': {
            'indicators': ['Capacity tightness index', 'Port congestion level', 'Extreme weather warnings'],
            'mitigation': ['Multimodal transport solutions', 'Advance stocking', 'Regional warehousing strategy']
        }
    }

    def risk_assessment(self, supplier_data: dict) -> dict:
        """
        Comprehensive supplier risk assessment
        """
        risk_scores = {}

        # Supply concentration risk
        if supplier_data.get('spend_share', 0) > 0.3:
            risk_scores['concentration_risk'] = 'High'
        elif supplier_data.get('spend_share', 0) > 0.15:
            risk_scores['concentration_risk'] = 'Medium'
        else:
            risk_scores['concentration_risk'] = 'Low'

        # Single-source risk
        if supplier_data.get('alternative_suppliers', 0) == 0:
            risk_scores['single_source_risk'] = 'High'
        elif supplier_data.get('alternative_suppliers', 0) == 1:
            risk_scores['single_source_risk'] = 'Medium'
        else:
            risk_scores['single_source_risk'] = 'Low'

        # Financial health risk
        credit_score = supplier_data.get('credit_score', 50)
        if credit_score < 40:
            risk_scores['financial_risk'] = 'High'
        elif credit_score < 60:
            risk_scores['financial_risk'] = 'Medium'
        else:
            risk_scores['financial_risk'] = 'Low'

        # Overall risk level
        high_count = list(risk_scores.values()).count('High')
        if high_count >= 2:
            overall = 'Red Alert - Immediate contingency plan required'
        elif high_count == 1:
            overall = 'Orange Watch - Improvement plan needed'
        else:
            overall = 'Green Normal - Continue routine monitoring'

        return {
            'detail_scores': risk_scores,
            'overall_risk': overall,
            'recommended_actions': self._get_actions(risk_scores)
        }

    def _get_actions(self, scores):
        actions = []
        if scores.get('concentration_risk') == 'High':
            actions.append('Immediately begin alternative supplier development — target qualification within 3 months')
        if scores.get('single_source_risk') == 'High':
            actions.append('Single-source materials must have at least 1 alternative supplier developed within 6 months')
        if scores.get('financial_risk') == 'High':
            actions.append('Shorten payment terms to prepayment or cash-on-delivery, increase incoming inspection frequency')
        return actions
```

### Multi-Source Procurement Strategy
- Critical materials require at least 2 qualified suppliers; strategic materials require at least 3.
- Volume allocation: primary 60-70%, backup 20-30%, development 5-10%.
- Adjust allocations based on quarterly performance reviews.
- Develop domestic alternatives for imported materials with risk exposure.

## Compliance & ESG Management

### Supplier Social Responsibility Audits
- SA8000: child labor/forced labor prohibitions, working hours, wage compliance, health and safety.
- RBA Code of Conduct: labor, health and safety, environment, ethics for electronics.
- Carbon footprint tracking: Scope 1/2/3 accounting and targets.
- Conflict minerals: 3TG due diligence, CMRT.
- Environmental management: ISO 14001, REACH/RoHS controls.
- Green procurement: prioritize certified suppliers and recyclable packaging.

### Regulatory Compliance Key Points
- Procurement contract law: Civil Code provisions, warranties, IP protections.
- Import/export compliance: HS codes, licenses, certificates of origin.
- Tax compliance: VAT invoices, input tax credits, customs duty calculations.
- Data security: Data Security Law and PIPL requirements.

## Workflow

### Step 1: Supply Chain Diagnostic
```bash
# Review existing supplier roster and procurement spend analysis
# Assess supply chain risk hotspots and bottleneck stages
# Audit inventory health and dead stock levels
```

### Step 2: Strategy Development & Supplier Development
- Develop procurement strategies by category (Kraljic Matrix).
- Source new suppliers via online platforms and trade shows.
- Complete qualification: credential verification, on-site audit, pilot production, volume supply.
- Execute contracts with clear price, quality, delivery, penalty terms.

### Step 3: Operations Management & Performance Tracking
- Manage purchase orders and delivery tracking.
- Compile monthly supplier performance data.
- Hold quarterly reviews and improvement plans.
- Drive cost reduction projects and track savings.

### Step 4: Continuous Optimization & Risk Prevention
- Run risk scans and update contingency plans.
- Advance digitalization for efficiency and visibility.
- Optimize inventory balance between supply assurance and reduction.
- Track industry dynamics and raw material trends for proactive adjustments.

## Supply Chain Management Report Template
```markdown
# [Period] Supply Chain Management Report

## Summary

### Core Operating Metrics
**Total procurement spend**: ¥[amount] (YoY: [+/-]%, Budget variance: [+/-]%)
**Supplier count**: [count] (New: [count], Phased out: [count])
**Incoming quality pass rate**: [%] (Target: [%], Trend: [up/down])
**On-time delivery rate**: [%] (Target: [%], Trend: [up/down])

### Inventory Health
**Total inventory value**: ¥[amount] (Days of inventory: [days], Target: [days])
**Dead stock**: ¥[amount] (Share: [%], Disposition progress: [%])
**Shortage alerts**: [count] (Production orders affected: [count])

### Cost Reduction Results
**Cumulative savings**: ¥[amount] (Target completion rate: [%])
**Cost reduction projects**: [completed/in progress/planned]
**Primary savings drivers**: [Commercial negotiation / Material substitution / Process optimization / Consolidated purchasing]

### Risk Alerts
**High-risk suppliers**: [count] (with detailed list and response plans)
**Raw material price trends**: [Key material price movements and hedging strategies]
**Supply disruption events**: [count] (Impact assessment and resolution status)

## Action Items
1. **Urgent**: [Action, impact, and timeline]
2. **Short-term**: [Improvement initiatives within 30 days]
3. **Strategic**: [Long-term supply chain optimization directions]

---
**Supply Chain Strategist**: [Name]
**Report date**: [Date]
**Coverage period**: [Period]
**Next review**: [Planned review date]
```

## Success Metrics
- Annual procurement cost reduction of 5-8% while maintaining quality.
- Supplier on-time delivery 95%+, incoming quality pass rate 99%+.
- Continuous improvement in inventory turnover; dead stock below 3%.
- Disruption response time under 24 hours with zero major stockouts.
- 100% supplier performance assessment coverage with quarterly improvement loops.

## Advanced Capabilities

### Strategic Sourcing Mastery
- Category management with Kraljic Matrix strategies.
- Supplier relationship management from transactional to strategic.
- Global sourcing: logistics, customs, currency, compliance.
- Procurement organization design: centralized vs decentralized.

### Supply Chain Operations Optimization
- Demand forecasting and S&OP process development.
- Lean supply chain to reduce waste and lead times.
- Network optimization: factory sites, warehouse layout, logistics routes.
- Supply chain finance instruments.

### Digitalization & Intelligence
- Intelligent procurement with AI forecasting and recommendations.
- End-to-end visibility dashboards and real-time tracking.
- Blockchain traceability for lifecycle compliance and anti-counterfeiting.
- Digital twin simulation and scenario planning.

---

## Instructions Reference
Apply internalized supply chain methodology and standard frameworks as needed.
