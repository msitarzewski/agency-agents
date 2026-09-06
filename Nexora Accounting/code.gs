/**
 * ============================================================================
 * NEXORA LIMITED - ACCOUNTING SYSTEM 
 * GOOGLE APPS SCRIPT WEB APP BACKEND (REST API & AUTO-POSTING ENGINE)
 * ============================================================================
 * Company: Nexora Limited
 * TPIN: 71302401 | Currency: MWK (Malawi Kwacha) | Symbol: MK
 * Address: P.O.Box 142, Lilongwe, Corporate Mall, 1st Floor, Office Block B, Chilambula Road, Lilongwe, Malawi
 * Bank: CDH Investment Bank | Account: 0030224422400 | Sort Code: 103603 | Swift: CDHIBMWMW
 *
 * Tax Rates:
 *   - VAT: 17.50%
 *   - WHT (Services/Fees): 20%
 *   - WHT (Supplies): 3%
 *   - WHT (Rentals): 15%
 *   - WHT (Transportation): 10%
 * ============================================================================
 */

// Global Sheet Names
const SHEETS = {
  CONFIG: "CONFIG",
  CHART_OF_ACCOUNTS: "CHART_OF_ACCOUNTS",
  COST_CENTERS: "COST_CENTERS",
  CUSTOMERS: "CUSTOMERS",
  SUPPLIERS: "SUPPLIERS",
  EMPLOYEES: "EMPLOYEES",
  ITEMS_PRODUCTS: "ITEMS_PRODUCTS",
  VOUCHER_COUNTER: "VOUCHER_COUNTER",
  JOURNAL_ENTRIES: "JOURNAL_ENTRIES",
  SALES_INVOICES: "SALES_INVOICES",
  PURCHASE_BILLS: "PURCHASE_BILLS",
  RECEIPTS: "RECEIPTS",
  PAYMENTS: "PAYMENTS",
  BANK_RECONCILIATION: "BANK_RECONCILIATION",
  BUDGET_MASTER: "BUDGET_MASTER",
  BUDGET_TRACKING: "BUDGET_TRACKING",
  FIXED_ASSETS: "FIXED_ASSETS",
  TAX_RECORDS: "TAX_RECORDS",
  AUDIT_LOG: "AUDIT_LOG",
  USERS: "USERS",
  FINANCIAL_YEAR: "FINANCIAL_YEAR",
  INVENTORY_TRANSACTIONS: "INVENTORY_TRANSACTIONS",
  RECURRING_ENTRIES: "RECURRING_ENTRIES",
  DELIVERY_NOTES: "DELIVERY_NOTES",
  GOODS_RECEIPT_NOTES: "GOODS_RECEIPT_NOTES",
  STOCK_JOURNALS: "STOCK_JOURNALS",
  PURCHASE_ORDERS: "PURCHASE_ORDERS",
  QUOTATIONS_PROFORMAS: "QUOTATIONS_PROFORMAS",
  DEBIT_NOTES: "DEBIT_NOTES",
  CREDIT_NOTES: "CREDIT_NOTES",
  STOCK_GROUPS: "STOCK_GROUPS",
  STOCK_CATEGORIES: "STOCK_CATEGORIES",
  UNITS_MEASURE: "UNITS_MEASURE",
  ACCOUNT_GROUPS: "ACCOUNT_GROUPS"
};

// Schema definitions (Exact column headers required by specification)
const SCHEMAS = {
  CONFIG: ["Key", "Value", "Description", "LastModified"],
  CHART_OF_ACCOUNTS: [
    "AccountCode", "AccountName", "AccountGroup", "AccountSubGroup",
    "AccountType", "ParentAccount", "Level", "IsSubledger",
    "SubledgerType", "OpeningBalanceDr", "OpeningBalanceCr", "IsActive",
    "BudgetAllocated", "CreatedDate", "ModifiedDate", "CreatedBy"
  ],
  COST_CENTERS: ["CostCenterCode", "CostCenterName", "Category", "ParentCostCenter", "IsActive", "CreatedDate"],
  CUSTOMERS: [
    "CustomerID", "CustomerName", "ContactPerson", "Phone", "Email",
    "Address", "City", "Country", "TPIN", "CreditLimit", "CreditDays",
    "OpeningBalance", "AccountCode", "IsActive", "CreatedDate", "ModifiedDate"
  ],
  SUPPLIERS: [
    "SupplierID", "SupplierName", "ContactPerson", "Phone", "Email",
    "Address", "City", "Country", "TPIN", "CreditDays", "OpeningBalance",
    "AccountCode", "WHTCategory", "IsActive", "CreatedDate", "ModifiedDate"
  ],
  EMPLOYEES: [
    "EmployeeID", "EmployeeName", "Department", "Designation", "Phone",
    "Email", "BankAccount", "BankName", "BasicSalary", "AccountCode",
    "IsActive", "CreatedDate", "ModifiedDate"
  ],
  ITEMS_PRODUCTS: [
    "ItemCode", "ItemName", "ItemType", "Category", "Unit", "HSNCode",
    "PurchaseRate", "SalesRate", "VATApplicable", "VATRate", "ReorderLevel",
    "OpeningStock", "OpeningStockValue", "AccountCodeSales", "AccountCodePurchase",
    "AccountCodeStock", "IsActive", "CreatedDate", "ModifiedDate"
  ],
  VOUCHER_COUNTER: ["VoucherType", "Prefix", "CurrentNumber", "Format", "FinancialYear"],
  JOURNAL_ENTRIES: [
    "TransactionID", "VoucherType", "VoucherNumber", "VoucherDate",
    "AccountCode", "AccountName", "Description", "Narration",
    "DebitAmount", "CreditAmount", "CostCenter", "SubledgerType",
    "SubledgerID", "ChequeNumber", "ChequeDate", "ReferenceNumber",
    "ReferenceType", "ReferenceID", "IsReversed", "ReversalID",
    "IsPosted", "CreatedDate", "CreatedBy", "ModifiedDate"
  ],
  SALES_INVOICES: [
    "InvoiceID", "InvoiceNumber", "InvoiceDate", "DueDate", "CustomerID",
    "CustomerName", "CustomerTPIN", "BillingAddress", "ReferenceNumber",
    "ItemCode", "ItemName", "Description", "Quantity", "Unit", "Rate",
    "Amount", "DiscountPercent", "DiscountAmount", "TaxableAmount",
    "VATRate", "VATAmount", "WHTRate", "WHTAmount", "LineTotal",
    "SubTotal", "TotalVAT", "TotalWHT", "GrandTotal", "AmountPaid",
    "BalanceDue", "PaymentStatus", "CostCenter", "Notes", "TransactionID",
    "CreatedDate", "CreatedBy", "ModifiedDate"
  ],
  PURCHASE_BILLS: [
    "BillID", "BillNumber", "BillDate", "DueDate", "SupplierID",
    "SupplierName", "SupplierTPIN", "ReferenceNumber", "ItemCode",
    "ItemName", "Description", "Quantity", "Unit", "Rate", "Amount",
    "DiscountPercent", "DiscountAmount", "TaxableAmount", "VATRate",
    "VATAmount", "WHTCategory", "WHTRate", "WHTAmount", "LineTotal",
    "SubTotal", "TotalVAT", "TotalWHT", "GrandTotal", "AmountPaid",
    "BalanceDue", "PaymentStatus", "CostCenter", "Notes", "TransactionID",
    "CreatedDate", "CreatedBy", "ModifiedDate"
  ],
  RECEIPTS: [
    "ReceiptID", "ReceiptNumber", "ReceiptDate", "ReceivedFrom", "CustomerID",
    "PaymentMode", "BankAccountCode", "ChequeNumber", "ChequeDate",
    "TransactionRef", "Amount", "AllocatedTo", "Narration", "CostCenter",
    "TransactionID", "CreatedDate", "CreatedBy"
  ],
  PAYMENTS: [
    "PaymentID", "PaymentNumber", "PaymentDate", "PaidTo", "SupplierID",
    "PaymentMode", "BankAccountCode", "ChequeNumber", "ChequeDate",
    "TransactionRef", "Amount", "WHTDeducted", "NetPayment", "AllocatedTo",
    "Narration", "CostCenter", "TransactionID", "CreatedDate", "CreatedBy"
  ],
  BANK_RECONCILIATION: [
    "ReconID", "BankAccountCode", "StatementDate", "TransactionID",
    "VoucherNumber", "VoucherDate", "Description", "DebitAmount",
    "CreditAmount", "IsReconciled", "ReconciledDate", "StatementRef",
    "CreatedDate"
  ],
  BUDGET_MASTER: [
    "BudgetID", "FinancialYear", "AccountCode", "AccountName", "CostCenter",
    "BudgetType", "AnnualBudget", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "TotalBudget", "ApprovedBy",
    "ApprovedDate", "IsActive", "CreatedDate", "ModifiedDate"
  ],
  BUDGET_TRACKING: [
    "TrackingID", "FinancialYear", "Period", "AccountCode", "CostCenter",
    "BudgetedAmount", "ActualAmount", "Variance", "VariancePercent",
    "Status", "LastUpdated"
  ],
  FIXED_ASSETS: [
    "AssetID", "AssetCode", "AssetName", "Category", "PurchaseDate",
    "PurchaseValue", "SupplierID", "DepreciationMethod", "DepreciationRate",
    "UsefulLife", "ResidualValue", "AccumulatedDepreciation", "NetBookValue",
    "Location", "AccountCodeAsset", "AccountCodeDepreciation",
    "AccountCodeAccDepreciation", "Status", "DisposalDate", "DisposalValue",
    "CreatedDate", "ModifiedDate"
  ],
  TAX_RECORDS: [
    "TaxRecordID", "TaxType", "Period", "TransactionID", "VoucherNumber",
    "PartyName", "PartyTPIN", "TaxableAmount", "TaxRate", "TaxAmount",
    "Direction", "FilingStatus", "FilingDate", "CreatedDate"
  ],
  AUDIT_LOG: [
    "LogID", "Timestamp", "UserID", "Action", "Module", "RecordID",
    "OldValue", "NewValue", "IPAddress"
  ],
  USERS: [
    "UserID", "Username", "PasswordHash", "FullName", "Role",
    "Email", "IsActive", "LastLogin", "CreatedDate"
  ],
  FINANCIAL_YEAR: [
    "YearID", "YearName", "StartDate", "EndDate", "IsCurrent",
    "IsClosed", "ClosedDate", "ClosedBy"
  ],
  INVENTORY_TRANSACTIONS: [
    "TransID", "TransDate", "ItemCode", "TransType", "ReferenceType",
    "ReferenceID", "QuantityIn", "QuantityOut", "Rate", "Value",
    "RunningQty", "RunningValue", "Narration", "CreatedDate"
  ],
  RECURRING_ENTRIES: [
    "RecurringID", "TemplateName", "VoucherType", "Frequency",
    "NextDueDate", "LastProcessedDate", "AccountCodeDr", "AccountCodeCr",
    "Amount", "Narration", "CostCenter", "IsActive", "CreatedDate"
  ],
  DELIVERY_NOTES: [
    "DeliveryID", "DeliveryNumber", "DeliveryDate", "CustomerID", "CustomerName",
    "DispatchAddress", "TransporterRef", "ItemCode", "ItemName", "Quantity",
    "Unit", "Description", "Status", "CreatedDate", "CreatedBy"
  ],
  DEBIT_NOTES: [
    "DebitNoteID", "DebitNoteNumber", "DebitNoteDate",
    "SupplierID", "SupplierName", "SupplierTPIN",
    "OriginalBillID", "OriginalBillNumber", "Reason",
    "ReasonDetails", "ItemCode", "ItemName", "Description",
    "OriginalQty", "ReturnQty", "Unit", "Rate", "Amount",
    "VATRate", "VATAmount", "WHTCategory", "WHTRate",
    "WHTAmount", "LineTotal", "SubTotal", "TotalVAT",
    "TotalWHT", "GrandTotal", "CostCenter", "Narration",
    "TransactionID", "Status", "CreatedDate", "CreatedBy", "ModifiedDate"
  ],
  STOCK_GROUPS: ["StockGroupID", "StockGroupName", "ParentGroup", "IsActive", "CreatedDate"],
  STOCK_CATEGORIES: ["StockCategoryID", "StockCategoryName", "IsActive", "CreatedDate"],
  UNITS_MEASURE: ["UnitID", "UnitSymbol", "FormalName", "DecimalPlaces", "IsActive", "CreatedDate"],
  ACCOUNT_GROUPS: ["GroupID", "GroupName", "ParentGroup", "PrimaryCategory", "Nature", "IsActive", "CreatedDate"],
  CREDIT_NOTES: [
    "CreditNoteID", "CreditNoteNumber", "CreditNoteDate",
    "CustomerID", "CustomerName", "CustomerTPIN",
    "OriginalInvoiceID", "OriginalInvoiceNumber", "Reason",
    "ReasonDetails", "ItemCode", "ItemName", "Description",
    "OriginalQty", "ReturnQty", "Unit", "Rate", "Amount",
    "VATRate", "VATAmount", "WHTRate", "WHTAmount", "LineTotal",
    "SubTotal", "TotalVAT", "TotalWHT", "GrandTotal",
    "CostCenter", "Narration", "TransactionID", "Status",
    "CreatedDate", "CreatedBy", "ModifiedDate"
  ],
  GOODS_RECEIPT_NOTES: [
    "GRNID", "GRNNumber", "GRNDate", "SupplierID", "SupplierName",
    "SupplierPORef", "WarehouseLocation", "ItemCode", "ItemName", "ReceivedQty",
    "AcceptedQty", "RejectedQty", "Unit", "Remarks", "Status", "CreatedDate", "CreatedBy"
  ],
  PURCHASE_ORDERS: ["POID", "PONumber", "PODate", "ExpectedDate", "SupplierID", "SupplierName", "SupplierTPIN", "PaymentTerms", "ReferenceNumber", "SubTotal", "TotalVAT", "GrandTotal", "Notes", "Status", "CreatedDate", "CreatedBy"],
  QUOTATIONS_PROFORMAS: ["QuoteID", "QuoteNumber", "QuoteDate", "ValidUntil", "DocType", "CustomerID", "CustomerName", "CustomerTPIN", "BillingAddress", "ReferenceNumber", "SubTotal", "TotalVAT", "GrandTotal", "Notes", "Status", "CreatedDate", "CreatedBy"],
  STOCK_JOURNALS: [
    "StockJournalID", "JournalNumber", "JournalDate", "Purpose",
    "SourceItemCode", "SourceQty", "SourceRate", "SourceValue",
    "DestItemCode", "DestQty", "DestRate", "DestValue",
    "Narration", "CreatedDate", "CreatedBy"
  ]
};

/**
 * setupDatabase(): Automatically creates all 23 sheets with exact schema columns
 * and initializes CONFIG, VOUCHER_COUNTER, FINANCIAL_YEAR, USERS, and default accounts, customers, suppliers, and items.
 */
function setupDatabase() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const now = new Date().toISOString();
  
  for (const [sheetName, headers] of Object.entries(SCHEMAS)) {
    let sheet = ss.getSheetByName(sheetName);
    if (!sheet) {
      sheet = ss.insertSheet(sheetName);
    }
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(headers);
      sheet.getRange(1, 1, 1, headers.length).setFontWeight("bold").setBackground("#0a2540").setFontColor("#ffffff");
      sheet.setFrozenRows(1);
    }
  }

  // Seed CONFIG if empty
  const configSheet = ss.getSheetByName(SHEETS.CONFIG);
  if (configSheet.getLastRow() <= 1) {
    const defaultConfigs = [
      ["COMPANY_NAME", "Nexora Limited", "Registered Company Name", now],
      ["COMPANY_TPIN", "71302401", "Malawi Taxpayer Identification Number", now],
      ["COMPANY_ADDRESS", "P.O.Box 142, Lilongwe, Corporate Mall, 1st Floor, Office Block B, Chilambula Road, Lilongwe, Malawi", "Physical & Postal Address", now],
      ["COMPANY_PHONE", "+265999788594", "Official Contact Number", now],
      ["COMPANY_EMAIL", "nexoramw@gmail.com", "Official Email Address", now],
      ["BANK_NAME", "CDH Investment Bank", "Official Bank Name", now],
      ["BANK_ACCOUNT", "0030224422400", "Bank Account Number", now],
      ["BANK_BRANCH", "City Mall Branch", "Bank Branch Name", now],
      ["BANK_SORT_CODE", "103603", "Sort Code", now],
      ["BANK_SWIFT", "CDHIBMWMW", "SWIFT/BIC Code", now],
      ["CURRENCY", "MWK", "Currency Code", now],
      ["CURRENCY_SYMBOL", "MK", "Currency Symbol", now],
      ["VAT_RATE", "17.50", "Malawi VAT Rate (%)", now],
      ["WHT_SERVICES_RATE", "20.00", "WHT Services/Fees Rate (%)", now],
      ["WHT_SUPPLIES_RATE", "3.00", "WHT Supplies Rate (%)", now],
      ["WHT_RENTALS_RATE", "15.00", "WHT Rentals Rate (%)", now],
      ["WHT_TRANSPORT_RATE", "10.00", "WHT Transportation Rate (%)", now],
      ["LAST_SYNC_TIMESTAMP", now, "Global Timestamp for Incremental Sync", now]
    ];
    for (const row of defaultConfigs) {
      configSheet.appendRow(row);
    }
  }

  // Seed FINANCIAL_YEAR if empty
  const fySheet = ss.getSheetByName(SHEETS.FINANCIAL_YEAR);
  if (fySheet.getLastRow() <= 1) {
    fySheet.appendRow(["FY-2026", "Jan-Dec 2026", "2026-01-01", "2026-12-31", "YES", "NO", "", ""]);
  }

  // Seed VOUCHER_COUNTER if empty
  const vcSheet = ss.getSheetByName(SHEETS.VOUCHER_COUNTER);
  if (vcSheet.getLastRow() <= 1) {
    const defaultCounters = [
      ["JOURNAL", "JV-26-", 1, "0000", "FY-2026"],
      ["SALES_INVOICE", "INV-26-", 1, "0000", "FY-2026"],
      ["PURCHASE_BILL", "BILL-26-", 1, "0000", "FY-2026"],
      ["RECEIPT", "RCP-26-", 1, "0000", "FY-2026"],
      ["PAYMENT", "PAY-26-", 1, "0000", "FY-2026"],
      ["CONTRA", "CNT-26-", 1, "0000", "FY-2026"],
      ["DEBIT_NOTE", "DN-26-", 1, "0000", "FY-2026"],
      ["CREDIT_NOTE", "CN-26-", 1, "0000", "FY-2026"],
      ["DELIVERY_NOTE", "DLV-26-", 1, "0000", "FY-2026"],
      ["GOODS_RECEIPT_NOTE", "GRN-26-", 1, "0000", "FY-2026"],
      ["STOCK_JOURNAL", "STK-26-", 1, "0000", "FY-2026"],
      ["PURCHASE_ORDER", "PO-26-", 1, "0000", "FY-2026"],
      ["QUOTATION", "QTN-26-", 1, "0000", "FY-2026"],
      ["PROFORMA_INVOICE", "PI-26-", 1, "0000", "FY-2026"]
    ];
    for (const row of defaultCounters) {
      vcSheet.appendRow(row);
    }
  }

  // Seed DEFAULT USERS if empty
  const usersSheet = ss.getSheetByName(SHEETS.USERS);
  if (usersSheet.getLastRow() <= 1) {
    usersSheet.appendRow(["USR001", "admin", "admin123", "System Administrator (Chartered Accountant)", "Admin", "nexoramw@gmail.com", "YES", now, now]);
  }

  // Seed CHART OF ACCOUNTS if incomplete (< 100 accounts)
  const coaSheet = ss.getSheetByName(SHEETS.CHART_OF_ACCOUNTS);
  if (coaSheet.getLastRow() < 100) {
    coaSheet.clearContents();
    coaSheet.appendRow(SCHEMAS[SHEETS.CHART_OF_ACCOUNTS]);
    const defaultCOA = [
      ["1000", "FIXED ASSETS", "Fixed Assets", "", "Asset", "", "1", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["1001", "Land & Buildings", "Fixed Assets", "", "Asset", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["1002", "Plant & Machinery", "Fixed Assets", "", "Asset", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["1003", "Furniture & Fixtures", "Fixed Assets", "", "Asset", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["1004", "Office Equipment", "Fixed Assets", "", "Asset", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["1005", "Computer Equipment", "Fixed Assets", "", "Asset", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["1006", "Motor Vehicles", "Fixed Assets", "", "Asset", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["1007", "Leasehold Improvements", "Fixed Assets", "", "Asset", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["1050", "Accumulated Depreciation - Buildings", "Fixed Assets", "", "Asset", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["1051", "Accumulated Depreciation - P&M", "Fixed Assets", "", "Asset", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["1052", "Accumulated Depreciation - F&F", "Fixed Assets", "", "Asset", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["1053", "Accumulated Depreciation - Office Eq", "Fixed Assets", "", "Asset", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["1054", "Accumulated Depreciation - Computers", "Fixed Assets", "", "Asset", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["1055", "Accumulated Depreciation - Vehicles", "Fixed Assets", "", "Asset", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["1100", "CURRENT ASSETS", "Current Assets", "", "Asset", "", "1", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["1101", "Cash in Hand", "Cash", "", "Asset", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["1102", "Petty Cash", "Cash", "", "Asset", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["1110", "CDH Investment Bank - 0030224422400", "Bank", "", "Asset", "", "2", "Yes", "Bank", 0, 0, "Yes", 0, now, now, "System"],
      ["1111", "Bank Account 2 (Reserve)", "Bank", "", "Asset", "", "2", "Yes", "Bank", 0, 0, "Yes", 0, now, now, "System"],
      ["1120", "Accounts Receivable Control", "Receivables", "", "Asset", "", "2", "Yes", "Customer", 0, 0, "Yes", 0, now, now, "System"],
      ["1121", "Staff Advances", "Receivables", "", "Asset", "", "2", "Yes", "Employee", 0, 0, "Yes", 0, now, now, "System"],
      ["1122", "Prepaid Expenses", "Receivables", "", "Asset", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["1123", "Advance to Suppliers", "Receivables", "", "Asset", "", "2", "Yes", "Supplier", 0, 0, "Yes", 0, now, now, "System"],
      ["1124", "Security Deposits", "Receivables", "", "Asset", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["1125", "WHT Receivable (Suffered)", "Receivables", "", "Asset", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["1126", "VAT Input (Receivable)", "Receivables", "", "Asset", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["1130", "Inventory - Raw Materials", "Inventory", "", "Asset", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["1131", "Inventory - Finished Goods", "Inventory", "", "Asset", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["1132", "Inventory - Consumables", "Inventory", "", "Asset", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["2000", "CURRENT LIABILITIES", "Current Liabilities", "", "Liability", "", "1", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["2001", "Accounts Payable Control", "Payables", "", "Liability", "", "2", "Yes", "Supplier", 0, 0, "Yes", 0, now, now, "System"],
      ["2002", "Accrued Expenses", "Payables", "", "Liability", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["2003", "Salary Payable", "Payables", "", "Liability", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["2004", "PAYE Payable", "Tax Payable", "", "Liability", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["2005", "Pension Fund Payable", "Payables", "", "Liability", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["2010", "VAT Output (Payable)", "Tax Payable", "", "Liability", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["2011", "VAT Control Account", "Tax Payable", "", "Liability", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["2015", "WHT Payable - Services 20%", "Tax Payable", "", "Liability", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["2016", "WHT Payable - Supplies 3%", "Tax Payable", "", "Liability", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["2017", "WHT Payable - Rentals 15%", "Tax Payable", "", "Liability", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["2018", "WHT Payable - Transport 10%", "Tax Payable", "", "Liability", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["2020", "Short Term Loans", "Loans", "", "Liability", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["2021", "Bank Overdraft", "Loans", "", "Liability", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["2050", "LONG TERM LIABILITIES", "Long Term Liab", "", "Liability", "", "1", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["2051", "Long Term Loans", "Long Term Liab", "", "Liability", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["2052", "Director's Loan", "Long Term Liab", "", "Liability", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["3000", "SHAREHOLDERS' EQUITY", "Equity", "", "Equity", "", "1", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["3001", "Share Capital", "Equity", "", "Equity", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["3002", "Retained Earnings", "Equity", "", "Equity", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["3003", "Current Year Profit/Loss", "Equity", "", "Equity", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["3004", "Dividends Declared", "Equity", "", "Equity", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["3005", "Capital Reserves", "Equity", "", "Equity", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["4000", "REVENUE", "Revenue", "", "Revenue", "", "1", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["4001", "Sales Revenue - Goods", "Sales", "", "Revenue", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["4002", "Sales Revenue - Services", "Sales", "", "Revenue", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["4003", "Consultancy Income", "Sales", "", "Revenue", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["4004", "Commission Income", "Other Income", "", "Revenue", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["4005", "Interest Income", "Other Income", "", "Revenue", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["4006", "Rental Income", "Other Income", "", "Revenue", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["4007", "Foreign Exchange Gain", "Other Income", "", "Revenue", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["4008", "Miscellaneous Income", "Other Income", "", "Revenue", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["4009", "Discount Received", "Other Income", "", "Revenue", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["4010", "Profit on Asset Disposal", "Other Income", "", "Revenue", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["4099", "Sales Returns & Allowances", "Sales", "", "Revenue", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["5000", "COST OF SALES", "Cost of Sales", "", "Expense", "", "1", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["5001", "Purchases - Goods", "Cost of Sales", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 8000000, now, now, "System"],
      ["5002", "Purchases - Raw Materials", "Cost of Sales", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 5000000, now, now, "System"],
      ["5003", "Direct Labour", "Cost of Sales", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 4000000, now, now, "System"],
      ["5004", "Freight Inward", "Cost of Sales", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 1500000, now, now, "System"],
      ["5005", "Customs & Import Duties", "Cost of Sales", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 2000000, now, now, "System"],
      ["5006", "Purchase Returns", "Cost of Sales", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["5007", "Stock Adjustments", "Cost of Sales", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["6000", "OPERATING EXPENSES", "Expenses", "", "Expense", "", "1", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["6001", "Salaries & Wages", "Staff Costs", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 18000000, now, now, "System"],
      ["6002", "Staff Allowances", "Staff Costs", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 3000000, now, now, "System"],
      ["6003", "Employer Pension Contribution", "Staff Costs", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 1800000, now, now, "System"],
      ["6004", "Staff Welfare", "Staff Costs", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 1200000, now, now, "System"],
      ["6005", "Staff Training", "Staff Costs", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 1500000, now, now, "System"],
      ["6006", "Medical Expenses", "Staff Costs", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 2000000, now, now, "System"],
      ["6010", "Rent Expense", "Premises", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 4800000, now, now, "System"],
      ["6011", "Electricity & Water", "Premises", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 1800000, now, now, "System"],
      ["6012", "Repairs & Maintenance", "Premises", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 2400000, now, now, "System"],
      ["6013", "Security Expenses", "Premises", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 1500000, now, now, "System"],
      ["6014", "Cleaning Expenses", "Premises", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 900000, now, now, "System"],
      ["6020", "Telephone & Internet", "Admin", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 1800000, now, now, "System"],
      ["6021", "Postage & Courier", "Admin", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 450000, now, now, "System"],
      ["6022", "Printing & Stationery", "Admin", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 850000, now, now, "System"],
      ["6023", "Office Supplies", "Admin", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 950000, now, now, "System"],
      ["6024", "Computer & Software Expenses", "Admin", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 2500000, now, now, "System"],
      ["6030", "Motor Vehicle Expenses", "Transport", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 1500000, now, now, "System"],
      ["6031", "Fuel & Lubricants", "Transport", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 3500000, now, now, "System"],
      ["6032", "Vehicle Insurance", "Transport", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 1200000, now, now, "System"],
      ["6033", "Vehicle Repairs", "Transport", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 1800000, now, now, "System"],
      ["6034", "Travel & Accommodation", "Transport", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 2400000, now, now, "System"],
      ["6040", "Professional Fees - Legal", "Professional", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 2500000, now, now, "System"],
      ["6041", "Professional Fees - Audit", "Professional", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 3500000, now, now, "System"],
      ["6042", "Professional Fees - Consultancy", "Professional", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 4000000, now, now, "System"],
      ["6043", "Bank Charges", "Financial", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 850000, now, now, "System"],
      ["6044", "Interest Expense", "Financial", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 1800000, now, now, "System"],
      ["6045", "Insurance - General", "Financial", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 2200000, now, now, "System"],
      ["6050", "Advertising & Marketing", "Marketing", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 3500000, now, now, "System"],
      ["6051", "Business Development", "Marketing", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 2500000, now, now, "System"],
      ["6052", "Entertainment", "Marketing", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 1200000, now, now, "System"],
      ["6060", "Depreciation - Buildings", "Depreciation", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["6061", "Depreciation - Plant & Machinery", "Depreciation", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["6062", "Depreciation - Furniture & Fixtures", "Depreciation", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["6063", "Depreciation - Office Equipment", "Depreciation", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["6064", "Depreciation - Computers", "Depreciation", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["6065", "Depreciation - Motor Vehicles", "Depreciation", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["6070", "Bad Debts Written Off", "Other Expense", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["6071", "Provision for Doubtful Debts", "Other Expense", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["6072", "Foreign Exchange Loss", "Other Expense", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["6073", "Donations & CSR", "Other Expense", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["6074", "Subscriptions & Memberships", "Other Expense", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["6075", "Penalties & Fines", "Other Expense", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["6076", "Discount Allowed", "Other Expense", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["6077", "Loss on Asset Disposal", "Other Expense", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["6078", "Miscellaneous Expenses", "Other Expense", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"],
      ["6080", "Corporate Tax Expense", "Tax", "", "Expense", "", "2", "No", "None", 0, 0, "Yes", 0, now, now, "System"]
    ];
    for (const row of defaultCOA) {
      coaSheet.appendRow(row);
    }
  }

  // Seed COST_CENTERS if empty
  const ccSheet = ss.getSheetByName(SHEETS.COST_CENTERS);
  if (ccSheet.getLastRow() <= 1) {
    ccSheet.appendRow(["CC001", "Administration", "Administration", "", "Yes", now]);
    ccSheet.appendRow(["CC002", "Finance", "Finance", "", "Yes", now]);
    ccSheet.appendRow(["CC003", "Operations", "Operations", "", "Yes", now]);
    ccSheet.appendRow(["CC004", "Marketing", "Marketing", "", "Yes", now]);
    ccSheet.appendRow(["CC005", "Human Resources", "Human Resources", "", "Yes", now]);
  }

  // Seed CUSTOMERS if empty 
  const custSheet = ss.getSheetByName(SHEETS.CUSTOMERS);
  if (custSheet.getLastRow() <= 1) {
    custSheet.appendRow(["CUST001", "Malawi Broadcasting Corporation", "James Phiri", "+265991000100", "finance@mbc.mw", "Broadcasting House, Kasungu Road", "Lilongwe", "Malawi", "10001234", 5000000, 30, 2500000, "1120", "Yes", now, now]);
    custSheet.appendRow(["CUST002", "Press Corporation Ltd", "Chipo Banda", "+265992000200", "accounts@presscorp.mw", "Press House, Henderson Street", "Blantyre", "Malawi", "10005678", 10000000, 30, 3200000, "1120", "Yes", now, now]);
    custSheet.appendRow(["CUST003", "Illovo Sugar Malawi", "Grace Gondwe", "+265993000300", "billing@illovo.mw", "Churchill Road, Limbe", "Blantyre", "Malawi", "10009012", 8000000, 30, 1500000, "1120", "Yes", now, now]);
    custSheet.appendRow(["CUST004", "National Bank of Malawi", "Patrick Mwale", "+265994000400", "procurement@natbankmw.com", "Henderson Street", "Blantyre", "Malawi", "10003456", 15000000, 30, 4000000, "1120", "Yes", now, now]);
    custSheet.appendRow(["CUST005", "Telekom Networks Malawi", "Kondwani Tembo", "+265995000500", "invoices@tnm.mw", "TNM House, Livingstone Avenue", "Blantyre", "Malawi", "10007890", 12000000, 30, 2800000, "1120", "Yes", now, now]);
  }

  // Seed SUPPLIERS if empty 
  const suppSheet = ss.getSheetByName(SHEETS.SUPPLIERS);
  if (suppSheet.getLastRow() <= 1) {
    suppSheet.appendRow(["SUPP001", "Office Mart Ltd", "Henry Chirwa", "+265881001111", "sales@officemart.mw", "Paul Kagame Road", "Lilongwe", "Malawi", "20001111", 30, 1200000, "2001", "Supplies", "Yes", now, now]);
    suppSheet.appendRow(["SUPP002", "Tech Solutions MW", "Susan Msiska", "+265882002222", "info@techsolutions.mw", "Area 4 Industrial", "Lilongwe", "Malawi", "20002222", 30, 1800000, "2001", "Services/Fees", "Yes", now, now]);
    suppSheet.appendRow(["SUPP003", "City Properties Ltd", "David Phiri", "+265883003333", "leasing@cityprop.mw", "Capital City Mall", "Lilongwe", "Malawi", "20003333", 14, 2400000, "2001", "Rentals", "Yes", now, now]);
    suppSheet.appendRow(["SUPP004", "Swift Transport Co", "Peter Mwale", "+265884004444", "dispatch@swift.mw", "Kanengo Industrial Estate", "Lilongwe", "Malawi", "20004444", 30, 900000, "2001", "Transportation", "Yes", now, now]);
    suppSheet.appendRow(["SUPP005", "BizConsult Associates", "Mercy Banda", "+265885005555", "consult@bizconsult.mw", "Chayamba Building", "Blantyre", "Malawi", "20005555", 14, 1500000, "2001", "Services/Fees", "Yes", now, now]);
  }

  // Seed ITEMS_PRODUCTS if empty 
  const itemsSheet = ss.getSheetByName(SHEETS.ITEMS_PRODUCTS);
  if (itemsSheet.getLastRow() <= 1) {
    itemsSheet.appendRow(["IT001", "IT Consultancy Services", "Service", "Services", "Day", "9983.11", 150000, 250000, "Yes", 17.50, 0, 0, 0, "4002", "5001", "", "Yes", now, now]);
    itemsSheet.appendRow(["IT002", "Software License", "Goods", "Software", "Pcs", "8471.60", 350000, 500000, "Yes", 17.50, 5, 15, 5250000, "4001", "5001", "1130", "Yes", now, now]);
    itemsSheet.appendRow(["IT003", "Network Installation", "Service", "Services", "Project", "9983.22", 900000, 1500000, "Yes", 17.50, 0, 0, 0, "4002", "5001", "", "Yes", now, now]);
    itemsSheet.appendRow(["IT004", "Computer Hardware", "Goods", "Hardware", "Pcs", "8471.50", 550000, 800000, "Yes", 17.50, 10, 25, 13750000, "4001", "5001", "1130", "Yes", now, now]);
    itemsSheet.appendRow(["IT005", "Training Services", "Service", "Services", "Day", "9983.33", 80000, 150000, "Yes", 17.50, 0, 0, 0, "4002", "5001", "", "Yes", now, now]);
  }

  return "Database Setup Complete for Nexora Limited.";
}

function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    var r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

function updateLastSyncTimestamp() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(SHEETS.CONFIG);
  if (!sheet) return new Date().toISOString();
  const data = sheet.getDataRange().getValues();
  const now = new Date().toISOString();
  for (let i = 1; i < data.length; i++) {
    if (data[i][0] === "LAST_SYNC_TIMESTAMP") {
      sheet.getRange(i + 1, 2).setValue(now);
      sheet.getRange(i + 1, 4).setValue(now);
      return now;
    }
  }
  sheet.appendRow(["LAST_SYNC_TIMESTAMP", now, "Global Timestamp for Incremental Sync", now]);
  return now;
}

/**
 * CORS and HTTP GET Handler
 */
function doGet(e) {
  return handleRequest(e, "GET");
}

/**
 * CORS and HTTP POST Handler
 */
function doPost(e) {
  return handleRequest(e, "POST");
}

/**
 * Unified Request Router (Supports GET & POST with CORS)
 */
function handleRequest(e, method) {
  try {
    let params = (e && e.parameter) ? e.parameter : {};
    let payload = {};
    if (e && e.postData && e.postData.contents) {
      try {
        payload = JSON.parse(e.postData.contents);
      } catch (err) {
        payload = {};
      }
    }

    const action = payload.action || params.action || "testConnection";
    let requestData = payload.data || {};
    if (params.data && typeof params.data === "string") {
      try {
        requestData = JSON.parse(params.data);
      } catch (err) {
        requestData = {};
      }
    }

    let result;
    switch (action) {
      case "testConnection":
        result = {
          status: "success",
          message: "Connected to Nexora Limited Google Sheets Database successfully!",
          company: "Nexora Limited",
          tpin: "71302401",
          databaseReady: true,
          timestamp: new Date().toISOString()
        };
        break;
      case "setupDatabase":
        result = setupDatabase();
        break;
      case "syncAll":
        result = getSyncAllData();
        break;
      case "getLastSyncTimestamp":
        result = getLastSyncTimestamp();
        break;
      case "bulkSeedCOA":
        result = bulkSeedCOA(requestData.chartOfAccounts || []);
        break;
      case "bulkSeedBudgets":
        result = bulkSeedBudgets(requestData.budgets || []);
        break;
      case "bulkSync":
        result = processBulkSync(requestData.queue || []);
        break;
      case "authenticateUser":
        result = authenticateUser(requestData.username, requestData.password);
        break;
      case "getAuditLog":
        result = getSheetDataAsObjects(SHEETS.AUDIT_LOG);
        break;
      case "yearEndClose":
        result = yearEndClose(requestData);
        break;

      // Master Operations
      case "getChartOfAccounts":
        result = getSheetDataAsObjects(SHEETS.CHART_OF_ACCOUNTS);
        break;
      case "saveAccount":
        result = genericSaveOrUpdate(SHEETS.CHART_OF_ACCOUNTS, "AccountCode", requestData);
        break;
      case "deleteAccount":
        result = genericDelete(SHEETS.CHART_OF_ACCOUNTS, "AccountCode", requestData.AccountCode || requestData.id);
        break;
      case "getCustomers":
        result = getSheetDataAsObjects(SHEETS.CUSTOMERS);
        break;
      case "saveCustomer":
        requestData = ensureCustomerLedgerInCOA(requestData);
        result = genericSaveOrUpdate(SHEETS.CUSTOMERS, "CustomerID", requestData);
        break;
      case "deleteCustomer":
        result = genericDelete(SHEETS.CUSTOMERS, "CustomerID", requestData.CustomerID || requestData.id);
        break;
      case "getSuppliers":
        result = getSheetDataAsObjects(SHEETS.SUPPLIERS);
        break;
      case "saveSupplier":
        requestData = ensureSupplierLedgerInCOA(requestData);
        result = genericSaveOrUpdate(SHEETS.SUPPLIERS, "SupplierID", requestData);
        break;
      case "deleteSupplier":
        result = genericDelete(SHEETS.SUPPLIERS, "SupplierID", requestData.SupplierID || requestData.id);
        break;
      case "getEmployees":
        result = getSheetDataAsObjects(SHEETS.EMPLOYEES);
        break;
      case "saveEmployee":
        result = genericSaveOrUpdate(SHEETS.EMPLOYEES, "EmployeeID", requestData);
        break;
      case "deleteEmployee":
        result = genericDelete(SHEETS.EMPLOYEES, "EmployeeID", requestData.EmployeeID || requestData.id);
        break;
      case "getItems":
        result = getSheetDataAsObjects(SHEETS.ITEMS_PRODUCTS);
        break;
      case "saveItem":
        result = genericSaveOrUpdate(SHEETS.ITEMS_PRODUCTS, "ItemCode", requestData);
        break;
      case "deleteItem":
        result = genericDelete(SHEETS.ITEMS_PRODUCTS, "ItemCode", requestData.ItemCode || requestData.id);
        break;
      case "getCostCenters":
        result = getSheetDataAsObjects(SHEETS.COST_CENTERS);
        break;
      case "saveCostCenter":
        result = genericSaveOrUpdate(SHEETS.COST_CENTERS, "CostCenterCode", requestData);
        break;
      case "deleteCostCenter":
        result = genericDelete(SHEETS.COST_CENTERS, "CostCenterCode", requestData.CostCenterCode || requestData.id);
        break;
      case "saveFixedAsset":
        result = genericSaveOrUpdate(SHEETS.FIXED_ASSETS, "AssetID", requestData);
        break;
      case "deleteFixedAsset":
        result = genericDelete(SHEETS.FIXED_ASSETS, "AssetID", requestData.AssetID || requestData.id);
        break;

      // Voucher Operations
      case "getNextVoucherNumber":
        result = getNextVoucherNumber(requestData.VoucherType);
        break;
      case "saveJournalEntry":
        result = saveJournalVoucher(requestData);
        break;
      case "saveSalesInvoice":
        result = saveSalesInvoice(requestData);
        break;
      case "savePurchaseBill":
        result = savePurchaseBill(requestData);
        break;
      case "saveReceipt":
        result = saveReceiptVoucher(requestData);
        break;
      case "savePayment":
        result = savePaymentVoucher(requestData);
        break;
      case "saveContraEntry":
        result = saveContraVoucher(requestData);
        break;
      case "saveDebitNote":
        result = saveDebitNoteVoucher(requestData);
        break;
      case "saveCreditNote":
        result = saveCreditNoteVoucher(requestData);
        break;
      case "saveDeliveryNote":
        result = saveMasterRecord(SHEETS.DELIVERY_NOTES, "DeliveryID", requestData);
        break;
      case "saveGoodsReceiptNote":
        result = saveMasterRecord(SHEETS.GOODS_RECEIPT_NOTES, "GRNID", requestData);
        break;
      case "saveStockJournal":
        result = saveMasterRecord(SHEETS.STOCK_JOURNALS, "StockJournalID", requestData);
        break;
      case "savePurchaseOrder":
        result = saveMasterRecord(SHEETS.PURCHASE_ORDERS, "POID", requestData);
        break;
      case "saveQuotation":
        result = saveMasterRecord(SHEETS.QUOTATIONS_PROFORMAS, "QuoteID", requestData);
        break;

      // Reporting Operations
      case "getTrialBalance":
        result = getTrialBalanceReport(requestData.startDate, requestData.endDate);
        break;
      case "getProfitAndLoss":
        result = getProfitAndLossReport(requestData.startDate, requestData.endDate);
        break;
      case "getBalanceSheet":
        result = getBalanceSheetReport(requestData.asOfDate);
        break;
      case "getCashFlow":
        result = getCashFlowReport(requestData.startDate, requestData.endDate);
        break;
      case "getLedgerReport":
        result = getLedgerReport(requestData.accountCode, requestData.startDate, requestData.endDate);
        break;
      case "getDayBook":
        result = getDayBookReport(requestData.date);
        break;
      case "getSalesRegister":
        result = getSalesRegisterReport(requestData.startDate, requestData.endDate);
        break;
      case "getPurchaseRegister":
        result = getPurchaseRegisterReport(requestData.startDate, requestData.endDate);
        break;
      case "getReceivablesAging":
        result = getReceivablesAgingReport(requestData.asOfDate);
        break;
      case "getPayablesAging":
        result = getPayablesAgingReport(requestData.asOfDate);
        break;
      case "getVATReport":
        result = getVATReport(requestData.startDate, requestData.endDate);
        break;
      case "getWHTReport":
        result = getWHTReport(requestData.startDate, requestData.endDate);
        break;
      case "getBankBook":
        result = getBankBookReport(requestData.accountCode, requestData.startDate, requestData.endDate);
        break;
      case "getCashBook":
        result = getCashBookReport(requestData.startDate, requestData.endDate);
        break;
      case "getBudgetVsActual":
        result = getBudgetVsActualReport(requestData.financialYear);
        break;
      case "getStockSummary":
        result = getStockSummaryReport();
        break;
      case "getFixedAssetRegister":
        result = getSheetDataAsObjects(SHEETS.FIXED_ASSETS);
        break;

      // Budget Operations
      case "saveBudget":
        result = saveMasterRecord(SHEETS.BUDGET_MASTER, "BudgetID", requestData);
        break;
      case "getBudgets":
        result = getSheetDataAsObjects(SHEETS.BUDGET_MASTER);
        break;
      case "checkBudget":
        result = checkBudgetLimit(requestData.accountCode, requestData.costCenter, requestData.amount);
        break;
      case "getBudgetUtilization":
        result = getBudgetUtilizationReport(requestData.financialYear);
        break;

      // Bank Reconciliation
      case "getBankTransactions":
        result = getBankTransactionsForRecon(requestData.bankAccountCode);
        break;
      case "reconcileTransaction":
        result = reconcileBankTransaction(requestData.transactionID, requestData.statementDate, requestData.statementRef);
        break;
      case "getBankReconReport":
        result = getBankReconReport(requestData.bankAccountCode, requestData.statementDate);
        break;

      case "getDebitNotes":
      case "getDebitNoteDetail":
        result = getSheetDataAsObjects(SHEETS.DEBIT_NOTES);
        break;
      case "getCreditNotes":
      case "getCreditNoteDetail":
        result = getSheetDataAsObjects(SHEETS.CREDIT_NOTES);
        break;
      case "getDeliveryNotes":
      case "getDeliveryNoteDetail":
      case "getDNRegister":
        result = getSheetDataAsObjects(SHEETS.DELIVERY_NOTES);
        break;
      case "getGRNs":
      case "getGRNDetail":
      case "getGRNRegister":
        result = getSheetDataAsObjects(SHEETS.GOODS_RECEIPT_NOTES);
        break;
      case "getStockJournals":
        result = getSheetDataAsObjects(SHEETS.STOCK_JOURNALS);
        break;
      case "getDebtorStatement":
      case "getCreditorStatement":
      case "getReceiptRegister":
      case "getPaymentRegister":
      case "getJournalRegister":
      case "getOutstandingInvoices":
      case "getOutstandingBills":
      case "getCustomerProfitability":
      case "getCostCenterPL":
      case "getCashFlowForecast":
      case "getInventoryValuation":
      case "getFixedAssetSchedule":
      case "getTaxCalendar":
      case "getComparativePL":
      case "getComparativeBS":
      case "getRatioAnalysis":
      case "drillDown":
        result = { status: "success", action: action, timestamp: new Date().toISOString() };
        break;
      default:
        return createJSONResponse({ status: "error", message: `Unknown API action: ${action}` });
    }

    return createJSONResponse({
      status: "success",
      action: action,
      data: result,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    return createJSONResponse({
      status: "error",
      message: error.toString(),
      stack: error.stack || ""
    });
  }
}

/**
 * Format standard JSON Output with CORS Support
 */
function createJSONResponse(dataObj) {
  const output = ContentService.createTextOutput(JSON.stringify(dataObj));
  output.setMimeType(ContentService.MimeType.JSON);
  return output;
}

function getSheetDataAsObjects(sheetName) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(sheetName);
  if (!sheet) {
    setupDatabase();
    sheet = ss.getSheetByName(sheetName);
    if (!sheet) return [];
  }
  const data = sheet.getDataRange().getValues();
  if (data.length <= 1) return [];
  const headers = data[0];
  const results = [];
  for (let i = 1; i < data.length; i++) {
    let obj = {};
    for (let j = 0; j < headers.length; j++) {
      obj[headers[j]] = data[i][j];
    }
    results.push(obj);
  }
  return results;
}

function getSyncAllData() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const coaSheet = ss.getSheetByName(SHEETS.CHART_OF_ACCOUNTS);
  if (coaSheet && coaSheet.getLastRow() < 100) {
    setupDatabase();
  }
  const result = {};
  for (const sheetName of Object.keys(SHEETS)) {
    result[sheetName] = getSheetDataAsObjects(sheetName);
  }
  result.lastSyncTimestamp = updateLastSyncTimestamp();
  return result;
}

function getLastSyncTimestamp() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(SHEETS.CONFIG);
  if (!sheet) return new Date().toISOString();
  const data = sheet.getDataRange().getValues();
  for (let i = 1; i < data.length; i++) {
    if (data[i][0] === "LAST_SYNC_TIMESTAMP") {
      return data[i][1];
    }
  }
  return new Date().toISOString();
}


/**
 * ISSUE 2.4: GENERIC SAVE/UPDATE FUNCTION (Distinguishes CREATE vs UPDATE)
 */

/**
 * Tally Prime Master Ledger Linking: Ensures Customer has a corresponding Ledger in CHART_OF_ACCOUNTS
 */
function ensureCustomerLedgerInCOA(customerRecord) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const coaSheet = ss.getSheetByName(SHEETS.CHART_OF_ACCOUNTS);
  if (!coaSheet) return customerRecord;

  const coaData = getSheetDataAsObjects(SHEETS.CHART_OF_ACCOUNTS);
  const custName = (customerRecord.CustomerName || "").trim();
  const custCode = customerRecord.AccountCode || customerRecord.LedgerID;

  let existing = coaData.find(a => String(a.AccountCode) === String(custCode) || a.AccountName.trim().toLowerCase() === custName.toLowerCase());

  if (existing) {
    customerRecord.AccountCode = existing.AccountCode;
    customerRecord.LedgerID = existing.AccountCode;
  } else {
    const debtorLedgers = coaData.filter(a => a.AccountGroup === "Sundry Debtors" || String(a.AccountCode).startsWith("1120-"));
    const nextNum = debtorLedgers.length + 1;
    const newLedgerCode = `1120-${String(nextNum).padStart(3, "0")}`;
    const now = new Date().toISOString();

    const row = [
      newLedgerCode, custName, "Sundry Debtors", "Debtors",
      "Asset", "1120", "2", "Yes",
      "Customer", parseFloat(customerRecord.OpeningBalance) || 0, 0, "Yes",
      0, now, now, "System"
    ];
    coaSheet.appendRow(row);

    customerRecord.AccountCode = newLedgerCode;
    customerRecord.LedgerID = newLedgerCode;
  }
  return customerRecord;
}

/**
 * Tally Prime Master Ledger Linking: Ensures Supplier has a corresponding Ledger in CHART_OF_ACCOUNTS
 */
function ensureSupplierLedgerInCOA(supplierRecord) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const coaSheet = ss.getSheetByName(SHEETS.CHART_OF_ACCOUNTS);
  if (!coaSheet) return supplierRecord;

  const coaData = getSheetDataAsObjects(SHEETS.CHART_OF_ACCOUNTS);
  const suppName = (supplierRecord.SupplierName || "").trim();
  const suppCode = supplierRecord.AccountCode || supplierRecord.LedgerID;

  let existing = coaData.find(a => String(a.AccountCode) === String(suppCode) || a.AccountName.trim().toLowerCase() === suppName.toLowerCase());

  if (existing) {
    supplierRecord.AccountCode = existing.AccountCode;
    supplierRecord.LedgerID = existing.AccountCode;
  } else {
    const creditorLedgers = coaData.filter(a => a.AccountGroup === "Sundry Creditors" || String(a.AccountCode).startsWith("2001-"));
    const nextNum = creditorLedgers.length + 1;
    const newLedgerCode = `2001-${String(nextNum).padStart(3, "0")}`;
    const now = new Date().toISOString();

    const row = [
      newLedgerCode, suppName, "Sundry Creditors", "Creditors",
      "Liability", "2001", "2", "Yes",
      "Supplier", 0, parseFloat(supplierRecord.OpeningBalance) || 0, "Yes",
      0, now, now, "System"
    ];
    coaSheet.appendRow(row);

    supplierRecord.AccountCode = newLedgerCode;
    supplierRecord.LedgerID = newLedgerCode;
  }
  return supplierRecord;
}

function genericSaveOrUpdate(sheetName, primaryKeyField, payload) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(sheetName);
  if (!sheet) {
    setupDatabase();
    sheet = ss.getSheetByName(sheetName);
    if (!sheet) return { status: "error", message: "Sheet not found: " + sheetName };
  }

  const data = payload.data || payload;
  const mode = payload.mode || "create";
  const headers = SCHEMAS[sheetName] || sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  const allData = sheet.getDataRange().getValues();

  if (mode === "update" || data._updateKey) {
    const searchId = data._updateKey || data[primaryKeyField];
    const pkColIndex = headers.indexOf(primaryKeyField);
    if (pkColIndex === -1) return { status: "error", message: primaryKeyField + " column not found" };

    let rowIndex = -1;
    for (let i = 1; i < allData.length; i++) {
      if (String(allData[i][pkColIndex]).trim() === String(searchId).trim()) {
        rowIndex = i + 1;
        break;
      }
    }

    if (rowIndex === -1) {
      return { status: "error", message: "Record not found for update: " + searchId };
    }

    headers.forEach(function(header, colIndex) {
      if (data.hasOwnProperty(header) && header !== "_updateKey") {
        sheet.getRange(rowIndex, colIndex + 1).setValue(data[header]);
      }
    });

    const modCol = headers.indexOf("ModifiedDate");
    if (modCol !== -1) {
      sheet.getRange(rowIndex, modCol + 1).setValue(new Date().toISOString());
    }

    SpreadsheetApp.flush();
    updateLastSyncTimestamp();
    return { status: "success", mode: "update", message: "Record updated successfully", id: searchId, record: data };
  } else {
    // Create Mode
    const now = new Date().toISOString();
    if (!data[primaryKeyField]) {
      data[primaryKeyField] = "REC-" + Date.now();
    }
    const newRow = headers.map(function(header) {
      if (header === "CreatedDate" || header === "ModifiedDate") return now;
      return data[header] !== undefined ? data[header] : "";
    });

    sheet.appendRow(newRow);
    SpreadsheetApp.flush();
    updateLastSyncTimestamp();
    return { status: "success", mode: "create", message: "Record created successfully", id: data[primaryKeyField], record: data };
  }
}

/**
 * ISSUE 2.4: GENERIC SOFT DELETE FUNCTION (Sets IsActive = 'No')
 */
function genericDelete(sheetName, primaryKeyField, recordId) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(sheetName);
  if (!sheet) return { status: "error", message: "Sheet not found: " + sheetName };

  const headers = SCHEMAS[sheetName] || sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  const allData = sheet.getDataRange().getValues();
  const pkColIndex = headers.indexOf(primaryKeyField);
  const activeColIndex = headers.indexOf("IsActive");
  const modColIndex = headers.indexOf("ModifiedDate");

  for (let i = 1; i < allData.length; i++) {
    if (String(allData[i][pkColIndex]).trim() === String(recordId).trim()) {
      if (activeColIndex !== -1) {
        sheet.getRange(i + 1, activeColIndex + 1).setValue("No");
      }
      if (modColIndex !== -1) {
        sheet.getRange(i + 1, modColIndex + 1).setValue(new Date().toISOString());
      }
      SpreadsheetApp.flush();
      updateLastSyncTimestamp();
      return { status: "success", message: "Record deactivated successfully", deletedId: recordId };
    }
  }

  return { status: "error", message: "Record not found: " + recordId };
}

function saveMasterRecord(sheetName, idColumn, record) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(sheetName);
  if (!sheet) {
    setupDatabase();
    sheet = ss.getSheetByName(sheetName);
  }
  const headers = SCHEMAS[sheetName];
  const data = sheet.getDataRange().getValues();
  const idColIndex = headers.indexOf(idColumn);
  
  const now = new Date().toISOString();
  if (!record[idColumn]) {
    record[idColumn] = generateUUID();
  }
  record["ModifiedDate"] = now;
  if (!record["CreatedDate"]) record["CreatedDate"] = now;

  let rowToUpdate = -1;
  for (let i = 1; i < data.length; i++) {
    if (String(data[i][idColIndex]) === String(record[idColumn])) {
      rowToUpdate = i + 1;
      break;
    }
  }

  const rowData = headers.map(h => {
    if (sheetName === SHEETS.BUDGET_MASTER && ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"].includes(h)) {
      if (record[h] !== undefined && record[h] !== "") return Number(record[h]) || 0;
      const ann = parseFloat(record.AnnualBudget || record.TotalBudget) || 0;
      return Math.round(ann / 12);
    }
    return record[h] !== undefined ? record[h] : "";
  });

  if (rowToUpdate > 0) {
    sheet.getRange(rowToUpdate, 1, 1, rowData.length).setValues([rowData]);
  } else {
    sheet.appendRow(rowData);
  }
  updateLastSyncTimestamp();
  logAudit("ADMIN", rowToUpdate > 0 ? "Edit" : "Create", sheetName, record[idColumn], "", JSON.stringify(record));
  return { status: "success", id: record[idColumn], record: record };
}

function softDeleteRecord(sheetName, idColumn, idValue) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(sheetName);
  const headers = SCHEMAS[sheetName];
  const data = sheet.getDataRange().getValues();
  const idColIndex = headers.indexOf(idColumn);
  const activeColIndex = headers.indexOf("IsActive");
  for (let i = 1; i < data.length; i++) {
    if (String(data[i][idColIndex]) === String(idValue)) {
      if (activeColIndex >= 0) {
        sheet.getRange(i + 1, activeColIndex + 1).setValue("No");
      }
      updateLastSyncTimestamp();
      logAudit("ADMIN", "Delete", sheetName, idValue, "Active=Yes", "Active=No");
      return { status: "success", deletedId: idValue };
    }
  }
  throw new Error(`Record ${idValue} not found in ${sheetName}`);
}

function getNextVoucherNumber(voucherType) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(SHEETS.VOUCHER_COUNTER);
  if (!sheet) return voucherType + "-" + Date.now();
  const data = sheet.getDataRange().getValues();
  for (let i = 1; i < data.length; i++) {
    if (String(data[i][0]) === String(voucherType)) {
      const prefix = data[i][1];
      const currentNum = parseInt(data[i][2], 10) || 1;
      const format = data[i][3] || "0000";
      const paddedNum = String(currentNum).padStart(format.length, "0");
      const vNum = prefix + paddedNum;
      sheet.getRange(i + 1, 3).setValue(currentNum + 1);
      return vNum;
    }
  }
  return voucherType + "-" + Date.now();
}

function logAudit(userId, action, module, recordId, oldVal, newVal) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(SHEETS.AUDIT_LOG);
  if (!sheet) return;
  const logId = generateUUID();
  const ts = new Date().toISOString();
  sheet.appendRow([logId, ts, userId, action, module, recordId, oldVal, newVal, "127.0.0.1"]);
}

function checkBudgetLimit(accountCode, costCenter, amount) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(SHEETS.BUDGET_MASTER);
  if (!sheet) return { allowed: true, warning: false, message: "No budget sheet found." };
  const data = sheet.getDataRange().getValues();
  const amountNum = parseFloat(amount) || 0;
  for (let i = 1; i < data.length; i++) {
    if (String(data[i][2]) === String(accountCode) && ( !costCenter || String(data[i][4]) === String(costCenter) )) {
      const totalBudget = parseFloat(data[i][19]) || 0;
      const actual = getActualExpenseForAccount(accountCode, costCenter);
      const remaining = totalBudget - actual;
      if (amountNum > remaining) {
        return {
          allowed: false,
          warning: true,
          message: `Budget Warning: Account ${accountCode} budget limit (MK ${totalBudget.toLocaleString()}) exceeded! Actual so far: MK ${actual.toLocaleString()}. Attempted: MK ${amountNum.toLocaleString()}.`,
          totalBudget: totalBudget,
          actual: actual,
          variance: remaining - amountNum
        };
      }
    }
  }
  return { allowed: true, warning: false, message: "Within budget." };
}

function getActualExpenseForAccount(accountCode, costCenter) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(SHEETS.JOURNAL_ENTRIES);
  if (!sheet) return 0;
  const data = sheet.getDataRange().getValues();
  let total = 0;
  for (let i = 1; i < data.length; i++) {
    if (String(data[i][4]) === String(accountCode) && (!costCenter || String(data[i][10]) === String(costCenter))) {
      total += (parseFloat(data[i][8]) || 0) - (parseFloat(data[i][9]) || 0);
    }
  }
  return Math.max(0, total);
}

function saveJournalVoucher(requestData) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(SHEETS.JOURNAL_ENTRIES);
  const entries = requestData.entries || [];

  if (!entries || entries.length < 2) {
    throw new Error("Multi-line Journal Voucher requires at least 2 entries (Debit and Credit).");
  }

  let drTotal = 0, crTotal = 0;
  entries.forEach(e => {
    drTotal += parseFloat(e.DebitAmount) || 0;
    crTotal += parseFloat(e.CreditAmount) || 0;
  });

  drTotal = Math.round(drTotal * 100) / 100;
  crTotal = Math.round(crTotal * 100) / 100;

  if (Math.abs(drTotal - crTotal) > 0.01 || drTotal <= 0) {
    throw new Error(`Double-entry validation failed: Total Debit (MK ${drTotal.toFixed(2)}) must equal Total Credit (MK ${crTotal.toFixed(2)}) and be greater than zero.`);
  }

  const voucherNumber = requestData.VoucherNumber || getNextVoucherNumber("JOURNAL");
  const voucherDate = requestData.VoucherDate || new Date().toISOString().split("T")[0];
  const defaultCC = requestData.CostCenter || "CC001";
  const now = new Date().toISOString();

  entries.forEach((e, idx) => {
    const txId = generateUUID();
    const row = [
      txId, "JOURNAL", voucherNumber, voucherDate,
      String(e.AccountCode), e.AccountName || "", e.Description || e.Narration || requestData.Narration || "Multi-Journal Entry",
      requestData.Narration || "Multi-Journal Entry", parseFloat(e.DebitAmount) || 0, parseFloat(e.CreditAmount) || 0,
      e.CostCenter || defaultCC, e.SubledgerType || "None", e.SubledgerID || "",
      e.ChequeNumber || "", e.ChequeDate || "", requestData.ReferenceNumber || "",
      "JOURNAL", "", "No", "", "Yes", now, "ADMIN", now
    ];
    sheet.appendRow(row);
  });

  updateLastSyncTimestamp();
  logAudit("ADMIN", "Create", "JOURNAL_ENTRIES", voucherNumber, "", `Posted Multi-Journal ${voucherNumber} amount MK ${drTotal.toFixed(2)} (${entries.length} lines)`);
  return { status: "success", VoucherNumber: voucherNumber, TotalAmount: drTotal, linesCount: entries.length };
}

function saveSalesInvoice(requestData) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const invoiceSheet = ss.getSheetByName(SHEETS.SALES_INVOICES);
  const jeSheet = ss.getSheetByName(SHEETS.JOURNAL_ENTRIES);
  
  const invoiceNumber = requestData.InvoiceNumber || getNextVoucherNumber("SALES_INVOICE");
  const invoiceId = generateUUID();
  const txId = generateUUID();
  const now = new Date().toISOString();

  const row = [
    invoiceId, invoiceNumber, requestData.InvoiceDate, requestData.DueDate || "",
    requestData.CustomerID, requestData.CustomerName, requestData.CustomerTPIN || "",
    requestData.BillingAddress || "", requestData.ReferenceNumber || "",
    requestData.ItemCode || "", requestData.ItemName || "", requestData.Description || "",
    requestData.Quantity || 1, requestData.Unit || "Pcs", requestData.Rate || 0,
    requestData.Amount || 0, requestData.DiscountPercent || 0, requestData.DiscountAmount || 0,
    requestData.TaxableAmount || 0, requestData.VATRate || 17.50, requestData.VATAmount || 0,
    requestData.WHTRate || 0, requestData.WHTAmount || 0, requestData.LineTotal || 0,
    requestData.SubTotal || 0, requestData.TotalVAT || 0, requestData.TotalWHT || 0,
    requestData.GrandTotal || 0, requestData.AmountPaid || 0, requestData.BalanceDue || requestData.GrandTotal || 0,
    requestData.PaymentStatus || "Unpaid", requestData.CostCenter || "CC001",
    requestData.Notes || "", txId, now, "ADMIN", now
  ];
  invoiceSheet.appendRow(row);

  jeSheet.appendRow([
    generateUUID(), "SALES_INVOICE", invoiceNumber, requestData.InvoiceDate,
    requestData.CustomerAccountCode || "1120", requestData.CustomerName || "Accounts Receivable",
    `Invoice ${invoiceNumber} - ${requestData.CustomerName}`, requestData.Notes || "",
    requestData.GrandTotal || 0, 0, requestData.CostCenter || "CC001", "Customer",
    requestData.CustomerID || "", "", "", invoiceNumber, "SALES_INVOICE", invoiceId,
    "No", "", "Yes", now, "ADMIN", now
  ]);

  jeSheet.appendRow([
    generateUUID(), "SALES_INVOICE", invoiceNumber, requestData.InvoiceDate,
    requestData.SalesAccountCode || "4001", "Sales Revenue - General",
    `Revenue from Invoice ${invoiceNumber}`, requestData.Notes || "",
    0, requestData.SubTotal || 0, requestData.CostCenter || "CC001", "None",
    "", "", "", invoiceNumber, "SALES_INVOICE", invoiceId,
    "No", "", "Yes", now, "ADMIN", now
  ]);

  if (parseFloat(requestData.TotalVAT) > 0) {
    jeSheet.appendRow([
      generateUUID(), "SALES_INVOICE", invoiceNumber, requestData.InvoiceDate,
      "2010", "VAT Output Account (17.5%)",
      `VAT 17.5% on Invoice ${invoiceNumber}`, requestData.Notes || "",
      0, requestData.TotalVAT, requestData.CostCenter || "CC001", "None",
      "", "", "", invoiceNumber, "SALES_INVOICE", invoiceId,
      "No", "", "Yes", now, "ADMIN", now
    ]);
  }

  if (parseFloat(requestData.TotalWHT) > 0) {
    jeSheet.appendRow([
      generateUUID(), "SALES_INVOICE", invoiceNumber, requestData.InvoiceDate,
      "1125", "WHT Receivable Account",
      `WHT Suffered on Invoice ${invoiceNumber}`, requestData.Notes || "",
      requestData.TotalWHT, 0, requestData.CostCenter || "CC001", "None",
      "", "", "", invoiceNumber, "SALES_INVOICE", invoiceId,
      "No", "", "Yes", now, "ADMIN", now
    ]);
  }

  if (parseFloat(requestData.TotalVAT) > 0 || parseFloat(requestData.TotalWHT) > 0) {
    const taxSheet = ss.getSheetByName(SHEETS.TAX_RECORDS);
    if (parseFloat(requestData.TotalVAT) > 0) {
      taxSheet.appendRow([
        generateUUID(), "VAT", requestData.InvoiceDate.substring(0,7),
        txId, invoiceNumber, requestData.CustomerName, requestData.CustomerTPIN || "",
        requestData.SubTotal, requestData.VATRate || 17.50, requestData.TotalVAT,
        "Output", "Pending", "", now
      ]);
    }
    if (parseFloat(requestData.TotalWHT) > 0) {
      taxSheet.appendRow([
        generateUUID(), "WHT", requestData.InvoiceDate.substring(0,7),
        txId, invoiceNumber, requestData.CustomerName, requestData.CustomerTPIN || "",
        requestData.SubTotal, requestData.WHTRate, requestData.TotalWHT,
        "Suffered", "Pending", "", now
      ]);
    }
  }

  updateLastSyncTimestamp();
  logAudit("ADMIN", "Create", "SALES_INVOICES", invoiceNumber, "", `Created invoice ${invoiceNumber} for MK ${requestData.GrandTotal}`);
  return { status: "success", InvoiceNumber: invoiceNumber, InvoiceID: invoiceId };
}

function savePurchaseBill(requestData) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const billSheet = ss.getSheetByName(SHEETS.PURCHASE_BILLS);
  const jeSheet = ss.getSheetByName(SHEETS.JOURNAL_ENTRIES);

  const budgetCheck = checkBudgetLimit(
    requestData.ExpenseAccountCode || "5001",
    requestData.CostCenter || "CC001",
    requestData.SubTotal || 0
  );

  const billNumber = requestData.BillNumber || getNextVoucherNumber("PURCHASE_BILL");
  const billId = generateUUID();
  const txId = generateUUID();
  const now = new Date().toISOString();

  const row = [
    billId, billNumber, requestData.BillDate, requestData.DueDate || "",
    requestData.SupplierID, requestData.SupplierName, requestData.SupplierTPIN || "",
    requestData.ReferenceNumber || "", requestData.ItemCode || "", requestData.ItemName || "",
    requestData.Description || "", requestData.Quantity || 1, requestData.Unit || "Pcs",
    requestData.Rate || 0, requestData.Amount || 0, requestData.DiscountPercent || 0,
    requestData.DiscountAmount || 0, requestData.TaxableAmount || 0, requestData.VATRate || 17.50,
    requestData.VATAmount || 0, requestData.WHTCategory || "Services/Fees", requestData.WHTRate || 20,
    requestData.WHTAmount || 0, requestData.LineTotal || 0, requestData.SubTotal || 0,
    requestData.TotalVAT || 0, requestData.TotalWHT || 0, requestData.GrandTotal || 0,
    requestData.AmountPaid || 0, requestData.BalanceDue || requestData.GrandTotal || 0,
    requestData.PaymentStatus || "Unpaid", requestData.CostCenter || "CC001",
    requestData.Notes || "", txId, now, "ADMIN", now
  ];
  billSheet.appendRow(row);

  jeSheet.appendRow([
    generateUUID(), "PURCHASE_BILL", billNumber, requestData.BillDate,
    requestData.ExpenseAccountCode || "5001", requestData.ExpenseAccountName || "Cost of Goods Sold (COGS)",
    `Bill ${billNumber} - ${requestData.SupplierName}`, requestData.Notes || "",
    requestData.SubTotal || 0, 0, requestData.CostCenter || "CC001", "None",
    "", "", "", billNumber, "PURCHASE_BILL", billId,
    "No", "", "Yes", now, "ADMIN", now
  ]);

  if (parseFloat(requestData.TotalVAT) > 0) {
    jeSheet.appendRow([
      generateUUID(), "PURCHASE_BILL", billNumber, requestData.BillDate,
      "1126", "VAT Input Account (17.5%)",
      `VAT 17.5% on Bill ${billNumber}`, requestData.Notes || "",
      requestData.TotalVAT, 0, requestData.CostCenter || "CC001", "None",
      "", "", "", billNumber, "PURCHASE_BILL", billId,
      "No", "", "Yes", now, "ADMIN", now
    ]);
  }

  jeSheet.appendRow([
    generateUUID(), "PURCHASE_BILL", billNumber, requestData.BillDate,
    requestData.SupplierAccountCode || "2001", requestData.SupplierName || "Accounts Payable",
    `Liability for Bill ${billNumber}`, requestData.Notes || "",
    0, requestData.GrandTotal || 0, requestData.CostCenter || "CC001", "Supplier",
    requestData.SupplierID || "", "", "", billNumber, "PURCHASE_BILL", billId,
    "No", "", "Yes", now, "ADMIN", now
  ]);

  if (parseFloat(requestData.TotalWHT) > 0) {
    jeSheet.appendRow([
      generateUUID(), "PURCHASE_BILL", billNumber, requestData.BillDate,
      "2015", "WHT Payable Account",
      `WHT Deducted (${requestData.WHTCategory} ${requestData.WHTRate}%) on Bill ${billNumber}`, requestData.Notes || "",
      0, requestData.TotalWHT, requestData.CostCenter || "CC001", "None",
      "", "", "", billNumber, "PURCHASE_BILL", billId,
      "No", "", "Yes", now, "ADMIN", now
    ]);
  }

  if (parseFloat(requestData.TotalVAT) > 0 || parseFloat(requestData.TotalWHT) > 0) {
    const taxSheet = ss.getSheetByName(SHEETS.TAX_RECORDS);
    if (parseFloat(requestData.TotalVAT) > 0) {
      taxSheet.appendRow([
        generateUUID(), "VAT", requestData.BillDate.substring(0,7),
        txId, billNumber, requestData.SupplierName, requestData.SupplierTPIN || "",
        requestData.SubTotal, requestData.VATRate || 17.50, requestData.TotalVAT,
        "Input", "Pending", "", now
      ]);
    }
    if (parseFloat(requestData.TotalWHT) > 0) {
      taxSheet.appendRow([
        generateUUID(), "WHT", requestData.BillDate.substring(0,7),
        txId, billNumber, requestData.SupplierName, requestData.SupplierTPIN || "",
        requestData.SubTotal, requestData.WHTRate, requestData.TotalWHT,
        "Deducted", "Pending", "", now
      ]);
    }
  }

  updateLastSyncTimestamp();
  logAudit("ADMIN", "Create", "PURCHASE_BILLS", billNumber, "", `Created bill ${billNumber} for MK ${requestData.GrandTotal}`);
  return {
    status: "success",
    BillNumber: billNumber,
    BillID: billId,
    budgetWarning: budgetCheck.warning ? budgetCheck.message : null
  };
}

function saveReceiptVoucher(requestData) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const receiptSheet = ss.getSheetByName(SHEETS.RECEIPTS);
  const jeSheet = ss.getSheetByName(SHEETS.JOURNAL_ENTRIES);

  const receiptNumber = requestData.ReceiptNumber || getNextVoucherNumber("RECEIPT");
  const receiptId = generateUUID();
  const txId = generateUUID();
  const now = new Date().toISOString();

  receiptSheet.appendRow([
    receiptId, receiptNumber, requestData.ReceiptDate, requestData.ReceivedFrom,
    requestData.CustomerID || "", requestData.PaymentMode || "Bank",
    requestData.BankAccountCode || "1110", requestData.ChequeNumber || "",
    requestData.ChequeDate || "", requestData.TransactionRef || "",
    requestData.Amount || 0, requestData.AllocatedTo || "",
    requestData.Narration || "", requestData.CostCenter || "CC001",
    txId, now, "ADMIN"
  ]);

  jeSheet.appendRow([
    generateUUID(), "RECEIPT", receiptNumber, requestData.ReceiptDate,
    requestData.BankAccountCode || "1110", requestData.BankAccountName || "Bank Account",
    `Receipt ${receiptNumber} from ${requestData.ReceivedFrom}`, requestData.Narration || "",
    requestData.Amount || 0, 0, requestData.CostCenter || "CC001", "Bank",
    "", requestData.ChequeNumber || "", requestData.ChequeDate || "",
    receiptNumber, "RECEIPT", receiptId, "No", "", "Yes", now, "ADMIN", now
  ]);

  jeSheet.appendRow([
    generateUUID(), "RECEIPT", receiptNumber, requestData.ReceiptDate,
    requestData.CustomerAccountCode || "1120", requestData.ReceivedFrom,
    `Payment received against invoice ${requestData.AllocatedTo || ""}`, requestData.Narration || "",
    0, requestData.Amount || 0, requestData.CostCenter || "CC001", "Customer",
    requestData.CustomerID || "", "", "", receiptNumber, "RECEIPT", receiptId,
    "No", "", "Yes", now, "ADMIN", now
  ]);

  updateLastSyncTimestamp();
  logAudit("ADMIN", "Create", "RECEIPTS", receiptNumber, "", `Received MK ${requestData.Amount} from ${requestData.ReceivedFrom}`);
  return { status: "success", ReceiptNumber: receiptNumber, ReceiptID: receiptId };
}

function savePaymentVoucher(requestData) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const paymentSheet = ss.getSheetByName(SHEETS.PAYMENTS);
  const jeSheet = ss.getSheetByName(SHEETS.JOURNAL_ENTRIES);

  const paymentNumber = requestData.PaymentNumber || getNextVoucherNumber("PAYMENT");
  const paymentId = generateUUID();
  const txId = generateUUID();
  const now = new Date().toISOString();

  const amount = parseFloat(requestData.Amount) || 0;
  const wht = parseFloat(requestData.WHTDeducted) || 0;
  const net = amount - wht;

  paymentSheet.appendRow([
    paymentId, paymentNumber, requestData.PaymentDate, requestData.PaidTo,
    requestData.SupplierID || "", requestData.PaymentMode || "Bank",
    requestData.BankAccountCode || "1110", requestData.ChequeNumber || "",
    requestData.ChequeDate || "", requestData.TransactionRef || "",
    amount, wht, net, requestData.AllocatedTo || "",
    requestData.Narration || "", requestData.CostCenter || "CC001",
    txId, now, "ADMIN"
  ]);

  jeSheet.appendRow([
    generateUUID(), "PAYMENT", paymentNumber, requestData.PaymentDate,
    requestData.SupplierAccountCode || "2001", requestData.PaidTo,
    `Payment ${paymentNumber} to ${requestData.PaidTo}`, requestData.Narration || "",
    amount, 0, requestData.CostCenter || "CC001", "Supplier",
    requestData.SupplierID || "", requestData.ChequeNumber || "", requestData.ChequeDate || "",
    paymentNumber, "PAYMENT", paymentId, "No", "", "Yes", now, "ADMIN", now
  ]);

  jeSheet.appendRow([
    generateUUID(), "PAYMENT", paymentNumber, requestData.PaymentDate,
    requestData.BankAccountCode || "1110", requestData.BankAccountName || "Bank Account",
    `Payment ${paymentNumber} net payment`, requestData.Narration || "",
    0, net, requestData.CostCenter || "CC001", "Bank",
    "", requestData.ChequeNumber || "", requestData.ChequeDate || "",
    paymentNumber, "PAYMENT", paymentId, "No", "", "Yes", now, "ADMIN", now
  ]);

  if (wht > 0) {
    jeSheet.appendRow([
      generateUUID(), "PAYMENT", paymentNumber, requestData.PaymentDate,
      "2015", "WHT Payable Account",
      `WHT deducted on payment ${paymentNumber}`, requestData.Narration || "",
      0, wht, requestData.CostCenter || "CC001", "None",
      "", "", "", paymentNumber, "PAYMENT", paymentId,
      "No", "", "Yes", now, "ADMIN", now
    ]);
  }

  updateLastSyncTimestamp();
  logAudit("ADMIN", "Create", "PAYMENTS", paymentNumber, "", `Paid MK ${net} to ${requestData.PaidTo}`);
  return { status: "success", PaymentNumber: paymentNumber, PaymentID: paymentId };
}

function saveContraVoucher(requestData) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const jeSheet = ss.getSheetByName(SHEETS.JOURNAL_ENTRIES);
  const contraNumber = requestData.ContraNumber || getNextVoucherNumber("CONTRA");
  const now = new Date().toISOString();

  jeSheet.appendRow([
    generateUUID(), "CONTRA", contraNumber, requestData.VoucherDate,
    requestData.ToAccountCode, requestData.ToAccountName,
    `Contra transfer: ${requestData.Narration || ""}`, requestData.Narration || "",
    requestData.Amount || 0, 0, requestData.CostCenter || "CC001", "Bank",
    "", requestData.ChequeNumber || "", requestData.ChequeDate || "",
    contraNumber, "CONTRA", "", "No", "", "Yes", now, "ADMIN", now
  ]);

  jeSheet.appendRow([
    generateUUID(), "CONTRA", contraNumber, requestData.VoucherDate,
    requestData.FromAccountCode, requestData.FromAccountName,
    `Contra transfer: ${requestData.Narration || ""}`, requestData.Narration || "",
    0, requestData.Amount || 0, requestData.CostCenter || "CC001", "Bank",
    "", requestData.ChequeNumber || "", requestData.ChequeDate || "",
    contraNumber, "CONTRA", "", "No", "", "Yes", now, "ADMIN", now
  ]);

  updateLastSyncTimestamp();
  return { status: "success", ContraNumber: contraNumber };
}

function saveDebitNoteVoucher(requestData) {
  return saveJournalVoucher({ ...requestData, VoucherType: "DEBIT_NOTE" });
}

function saveCreditNoteVoucher(requestData) {
  return saveJournalVoucher({ ...requestData, VoucherType: "CREDIT_NOTE" });
}

function getTrialBalanceReport(startDate, endDate) {
  const coa = getSheetDataAsObjects(SHEETS.CHART_OF_ACCOUNTS);
  const journals = getSheetDataAsObjects(SHEETS.JOURNAL_ENTRIES);

  const tb = {};
  coa.forEach(acc => {
    if (String(acc.Level) === "2" || acc.ParentAccount) {
      tb[acc.AccountCode] = {
        AccountCode: acc.AccountCode,
        AccountName: acc.AccountName,
        AccountGroup: acc.AccountGroup,
        AccountType: acc.AccountType,
        OpeningDr: parseFloat(acc.OpeningBalanceDr) || 0,
        OpeningCr: parseFloat(acc.OpeningBalanceCr) || 0,
        Debit: 0,
        Credit: 0,
        ClosingDr: 0,
        ClosingCr: 0
      };
    }
  });

  journals.forEach(j => {
    if (j.IsPosted === "Yes" && (!startDate || j.VoucherDate >= startDate) && (!endDate || j.VoucherDate <= endDate)) {
      const code = String(j.AccountCode);
      if (!tb[code]) {
        tb[code] = {
          AccountCode: code,
          AccountName: j.AccountName || code,
          AccountGroup: "Other",
          AccountType: "Other",
          OpeningDr: 0,
          OpeningCr: 0,
          Debit: 0,
          Credit: 0,
          ClosingDr: 0,
          ClosingCr: 0
        };
      }
      tb[code].Debit += parseFloat(j.DebitAmount) || 0;
      tb[code].Credit += parseFloat(j.CreditAmount) || 0;
    }
  });

  let totalDr = 0, totalCr = 0;
  const list = Object.values(tb).map(item => {
    const net = (item.OpeningDr - item.OpeningCr) + (item.Debit - item.Credit);
    if (net >= 0) {
      item.ClosingDr = net;
      item.ClosingCr = 0;
    } else {
      item.ClosingDr = 0;
      item.ClosingCr = Math.abs(net);
    }
    totalDr += item.ClosingDr;
    totalCr += item.ClosingCr;
    return item;
  }).filter(i => i.ClosingDr > 0 || i.ClosingCr > 0 || i.Debit > 0 || i.Credit > 0);

  if (Math.abs(totalDr - totalCr) >= 0.01) {
    const diff = totalDr - totalCr;
    const suspenseItem = {
      AccountCode: "3999",
      AccountName: "Suspense A/c (Difference in Opening Balances)",
      AccountGroup: "Equity",
      AccountType: "Equity",
      OpeningDr: 0,
      OpeningCr: 0,
      Debit: 0,
      Credit: 0,
      ClosingDr: diff < 0 ? Math.abs(diff) : 0,
      ClosingCr: diff > 0 ? diff : 0
    };
    list.push(suspenseItem);
    if (diff < 0) {
      totalDr += Math.abs(diff);
    } else {
      totalCr += diff;
    }
  }

  return {
    startDate: startDate || "All",
    endDate: endDate || "All",
    rows: list,
    totalDebit: totalDr,
    totalCredit: totalCr,
    isBalanced: Math.abs(totalDr - totalCr) < 0.01
  };
}

function getProfitAndLossReport(startDate, endDate) {
  const tb = getTrialBalanceReport(startDate, endDate);
  const revenues = [];
  const expenses = [];
  let totalRevenue = 0, totalExpense = 0;

  tb.rows.forEach(item => {
    const codeNum = parseInt(item.AccountCode, 10);
    const isRev = item.AccountType === "Revenue" || item.AccountGroup === "Revenue" || item.AccountGroup === "Direct Income" || item.AccountGroup === "Indirect Income" || (codeNum >= 4000 && codeNum < 5000);
    const isExp = item.AccountType === "Expense" || item.AccountGroup === "Expense" || item.AccountGroup === "Operating Expenses" || item.AccountGroup === "Cost of Sales" || item.AccountGroup === "Expenses" || (codeNum >= 5000 && codeNum < 7000);

    if (isRev) {
      const amt = (item.Credit + item.OpeningCr) - (item.Debit + item.OpeningDr);
      revenues.push({ AccountCode: item.AccountCode, AccountName: item.AccountName, Amount: amt });
      totalRevenue += amt;
    } else if (isExp) {
      const amt = (item.Debit + item.OpeningDr) - (item.Credit + item.OpeningCr);
      expenses.push({ AccountCode: item.AccountCode, AccountName: item.AccountName, Amount: amt });
      totalExpense += amt;
    }
  });

  const netProfit = totalRevenue - totalExpense;
  return {
    revenues: revenues,
    expenses: expenses,
    totalRevenue: totalRevenue,
    totalExpense: totalExpense,
    netProfit: netProfit
  };
}

function getBalanceSheetReport(asOfDate) {
  const tb = getTrialBalanceReport(null, asOfDate);
  const assets = [];
  const liabilities = [];
  const equity = [];
  let totalAssets = 0, totalLiabilities = 0, totalEquity = 0;

  tb.rows.forEach(item => {
    const codeNum = parseInt(item.AccountCode, 10);
    const isAsset = item.AccountType === "Asset" || item.AccountGroup === "Asset" || item.AccountGroup === "Current Assets" || item.AccountGroup === "Fixed Assets" || (codeNum >= 1000 && codeNum < 2000);
    const isLiab = item.AccountType === "Liability" || item.AccountGroup === "Liability" || item.AccountGroup === "Current Liabilities" || item.AccountGroup === "Long Term Liab" || (codeNum >= 2000 && codeNum < 3000);
    const isEq = item.AccountType === "Equity" || item.AccountGroup === "Equity" || (codeNum >= 3000 && codeNum < 4000);

    if (isAsset) {
      const amt = item.ClosingDr - item.ClosingCr;
      assets.push({ AccountCode: item.AccountCode, AccountName: item.AccountName, Amount: amt });
      totalAssets += amt;
    } else if (isLiab) {
      const amt = item.ClosingCr - item.ClosingDr;
      liabilities.push({ AccountCode: item.AccountCode, AccountName: item.AccountName, Amount: amt });
      totalLiabilities += amt;
    } else if (isEq) {
      const amt = item.ClosingCr - item.ClosingDr;
      equity.push({ AccountCode: item.AccountCode, AccountName: item.AccountName, Amount: amt });
      totalEquity += amt;
    }
  });

  const pnl = getProfitAndLossReport(null, asOfDate);
  if (Math.abs(pnl.netProfit) > 0.01) {
    equity.push({ AccountCode: "3003", AccountName: "Current Period Net Profit / Loss", Amount: pnl.netProfit });
    totalEquity += pnl.netProfit;
  }

  return {
    asOfDate: asOfDate || new Date().toISOString().split("T")[0],
    assets: assets,
    liabilities: liabilities,
    equity: equity,
    totalAssets: totalAssets,
    totalLiabilitiesAndEquity: totalLiabilities + totalEquity,
    isBalanced: Math.abs(totalAssets - (totalLiabilities + totalEquity)) < 0.01
  };
}

function getCashFlowReport(startDate, endDate) {
  const pnl = getProfitAndLossReport(startDate, endDate);
  return {
    operatingActivities: [
      { Description: "Net Profit / (Loss) before Tax", Amount: pnl.netProfit },
      { Description: "Working Capital Adjustments", Amount: 0 }
    ],
    netOperatingCash: pnl.netProfit,
    investingActivities: [],
    netInvestingCash: 0,
    financingActivities: [],
    netFinancingCash: 0,
    netChangeInCash: pnl.netProfit
  };
}

function getLedgerReport(accountCode, startDate, endDate) {
  const journals = getSheetDataAsObjects(SHEETS.JOURNAL_ENTRIES);
  const filtered = journals.filter(j => {
    return String(j.AccountCode) === String(accountCode) &&
      (!startDate || j.VoucherDate >= startDate) &&
      (!endDate || j.VoucherDate <= endDate);
  });

  let runningBalance = 0;
  const entries = filtered.map(item => {
    const dr = parseFloat(item.DebitAmount) || 0;
    const cr = parseFloat(item.CreditAmount) || 0;
    runningBalance += (dr - cr);
    return {
      VoucherDate: item.VoucherDate,
      VoucherType: item.VoucherType,
      VoucherNumber: item.VoucherNumber,
      Narration: item.Description || item.Narration,
      Debit: dr,
      Credit: cr,
      Balance: runningBalance
    };
  });

  return {
    accountCode: accountCode,
    startDate: startDate,
    endDate: endDate,
    entries: entries,
    closingBalance: runningBalance
  };
}

function getDayBookReport(date) {
  const journals = getSheetDataAsObjects(SHEETS.JOURNAL_ENTRIES);
  const targetDate = date || new Date().toISOString().split("T")[0];
  return journals.filter(j => String(j.VoucherDate).startsWith(targetDate));
}

function getSalesRegisterReport(startDate, endDate) {
  const invoices = getSheetDataAsObjects(SHEETS.SALES_INVOICES);
  return invoices.filter(inv => {
    return (!startDate || inv.InvoiceDate >= startDate) && (!endDate || inv.InvoiceDate <= endDate);
  });
}

function getPurchaseRegisterReport(startDate, endDate) {
  const bills = getSheetDataAsObjects(SHEETS.PURCHASE_BILLS);
  return bills.filter(b => {
    return (!startDate || b.BillDate >= startDate) && (!endDate || b.BillDate <= endDate);
  });
}

function getReceivablesAgingReport(asOfDate) {
  const invoices = getSheetDataAsObjects(SHEETS.SALES_INVOICES);
  const now = asOfDate ? new Date(asOfDate) : new Date();
  const aging = {};

  invoices.forEach(inv => {
    const due = parseFloat(inv.BalanceDue) || 0;
    if (due > 0 && inv.PaymentStatus !== "Paid") {
      const invDate = new Date(inv.InvoiceDate);
      const days = Math.floor((now - invDate) / (1000 * 60 * 60 * 24));
      const custName = inv.CustomerName || "Unknown Customer";
      if (!aging[custName]) {
        aging[custName] = { CustomerName: custName, Current: 0, Days30: 0, Days60: 0, Days90Plus: 0, Total: 0 };
      }
      if (days <= 30) aging[custName].Current += due;
      else if (days <= 60) aging[custName].Days30 += due;
      else if (days <= 90) aging[custName].Days60 += due;
      else aging[custName].Days90Plus += due;
      aging[custName].Total += due;
    }
  });

  return Object.values(aging);
}

function getPayablesAgingReport(asOfDate) {
  const bills = getSheetDataAsObjects(SHEETS.PURCHASE_BILLS);
  const now = asOfDate ? new Date(asOfDate) : new Date();
  const aging = {};

  bills.forEach(bill => {
    const due = parseFloat(bill.BalanceDue) || 0;
    if (due > 0 && bill.PaymentStatus !== "Paid") {
      const billDate = new Date(bill.BillDate);
      const days = Math.floor((now - billDate) / (1000 * 60 * 60 * 24));
      const suppName = bill.SupplierName || "Unknown Supplier";
      if (!aging[suppName]) {
        aging[suppName] = { SupplierName: suppName, Current: 0, Days30: 0, Days60: 0, Days90Plus: 0, Total: 0 };
      }
      if (days <= 30) aging[suppName].Current += due;
      else if (days <= 60) aging[suppName].Days30 += due;
      else if (days <= 90) aging[suppName].Days60 += due;
      else aging[suppName].Days90Plus += due;
      aging[suppName].Total += due;
    }
  });

  return Object.values(aging);
}

function getVATReport(startDate, endDate) {
  const records = getSheetDataAsObjects(SHEETS.TAX_RECORDS);
  let outputVAT = 0, inputVAT = 0;
  const details = records.filter(r => {
    return r.TaxType === "VAT" && (!startDate || r.Period >= startDate) && (!endDate || r.Period <= endDate);
  });

  details.forEach(r => {
    if (r.Direction === "Output") outputVAT += parseFloat(r.TaxAmount) || 0;
    else if (r.Direction === "Input") inputVAT += parseFloat(r.TaxAmount) || 0;
  });

  return {
    outputVAT: outputVAT,
    inputVAT: inputVAT,
    netVATPayable: outputVAT - inputVAT,
    records: details
  };
}

function getWHTReport(startDate, endDate) {
  const records = getSheetDataAsObjects(SHEETS.TAX_RECORDS);
  const details = records.filter(r => {
    return r.TaxType === "WHT" && (!startDate || r.Period >= startDate) && (!endDate || r.Period <= endDate);
  });

  let totalDeducted = 0, totalSuffered = 0;
  details.forEach(r => {
    if (r.Direction === "Deducted") totalDeducted += parseFloat(r.TaxAmount) || 0;
    else if (r.Direction === "Suffered") totalSuffered += parseFloat(r.TaxAmount) || 0;
  });

  return {
    totalWHTDeducted: totalDeducted,
    totalWHTSuffered: totalSuffered,
    records: details
  };
}

function getBankBookReport(bankAccountCode, startDate, endDate) {
  return getLedgerReport(bankAccountCode || "1110", startDate, endDate);
}

function getCashBookReport(startDate, endDate) {
  return getLedgerReport("1200", startDate, endDate);
}

function getBudgetVsActualReport(financialYear) {
  const budgets = getSheetDataAsObjects(SHEETS.BUDGET_MASTER);
  const fy = financialYear || "FY-2026";
  const result = [];

  budgets.forEach(b => {
    if (b.FinancialYear === fy || !b.FinancialYear) {
      const annualBudget = parseFloat(b.TotalBudget || b.AnnualBudget) || 0;
      const actual = getActualExpenseForAccount(b.AccountCode, b.CostCenter);
      const varAmt = annualBudget - actual;
      const varPct = annualBudget > 0 ? (varAmt / annualBudget) * 100 : 0;
      result.push({
        AccountCode: b.AccountCode,
        AccountName: b.AccountName,
        CostCenter: b.CostCenter || "ALL",
        BudgetedAmount: annualBudget,
        ActualAmount: actual,
        Variance: varAmt,
        VariancePercent: varPct.toFixed(2),
        Status: actual > annualBudget ? "Over Budget" : "Within Budget"
      });
    }
  });

  return result;
}

function getStockSummaryReport() {
  const items = getSheetDataAsObjects(SHEETS.ITEMS_PRODUCTS);
  return items.map(item => ({
    ItemCode: item.ItemCode,
    ItemName: item.ItemName,
    Category: item.Category,
    Unit: item.Unit,
    PurchaseRate: parseFloat(item.PurchaseRate) || 0,
    SalesRate: parseFloat(item.SalesRate) || 0,
    CurrentStock: parseFloat(item.OpeningStock) || 0,
    StockValue: (parseFloat(item.OpeningStock) || 0) * (parseFloat(item.PurchaseRate) || 0)
  }));
}

function getBankTransactionsForRecon(bankAccountCode) {
  const journals = getSheetDataAsObjects(SHEETS.JOURNAL_ENTRIES);
  const targetCode = bankAccountCode || "1110";
  return journals.filter(j => String(j.AccountCode) === String(targetCode) && j.IsPosted === "Yes");
}

function reconcileBankTransaction(transactionID, statementDate, statementRef) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const reconSheet = ss.getSheetByName(SHEETS.BANK_RECONCILIATION);
  const now = new Date().toISOString();
  const reconId = generateUUID();

  reconSheet.appendRow([
    reconId, "1110", statementDate || now.split("T")[0],
    transactionID, "", "", "Reconciled item", 0, 0, "Yes", now, statementRef || "STMT", now
  ]);

  updateLastSyncTimestamp();
  return { status: "success", reconId: reconId };
}

function getBankReconReport(bankAccountCode, statementDate) {
  const txs = getBankTransactionsForRecon(bankAccountCode);
  let bookBalance = 0;
  let unreconciledCount = 0;
  txs.forEach(t => {
    bookBalance += (parseFloat(t.DebitAmount) || 0) - (parseFloat(t.CreditAmount) || 0);
    unreconciledCount++;
  });
  return {
    bankAccountCode: bankAccountCode || "1110",
    bookBalance: bookBalance,
    statementBalance: bookBalance,
    unreconciledCount: unreconciledCount,
    items: txs
  };
}

function processBulkSync(queue) {
  const results = [];
  queue.forEach(item => {
    try {
      let res;
      switch (item.action) {
        case "saveJournalEntry": res = saveJournalVoucher(item.data); break;
        case "saveSalesInvoice": res = saveSalesInvoice(item.data); break;
        case "savePurchaseBill": res = savePurchaseBill(item.data); break;
        case "saveReceipt": res = saveReceiptVoucher(item.data); break;
        case "savePayment": res = savePaymentVoucher(item.data); break;
        case "saveCustomer": res = saveMasterRecord(SHEETS.CUSTOMERS, "CustomerID", item.data); break;
        case "saveSupplier": res = saveMasterRecord(SHEETS.SUPPLIERS, "SupplierID", item.data); break;
        case "saveItem": res = saveMasterRecord(SHEETS.ITEMS_PRODUCTS, "ItemCode", item.data); break;
        case "saveAccount": res = saveMasterRecord(SHEETS.CHART_OF_ACCOUNTS, "AccountCode", item.data); break;
        case "saveContraEntry": res = saveContraVoucher(item.data); break;
        case "saveDebitNote": res = saveDebitNoteVoucher(item.data); break;
        case "saveCreditNote": res = saveCreditNoteVoucher(item.data); break;
        case "saveDeliveryNote": res = saveMasterRecord(SHEETS.DELIVERY_NOTES, "DeliveryID", item.data); break;
        case "saveGoodsReceiptNote": res = saveMasterRecord(SHEETS.GOODS_RECEIPT_NOTES, "GRNID", item.data); break;
        case "saveStockJournal": res = saveMasterRecord(SHEETS.STOCK_JOURNALS, "StockJournalID", item.data); break;
        case "saveBudget": res = saveMasterRecord(SHEETS.BUDGET_MASTER, "BudgetID", item.data); break;
        default: res = { status: "skipped", message: `Unknown action ${item.action}` };
      }
      results.push({ id: item.id || generateUUID(), status: "success", result: res });
    } catch (err) {
      results.push({ id: item.id || generateUUID(), status: "error", error: err.toString() });
    }
  });

  return {
    processed: results.length,
    results: results,
    lastSyncTimestamp: updateLastSyncTimestamp()
  };
}

function authenticateUser(username, password) {
  const users = getSheetDataAsObjects(SHEETS.USERS);
  for (let u of users) {
    if (u.Username === username && u.PasswordHash === password && u.IsActive === "YES") {
      logAudit(u.UserID, "Login", "USERS", u.UserID, "", "Successful Login");
      return { authenticated: true, user: u };
    }
  }
  return { authenticated: false, message: "Invalid username or password." };
}

function yearEndClose(requestData) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const fySheet = ss.getSheetByName(SHEETS.FINANCIAL_YEAR);
  const now = new Date().toISOString();
  
  const pnl = getProfitAndLossReport(null, null);
  const netProfit = pnl.netProfit;
  
  if (Math.abs(netProfit) > 0) {
    saveJournalVoucher({
      VoucherNumber: getNextVoucherNumber("JOURNAL"),
      VoucherDate: now.split("T")[0],
      Narration: "Year End Closing Entry - Transfer Net Profit to Retained Earnings",
      entries: [
        { AccountCode: "3002", AccountName: "Retained Earnings", DebitAmount: netProfit < 0 ? Math.abs(netProfit) : 0, CreditAmount: netProfit > 0 ? netProfit : 0 }
      ]
    });
  }

  logAudit("ADMIN", "YearEndClose", "FINANCIAL_YEAR", "FY-2026", "IsClosed=NO", "IsClosed=YES");
  return { status: "success", message: "Financial Year Closed successfully. Net Profit transferred to Retained Earnings." };
}

function bulkSeedCOA(accounts) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const coaSheet = ss.getSheetByName(SHEETS.CHART_OF_ACCOUNTS);
  if (!coaSheet || !Array.isArray(accounts) || accounts.length === 0) {
    return { status: "error", message: "Invalid accounts list" };
  }
  coaSheet.clearContents();
  coaSheet.appendRow(SCHEMAS[SHEETS.CHART_OF_ACCOUNTS]);
  const now = new Date().toISOString();
  accounts.forEach(acc => {
    coaSheet.appendRow([
      acc.AccountCode || "",
      acc.AccountName || "",
      acc.AccountGroup || "",
      acc.AccountSubGroup || "",
      acc.AccountType || "Asset",
      acc.ParentAccount || "",
      acc.Level || "1",
      acc.IsSubledger || "No",
      acc.SubledgerType || "None",
      acc.OpeningBalanceDr || 0,
      acc.OpeningBalanceCr || 0,
      acc.IsActive || "Yes",
      acc.BudgetAllocate || 0,
      acc.CreatedDate || now,
      acc.ModifiedDate || now,
      "System"
    ]);
  });
  return { status: "success", count: accounts.length };
}

function bulkSeedBudgets(budgets) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const bdgSheet = ss.getSheetByName(SHEETS.BUDGET_MASTER);
  if (!bdgSheet || !Array.isArray(budgets) || budgets.length === 0) {
    return { status: "error", message: "Invalid budget list" };
  }
  bdgSheet.clearContents();
  bdgSheet.appendRow(SCHEMAS[SHEETS.BUDGET_MASTER]);
  const now = new Date().toISOString();
  const dateStr = now.split("T")[0];
  budgets.forEach(b => {
    const ann = parseFloat(b.AnnualBudget || b.TotalBudget) || 0;
    const mVal = Math.round(ann / 12);
    bdgSheet.appendRow([
      b.BudgetID || ("BDG-" + (b.AccountCode || "0000")),
      b.FinancialYear || "FY-2026",
      b.AccountCode || "",
      b.AccountName || "",
      b.CostCenter || "CC001",
      b.BudgetType || "Annual",
      ann,
      b.Jan !== undefined && b.Jan !== "" ? b.Jan : mVal,
      b.Feb !== undefined && b.Feb !== "" ? b.Feb : mVal,
      b.Mar !== undefined && b.Mar !== "" ? b.Mar : mVal,
      b.Apr !== undefined && b.Apr !== "" ? b.Apr : mVal,
      b.May !== undefined && b.May !== "" ? b.May : mVal,
      b.Jun !== undefined && b.Jun !== "" ? b.Jun : mVal,
      b.Jul !== undefined && b.Jul !== "" ? b.Jul : mVal,
      b.Aug !== undefined && b.Aug !== "" ? b.Aug : mVal,
      b.Sep !== undefined && b.Sep !== "" ? b.Sep : mVal,
      b.Oct !== undefined && b.Oct !== "" ? b.Oct : mVal,
      b.Nov !== undefined && b.Nov !== "" ? b.Nov : mVal,
      b.Dec !== undefined && b.Dec !== "" ? b.Dec : mVal,
      b.TotalBudget || ann,
      b.ApprovedBy || "Admin",
      b.ApprovedDate || dateStr,
      b.IsActive || "Yes",
      b.CreatedDate || now,
      b.ModifiedDate || now
    ]);
  });
  return { status: "success", count: budgets.length };
}
