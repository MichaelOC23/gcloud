
import os
import sys
import timedelta
import time 
from datetime import datetime
from contextlib import asynccontextmanager
from titlecase import titlecase
import asyncio
import asyncpg
import aiohttp
import csv
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import zipfile
import shutil
from io import StringIO

class DatagenETL:
    def __init__(self, db_env="aws"):
        self.DATA = f"{os.path.expanduser("~")}/code/data" # Working directory for data
        self.ARCHIVE = f"{self.DATA}/archive" # Archive directory for prior executions
        self.SOURCE_DATA = f"{self.DATA}/sources" # Source data directory (downloaded and created data from current execution)
        self.NASDAQ_TABLES = ['TICKERS', 'INDICATORS', 'METRICS', 'ACTIONS', 'SP500', 'EVENTS',  'SEP','SF1', 'SFP', 'DAILY'] # 'SF3', 'SF3A', 'SF3B', 
        self.LOGS = 'logs' # Directory for logs
        
        # Security Master Files / Paths
        self.sic_code_file_path = f"{self.SOURCE_DATA}/sic_industry_codes.json"
        self.positions_chase_path = f"{self.SOURCE_DATA}/positions-chase.csv"
        self.securitymaster_nasdaq_path = f"{self.SOURCE_DATA}/NASDAQ_TICKERS.csv"
        self.company_description_path = f"{self.SOURCE_DATA}/ticker_desc_list.json"
        self.company_description_dictionary_path = f"{self.SOURCE_DATA}/ticker_desc_dictionary.json"
        self.sec_ticker_dictionary_path = f"{self.SOURCE_DATA}/sec_tickers.json"
        self.single_stock_price_history_path = f"{self.SOURCE_DATA}/single_stock_price_history.csv"

        self.sql_migrations = {
            "ResetDatabase": """
                DROP SCHEMA IF EXISTS datagen CASCADE;
                CREATE SCHEMA datagen;
                """,
            
            "MigrationSetup": """
                CREATE TABLE datagen."EventLog" (
                "Id" serial4 NOT NULL,
                "EventType" text NOT NULL,
                "EventDescription" text NOT NULL,
                "EventDate" timestamptz NOT NULL,
                "RelatedEntityId" char(36),
                "RelatedEntityType" text,
                CONSTRAINT "PK_EventLog" PRIMARY KEY ("Id")
                );
                """,
            
            # Traditional CRUD by ID or Business Key
            # Business Key: Code | CodeType
            "CreateCodeSet": """
                CREATE TABLE datagen."CodeSet" (
                "Id" serial4 NOT NULL,
                "CodeType" text NOT NULL,
                "Description" text NULL,
                "Code" text NOT NULL,
                "CodeValueString1" text NULL,
                "CodeValueString2" text NULL,
                "CodeValueString3" text NULL,
                "CodeValueFloat1" float4 NULL,
                "CodeValueDate1" timestamptz NULL,
                "CodeValueInt1" int4 NULL,
                "CreatedOn" timestamptz NOT NULL,
                "UpdatedOn" timestamptz NOT NULL,
                "CreatedBy" text NULL,
                "UpdatedBy" text NULL,
                CONSTRAINT "PK_CodeSet" PRIMARY KEY ("Id"),
                CONSTRAINT "UQ_CodeSet_CodeType_Code" UNIQUE ("CodeType", "Code")

                );
                """,
            # Time series by Ticker | AsOfDate
            # Source: NASDAQ DAILY
            "CreatePriceHistory": """
                CREATE TABLE datagen."PriceHistory" (
                "Id" serial4 NOT NULL,
                "Ticker" text NOT NULL,
                "EffectiveDate" DATE NOT NULL,
                "DeprecatedOn" timestamptz NULL,
                "LastUpdated" timestamptz NOT NULL,
                "EnterpriseValueDaily" Decimal NULL,
                "MarketCapitalization" Decimal NULL,
                "PriceToBookValue" Decimal NULL,
                "PriceEarningsRatio" Decimal NULL,
                "PriceSalesRatio" Decimal NULL,
                "CreatedBy" text NOT NULL,
                "CreatedOn" timestamptz NOT NULL,
                "UpdatedBy" text NOT NULL,
                "UpdatedOn" timestamptz NULL,
                CONSTRAINT "PK_PriceHistory" PRIMARY KEY ("Id")
                );
                """,
            
            "CreateSecurityMaster": """
                CREATE TABLE datagen."SecurityMaster" (
                "Id" serial4 NOT NULL,
                "DeprecatedOn" timestamptz NULL,
                "SymTicker" text NULL,
                "SecurityFriendlyName" text NULL,
                "SecurityLegalName" text NOT NULL,
                "SecurityShortName" text NULL,
                "SymCusip" text NULL,
                "SymIsin" text NULL,
                "SymSedol" text NULL,
                "AssetClassLevel1" text NOT NULL,
                "AssetClassLevel2" text NULL,
                "AssetClassLevel3" text NULL,
                "Strategy" text NULL,
                "Objective" text NULL,
                "Sector" text NULL,
                "Industry" text NULL,
                "IndustryGroup" text NULL,
                "IndustryTitle" text NULL,
                "GICSIndustry" text NULL,
                "GICSIndustryGroup" text NULL,
                "GICSSector" text NULL,
                "GICSSubIndustry" text NULL,
                "BrandSymbolURL" text NULL,
                "CompanyDescription" text NULL,
                "CompanyWebsiteURL" text NULL,
                "CountryOfIssuance" text NULL,
                "CountryOfRisk" text NULL,
                "CouponRate" Decimal NULL,
                "CreditRating" text NULL,
                "CurrencyCode" text NOT NULL,
                "CurrentYield" Decimal NULL,
                "DividendPaymentFrequency" text NULL,
                "DividendYield" Decimal NULL,
                "ExchangeCode" text NULL,
                "ExpirationDate" text NULL,
                "ExternalSystemKeySecurityGoldCopy" text NULL,
                "FaceValue" Decimal NULL,
                "FactSheetURL" text NULL,
                "FitchRating" text NULL,
                "InvestmentType" text NULL,
                "IssuerCategory" text NULL,
                "IssuerName" text NULL,
                "MaturityDate" text NULL,
                "MoodysRating" text NULL,
                "NasdaqEarliestFinancialQuarter" text NULL,
                "NasdaqEarliestPriceDate" text NULL,
                "NasdaqLatestFinancialQuarter" text NULL,
                "NasdaqMostRecentPriceDate" text NULL,
                "PriceFactor" Decimal DEFAULT 1,
                "PricingVendorPrimary" text NULL,
                "PricingVendorSecondary" text NULL,
                "PricingVendorTertiary" text NULL,
                "PrimaryExchange" text NULL,
                "RegionOfRisk" text NULL,
                "RelatedTickers" _text NULL,
                "SECFilingURLs" _text NULL,
                "SharesOutstanding" Decimal NULL,
                "YieldToMaturity" Decimal NULL,
                "LogoURL" text NULL,
                "CreatedBy" text NOT NULL,
                "CreatedOn" timestamptz NOT NULL,
                "UpdatedBy" text NOT NULL,
                "UpdatedOn" timestamptz NULL,
                CONSTRAINT "PK_SecurityMaster" PRIMARY KEY ("Id")
            );
                """,
            
            "CreateAccount": """
                CREATE TABLE datagen."Account" (
                "Id" serial4 NOT NULL,
                "AccountNumber" text NULL,
                "ExternalSystemKeyAccounting" text NULL,
                "LegalName" text NULL,
                "ShortName" text NOT NULL,
                "LongName" text NULL,
                "OwnerFriendlyName" text NULL,
                "ManagerFriendlyName" text NULL,
                "BaseCurrency" text NULL,
                "ReportingCurrency" text NULL,
                "PreferredSecurityIdentifier" text NULL,
                "AccountOwnerName" text NULL,
                "AccountOwnerNameJoint" text NULL,
                "AccountTypes" _text NULL,
                "InstitutionName1" text NULL,
                "BusinessUnitLevel1" text NULL,
                "IsClosed" bool NULL,
                "AccountCloseDate" text NULL,
                "CloseReason" text NULL,
                "AdvisorName" text NULL,
                "AdvisoryTeamName" text NULL,
                "ManagerStrategyDescription" text NULL,
                "TaxTreatmentTypes" _text NULL,
                "ModelPortfolioName" text NULL,
                "AssetAllocationName" text NULL,
                "LotReliefMethodDefault" text NULL,
                "IsDiscretionary" bool NULL,
                "OwnerFiscalYearStartDate" text NULL,
                "IsMasterAccount" bool NULL,
                "IsSubAccount" bool NULL,
                "OwnerCountryOfDomicile" text NULL,
                "AnnualManagementFeePercent" Decimal NULL,
                "Description" text NULL,
                "IsMarginApproved" bool NULL,
                "IsOptionsApproved" bool NULL,
                "TargetMarketValue" Decimal NULL,
                "TargetMarketValueDate" text NULL,
                "IsExcludedFromRegulatoryReporting" bool NULL,
                "IsExcludedFromNetWorthReporting" bool NULL,
                "IsHiddenFromOwner" bool NULL,
                "IsHiddenFromAdvisor" bool NULL,
                "IsOwnerDefaultAccount" bool NULL,
                "IsAdvisorDefaultAccount" bool NULL,
                "CreatedOn" timestamptz NOT NULL,
                "UpdatedOn" timestamptz NULL,
                "IsPrivateAsset" bool NULL,
                "CreatedBy" char(36) NOT NULL,
                "UpdatedBy" char(36) NOT NULL,
                "DeletedBy" char(36) NOT NULL,
                CONSTRAINT "PK_Account_Id" PRIMARY KEY ("Id")
                );
                """,
            
            "CreatePosition": """
                CREATE TABLE datagen."Position" (
                "Id" serial4 NOT NULL,
                "EventLogId" char(36) NOT NULL,
                "EffectiveDate" DATE NOT NULL,
                "DeprecatedOn" timestamptz NULL,
                "AccountId" char(36) NOT NULL,
                "SecurityId" char(36) NOT NULL,
                "Sleeve" text NOT NULL,
                "SubAccount" text NULL,
                "AssetClassLevel1" text NOT NULL,
                "AssetClassLevel2" text NULL,
                "AssetClassLevel3" text NULL,
                "Strategy" text NULL,
                "Objective" text NULL,
                "SICOffice" text NULL,
                "SICCode" text NULL,
                "Sector" text NULL,
                "Industry" text NULL,
                "IndustryGroup" text NULL,
                "IndustryTitle" text NULL,
                "SymCusip" text NULL,
                "SymIsin" text NULL,
                "SymTicker" text NULL,
                "SymSedol" text NULL,
                "SecurityShortName" text NULL,
                "SecurityLegalName" text NOT NULL,
                "LocalCurrencyCode" text NULL,
                "CountryOfIssuance" text NULL,
                "CountryOfRisk" text NULL,
                "RegionOfRisk" text NULL,
                "InvestmentType" text NULL,
                "IssuerCategory" text NULL,
                "IssuerName" text NULL,
                "ExchangeCode" text NULL,
                "PrimaryExchange" text NULL,
                "CreditRating" text NULL,
                "ExpirationDate" text NULL,
                "MaturityDate" text NULL,
                "SharesOutstanding" Decimal NULL,
                "BaseCurrencyCode" text NULL,
                "PriceFactor" Decimal DEFAULT 1,
                "UnitsHeld" Decimal NULL,
                "BaseCurrencyDayEndPrice" Decimal NULL,
                "BaseCurrencyPriorDayEndPrice" Decimal NULL,
                "BaseCurrencyDayEndMarketValue" Decimal NULL,
                "BaseCurrencyDayStartingMarketValue" Decimal NULL,
                "BaseCurrencyDayEndUnrealizedGainLoss" Decimal NULL,
                "BaseCurrencyDayStartUnrealizedGainLoss" Decimal NULL,
                "BaseCurrencyDayChangeUnrealizedGainLoss" Decimal NULL,
                "BaseCurrencyMTDChangeUnrealizedGainLoss" Decimal NULL,
                "BaseCurrencyQTDChangeUnrealizedGainLoss" Decimal NULL,
                "BaseCurrencyYTDChangeUnrealizedGainLoss" Decimal NULL,
                "BaseCurrencyDayEndAccruedInterest" Decimal NULL,
                "BaseCurrencyDayStartAccruedInterest" Decimal NULL,
                "BaseCurrencyDayChangeAccruedInterest" Decimal NULL,
                "BaseCurrencyDayEndAccruedDividends" Decimal NULL,
                "BaseCurrencyDayStartAccruedDividends" Decimal NULL,
                "BaseCurrencyDayChangeAccruedDividends" Decimal NULL,
                "BaseCurrencyDayEndAccruedIncome" Decimal NULL,
                "BaseCurrencyDayStartAccruedIncome" Decimal NULL,
                "BaseCurrencyDayChangeAccruedIncome" Decimal NULL,
                "BaseCurrencyDayEndCostBasis" Decimal NULL,
                "BaseCurrencyDayStartCostBasis" Decimal NULL,
                "BaseCurrencyOriginalCost" Decimal NULL,
                "BaseCurrencyOriginalUnitCost" Decimal NULL,
                "BaseCurrencyDayEndYTDRealizedGainLoss" Decimal NULL,
                "BaseCurrencyDayStartYTDRealizedGainLoss" Decimal NULL,
                "BaseCurrencyDayChangeYTDRealizedGainLoss" Decimal NULL,
                "LogoURL" text NULL,
                "CreatedOn" timestamptz NOT NULL,
                "UpdatedOn" timestamptz NULL,
                "CreatedBy" char(36) NOT NULL,
                "UpdatedBy" char(36) NOT NULL,
                CONSTRAINT "PK_Position_Id" PRIMARY KEY ("Id")
                );
                """,
            
            "CreateTransaction": """
                CREATE TABLE datagen."Transaction" (
                    "Id" serial4 NOT NULL,
                    "AccountId" char(36) NOT NULL,
                    "SecurityId" char(36) NOT NULL,
                    "TransactionType" text NOT NULL,
                    "TradeDate" DATE NOT NULL,
                    "DeprecatedOn" timestamptz NULL,
                    "SettlementDate" DATE NULL,
                    "Quantity" Decimal NULL,
                    "Price" Decimal NULL,
                    "GrossAmount" numeric NOT NULL,
                    "NetAmount" numeric NOT NULL,
                    "Fees" Decimal NULL,
                    "Taxes" Decimal NULL,
                    "CurrencyCode" text NOT NULL,
                    "ExchangeRate" Decimal NULL,
                    "CounterpartyIdentifier" text NULL,
                    "Description" text NULL,
                    "RelatedTransactionId" char(36) NOT NULL,
                    "DeprecatedOn" timestamptz NULL,
                    "IsReversed" boolean NOT NULL DEFAULT false,
                    "ReversalTransactionId" char(36) NOT NULL,
                    "CreatedOn" timestamptz NOT NULL,
                    "UpdatedOn" timestamptz NULL,
                    "CreatedBy" char(36) NOT NULL,
                    "UpdatedBy" char(36) NOT NULL,
                    CONSTRAINT "PK_Transaction" PRIMARY KEY ("Id")
                    );
                    
                    -- Create an index on the AccountId for faster querying
                    CREATE INDEX "IX_Transaction_AccountId" ON datagen."Transaction" ("AccountId");
                    
                    -- Create an index on the TransactionType for faster filtering
                    CREATE INDEX "IX_Transaction_TransactionType" ON datagen."Transaction" ("TransactionType");
                    
                    -- Create an index on the TradeDate for faster date-based querying
                    CREATE INDEX "IX_Transaction_TradeDate" ON datagen."Transaction" ("TradeDate");
                    """,    
                    
            "InsertTransactionTypes": """
                INSERT INTO datagen."CodeSet" 
                    ("CodeType", "Description", "Code", "CodeValueString1", "CreatedOn", "UpdatedOn", "CreatedBy", "UpdatedBy")
                    VALUES 
                    ( 'TransactionType', 'Purchase of securities', 'Buy', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Sale of securities', 'Sell', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Addition of cash or securities to the portfolio', 'Contribution', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Removal of cash or securities from the portfolio','Withdrawal', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Cash distribution to shareholders','DividendDeclaration', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Reinvestment of dividends into additional shares','DividendReinvestment', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Increase in the number of shares, reducing the price per share', 'StockSplit', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Decrease in the number of shares, increasing the price per share','ReverseStockSplit', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Distribution of realized capital gains to shareholders', 'CapitalGainDistribution', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Interest earned on cash or fixed-income securities', 'InterestIncome', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Payment of interest on a margin loan or other liabilities','InterestPayment', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Interest charged on borrowed funds for margin accounts', 'MarginInterest', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Distribution that reduces the cost basis of the investment', 'ReturnOfCapital', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Payment of dividends from the portfolio''s securities','DividendPayment', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Payment of fees, such as management or advisory fees','FeePayment', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Payment of taxes from the portfolio', 'TaxPayment', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Any corporate action not specifically defined','OtherCorporateAction', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Combination of two companies, affecting shareholdings','Merger', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Purchase of one company by another', 'Acquisition', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Distribution of shares in a subsidiary to existing shareholders', 'SpinOff', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Offering of additional shares to existing shareholders', 'RightsIssue', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Offer to purchase shares from shareholders at a specified price', 'TenderOffer', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Distribution of additional shares instead of cash dividends', 'StockDividend', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Repurchase of shares by the issuing company', 'StockBuyback', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Sale of borrowed securities with intention to repurchase later at a lower price', 'ShortSale', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Purchase of securities to close out a short position','ShortCover', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Transfer of securities into the portfolio','TransferIn', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Transfer of securities out of the portfolio', 'TransferOut', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Sale of securities to close out the portfolio','Liquidation', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Deposit of cash into the portfolio', 'CashDeposit', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Withdrawal of cash from the portfolio','CashWithdrawal', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Adjustment to the cost basis of specific tax lots','TaxLotAdjustment', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Sale and repurchase triggering wash sale rules', 'WashSale', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Corporate restructuring that affects the securities', 'Reorganization', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Conversion of one type of security into another', 'SecurityConversion', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Fee charged by the custodian for holding securities', 'CustodianFee', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Sale of fractional shares','FractionalShareSale', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'TransactionType', 'Sale of securities due to a margin call or other requirement','ForcedSale', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System');
                    """,

            "InsertOrderTypes": """
                INSERT INTO datagen."CodeSet" 
                    ("CodeType", "Description", "Code", "CodeValueString1", "CreatedOn", "UpdatedOn", "CreatedBy", "UpdatedBy")
                    VALUES 
                    ( 'OrderType', 'Purchase of securities', 'BuyOrder', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'OrderType', 'Sale of securities', 'SellOrder', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'OrderType', 'Purchase of securities to cover a Short Sale', 'ShortCoverOrder', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'OrderType', 'Sale of borrowed securities', 'ShortSaleOrder', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'OrderType', 'Addition of cash or securities to the portfolio', 'Contribution', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ( 'OrderType', 'Removal of cash or securities from the portfolio', 'Withdrawal', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System');
                    """,

            "InsertOrderStatuses": """
                INSERT INTO datagen."CodeSet" 
                    ("CodeType", "Description", "Code", "CodeValueString1", "CreatedOn", "UpdatedOn", "CreatedBy", "UpdatedBy")
                    VALUES 
                    ('OrderStatus', 'Order has been received but not yet processed', 'Pending', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ('OrderStatus', 'Order has been successfully executed', 'Executed', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ('OrderStatus', 'Order has been cancelled', 'Cancelled', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ('OrderStatus', 'Order is partially executed', 'PartiallyExecuted', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System'),
                    ('OrderStatus', 'Order execution has failed', 'Failed', NULL, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'System', 'System');
                    """,

            "CreateOrder": """
                CREATE TABLE datagen."Order" (
                    "Id" serial4 NOT NULL,
                    "AccountId" char(36) NOT NULL,
                    "SecurityId" text NULL,
                    "OrderType" text NOT NULL,
                    "OrderStatus" text NOT NULL,
                    "OrderDate" timestamptz NOT NULL,
                    "SettlementDate" timestamptz NULL,
                    "Quantity" Decimal NULL,
                    "Price" Decimal NULL,
                    "TotalAmount" numeric NOT NULL,
                    "CurrencyCode" text NOT NULL,
                    "ExchangeRate" Decimal NULL,
                    "Description" text NULL,
                    "CreatedOn" timestamptz NOT NULL,
                    "UpdatedOn" timestamptz NULL,
                    "CreatedBy" char(36) NOT NULL,
                    "UpdatedBy" char(36) NOT NULL,
                    "DeletedBy" char(36) NOT NULL,
                    CONSTRAINT "PK_Order" PRIMARY KEY ("Id")
                    -- CONSTRAINT "FK_Order_Account" FOREIGN KEY ("AccountId") REFERENCES datagen."Account" ("Id"),
                    -- CONSTRAINT "FK_Order_SecurityMaster" FOREIGN KEY ("SecurityId") REFERENCES datagen."SecurityMaster" ("Id")
                    );

                    -- Create an index on the AccountId for faster querying
                    CREATE INDEX "IX_Order_AccountId" ON datagen."Order" ("AccountId");

                    -- Create an index on the OrderType for faster filtering
                    CREATE INDEX "IX_Order_OrderType" ON datagen."Order" ("OrderType");

                    -- Create an index on the OrderDate for faster date-based querying
                    CREATE INDEX "IX_Order_OrderDate" ON datagen."Order" ("OrderDate");

                    -- Create an index on the OrderStatus for faster status-based querying
                    CREATE INDEX "IX_Order_OrderStatus" ON datagen."Order" ("OrderStatus");
                    """,

            #Note: LotId is the instatiating transaction's id
            "CreateTaxLot": """
                CREATE TABLE datagen."TaxLot" (
                    "Id" serial4 NOT NULL,
                    "LotId" char(36) NOT NULL, 
                    "ParentLotId" char(36) NULL,
                    "EventLogId" char(36) NOT NULL,
                    "TransactionId" char(36) NOT NULL,
                    "AccountId" char(36) NOT NULL,
                    "SecurityId" text NOT NULL,
                    "EffectiveDate" DATE NOT NULL,
                    "DeprecatedOn" timestamptz NULL,
                    "LotReliefMethod" text NOT NULL,
                    "UnitsHeld" Decimal NOT NULL,
                    "OriginalUnitsHeld" Decimal NOT NULL,
                    "CostBasis" Decimal NOT NULL,
                    "OriginalCostBasis" Decimal NOT NULL,
                    "OriginalUnitCost" Decimal NOT NULL,
                    "AccruedInterestEffect" Decimal NULL,
                    "AccruedDividendsEffect" Decimal NULL,
                    "AccruedIncomeEffect" Decimal NULL,
                    "AccruedExpenseEffect" Decimal NULL,
                    "AccruedFeeEffect" Decimal NULL,
                    "AccrualLedgerCode" text NULL,
                    "AccrualDebit" Decimal NULL,
                    "AccrualCredit" Decimal NULL,
                    "LastRecalculatedOn" timestamptz NOT NULL,
                    "CreatedOn" timestamptz NOT NULL,
                    CONSTRAINT "PK_TaxLot" PRIMARY KEY ("Id")
                    -- CONSTRAINT "FK_TaxLot_Account" FOREIGN KEY ("AccountId") REFERENCES datagen."Account" ("Id"),
                    -- CONSTRAINT "FK_TaxLot_SecurityMaster" FOREIGN KEY ("SecurityId") REFERENCES datagen."SecurityMaster" ("Id"),
                    -- CONSTRAINT "FK_TaxLot_Transaction" FOREIGN KEY ("TransactionId") REFERENCES datagen."Transaction" ("Id"),
                    -- CONSTRAINT "FK_TaxLot_ParentLot" FOREIGN KEY ("ParentLotId") REFERENCES datagen."TaxLot" ("Id"),
                    -- CONSTRAINT "FK_TaxLot_EventLog" FOREIGN KEY ("EventLogId") REFERENCES datagen."EventLog" ("Id")
                );

                -- Create indexes for faster querying
                CREATE INDEX "IX_TaxLot_AccountId" ON datagen."TaxLot" ("AccountId");
                CREATE INDEX "IX_TaxLot_SecurityId" ON datagen."TaxLot" ("SecurityId");
                CREATE INDEX "IX_TaxLot_TransactionId" ON datagen."TaxLot" ("TransactionId");
                CREATE INDEX "IX_TaxLot_BusinessDate" ON datagen."TaxLot" ("BusinessDate");
                CREATE INDEX "IX_TaxLot_DeprecatedOn" ON datagen."TaxLot" ("DeprecatedOn");
                """,
            
            "CreateEvents":"""
                CREATE TABLE datagen."Event" (
                    "Id" SERIAL PRIMARY KEY,
                    "SymTicker" text NOT NULL,
                    "EventDate" DATE NOT NULL,
                    "EventCodes" TEXT[] NOT NULL,
                    "CreatedBy" TEXT NOT NULL,
                    "CreatedOn" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    "UpdatedBy" TEXT,
                    "UpdatedOn" TIMESTAMPTZ
                    );

                    -- Create an index on SymTicker and EventDate for faster querying
                    CREATE INDEX "IX_EventLog_SymTicker_EventDate" ON datagen."EventLog" ("SymTicker", "EventDate");
                    """,
            
            }
        self.environment_dict = {
            "local": 'postgresql://postgres:test@localhost:5432/platform',
            "aws": "postgresql://postgres:lnRipjfDXV07KjgiWXyvv@michael.ch6qakwu269h.us-east-1.rds.amazonaws.com:5432/postgres"
            }
        self.connection_string = self.environment_dict.get(db_env) if self.environment_dict.get(db_env) else "NO CONNECITON STRING"
    
    @asynccontextmanager
    async def async_get_connection(self):
        conn = await asyncpg.connect(self.connection_string)
        try:
            yield conn
        finally:
            await conn.close()

    #! Database Initialization
    async def initialize_db(self):
        async with self.async_get_connection() as conn:
            for migration_name, sql in self.sql_migrations.items():
                try:
                    # Check if migration has already been executed
                    migration_executed = await self.check_migration_executed(conn, migration_name)
                    
                    if migration_executed:
                        print(f"Migration {migration_name} already executed, skipping.")
                        continue

                    # Execute the migration
                    await conn.execute(sql)
                    print(f"Executed migration: {migration_name}")

                    # Log the execution in event_log
                    await self.log_migration(conn, migration_name)

                except Exception as e:
                    if not migration_name.startswith("ResetDatabase"):
                        print(f"Error executing migration {migration_name}: {e}")
                        exit(1)
    async def check_migration_executed(self, conn, migration_name):
        try:
            result = await conn.fetchval(f"""
                SELECT COUNT(*) FROM datagen."EventLog"
                WHERE "EventType" = '{migration_name}'""")
            return result > 0
        except asyncpg.UndefinedTableError:
            # If the EventLog table doesn't exist, no migrations have been run
            return False
    async def log_migration(self, conn, migration_name):
        await conn.execute(f"""
            INSERT INTO datagen."EventLog" 
            ("EventType", "EventDescription", "EventDate")
            VALUES ('{migration_name}', $1, CURRENT_TIMESTAMP)
        """, f"Migration {migration_name} executed")

    #! Acquire Data
    async def pre_process_csv(self, folder, filename):
        def inspect_and_cast( df, max_rows=50):
            def is_date_or_empty(val):
                if pd.isnull(val):
                    return True
                val_str = str(val).strip()
                if val_str == '':
                    return True
                try:
                    pd.to_datetime(val_str)
                    return True
                except (ValueError, TypeError):
                    return False
            def is_numeric_or_empty(s):
                try:
                    s_float = pd.to_numeric(s, errors='coerce')
                    return s_float.notna() | s.isna()
                except ValueError:
                    return False
            def optimize_dataframe(df, max_rows):
                for col in df.columns:
                    sample = df[col].iloc[:max_rows]
                    if is_numeric_or_empty(sample).all():
                        df[col] = df[col].replace(r'^\s*$', '0', regex=True)
                        df[col] = df[col].fillna('0')
                        try:
                            df[col] = df[col].astype(float)
                        except ValueError:
                            continue
                return df
            df = optimize_dataframe(df, max_rows)
            for col in df.columns:
                if df[col].apply(is_date_or_empty).all():
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            df = df.fillna('')  
            return df
        
        csv_path = os.path.join(folder, filename)
        dtype_path = csv_path.replace('.csv', '_dtype.json')
        pickle_path = csv_path.replace('.csv', '.pkl')

        # If a pickle file exists, load from it
        if os.path.exists(pickle_path):
            df = pd.read_pickle(pickle_path)
            print(f"\033[1;96mLoaded {filename} from pickle.\033[0m")
            return df

        # Otherwise, load the CSV
        start_time = time.time()
        if os.path.exists(dtype_path):
            with open(dtype_path, 'r') as dtype_file:
                dtype_dict = json.load(dtype_file)
            df = pd.read_csv(csv_path, dtype=dtype_dict)
            print(f"\033[1;96mLoaded {filename} with specified dtypes from CSV.\033[0m")
        else:
            # CSV Will be processed as new
            with open(f'gmtc/{filename}') as f:
                
                # Read , lower case and remove spaces from header
                header = f.readline().strip().split(',')
                clean_header = [col.strip().replace(' ', '_').lower() for col in header]

                # Load the rest of the file into a DataFrame using the cleaned header
                df = pd.read_csv(f, names=clean_header, dtype=str)
                
            # Drop rows where all elements are NaN
            df = df.dropna(how='all')
            
            # Remove \n from all fields in the DataFrame
            df = df.apply(lambda col: col.apply(lambda x: x.replace('\n', ' ').replace('\r', ' ') if isinstance(x, str) else x))
            
            # Reset the index after dropping rows
            df = df.reset_index(drop=True)
            
            # Cast the DataFrame Columns as their appropriate types
            df = inspect_and_cast(df, 50)
            
            # Save dtypes
            dtype_dict = df.dtypes.apply(lambda x: x.name).to_dict()
            with open(dtype_path, 'w') as dtype_file:
                json.dump(dtype_dict, dtype_file)
            print(f"\033[1;96mSaved dtypes for {filename}.\033[0m")

        # Save the processed DataFrame as a pickle
        df.to_pickle(pickle_path)
        print(f"\033[1;96mSaved {filename} as pickle.\033[0m")
        print(f"\033[1;96mTime to process {filename}: {time.time() - start_time}\033[0m")
        return df
    async def archive_source_file(self, file_path):
            if os.path.exists(file_path):
                unique_date_key = datetime.now().strftime("%Y%m%d_%H%M%S")
                # get the file type-extension including the. from the end of the path
                file_extension = os.path.splitext(file_path)[1]
                archive_file_path = file_path.replace(f"sources/", f"archive")
                archive_file_path = f"{archive_file_path.replace(file_extension, "")}_{unique_date_key}{file_extension}"
                shutil.copy(file_path, f"{self.ARCHIVE}/{os.path.basename(file_path)}")
                os.remove(file_path)
    async def fetch_sec_url_once(self, url):
            headers = {
                'User-Agent': 'JustBuildIt admin@justbuildit.com',
                'Accept-Encoding': 'gzip, deflate',
                'Host': 'www.sec.gov'
                }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response
            else:
                raise Exception(f"Failed to fetch URL with status code {response.status_code}")
    async def get_all_nasdaq_files(self):      
        async def create_download_request(table):
            url = f"https://data.nasdaq.com/api/v3/datatables/SHARADAR/{table}.csv?qopts.export=true&api_key=6X82a45M1zJPu2ci4TJP"
            response = requests.get(url)
            status_dict = {}
            status_dict["name"] = table
            status_dict["status"] = response.status_code
            status_dict["link"] = url
            status_dict["downloaded"] = 0
            if response.status_code == 200:
                reader = csv.DictReader(StringIO(response.text))
                for row in reader:
                    for column_name in reader.fieldnames:
                        status_dict[column_name] = row[column_name]
                return status_dict
            else:
                status_dict["status"] = "Failed"
                status_dict["error"] = response.text
                print(Exception(f"ERROR ... Failed to get a download link for table {table}: {response.text}"))
                return None
        async def request_and_download_all_files():                 
            async def dowload_list_of_files_async(download_status):
                async def download_file(session, url, destination):
                    start_time = time.time()
                    print(f"Starting download of {destination} at {start_time}")
                    async with session.get(url) as response:
                        # Ensure the response is successful
                        response.raise_for_status()
                            
                        # Write the content to a destination file
                        with open(destination, 'wb') as f:
                            while True:
                                chunk = await response.content.read(1024)  # Read chunks of 1KB
                                if not chunk: break
                                f.write(chunk)
                        # if the file is a zip file, extract it
                        if destination.endswith('.zip'):
                            with zipfile.ZipFile(destination, 'r') as zip_ref:
                                filenames = zip_ref.extractall(self.SOURCE_DATA)
                            os.remove(destination)
                        print(f"Completed download of {destination} in {time.time() - start_time} seconds")
                waiting_on = []
                download_next_list = []
                # Create a session and download files concurrently
                async with aiohttp.ClientSession() as session:
                    for file in download_status:
                        if 'downloaded' not in file or 'file.status' not in file:
                            continue
                        if file["downloaded"] == 0 and file['file.status'] == "fresh":
                            download_next_list.append(download_file(session, file["file.link"], f"{self.SOURCE_DATA}/{file['name']}.zip"))
                            file["downloaded"] == 1
                        elif file["downloaded"] == 1:
                            continue
                        else:
                            waiting_on.append(file)
                    await asyncio.gather(*download_next_list)
                    return download_status, waiting_on
            print("Getting status of NASDAQ files")
            download_list = []      
            for table in self.NASDAQ_TABLES: 
                item = await create_download_request(table)
                if item is not None:
                    download_list.append(item)
            print("Beginning download of files that are ready")
            download_list, waiting_on = await dowload_list_of_files_async(download_list)
            while len(waiting_on) > 0:
                download_list, waiting_on = asyncio.run(dowload_list_of_files_async(download_list))
                print(f"Still waiting on: waiting_on {waiting_on}")
                time.sleep(5)
        def rename_files():
            for csvfile in os.listdir(self.SOURCE_DATA):
                if csvfile.endswith('.csv'):
                    if "SHARADAR" in csvfile:
                        for filecode in self.NASDAQ_TABLES:
                            if filecode in csvfile:
                                current_name = os.path.join(self.SOURCE_DATA, csvfile)
                                new_name = os.path.join(self.SOURCE_DATA, f"NASDAQ_{filecode.upper()}.csv")
                                os.rename(current_name, new_name)
                                time.sleep(1)
        await request_and_download_all_files()   
        rename_files()
    async def get_sec_listed_tickers(self):  
        def custom_title_case_securityname(text):
            # Define a dictionary of exceptions for specific terms
            exceptions = {
                " INC":      "Inc.",
                " LLC":      "LLC",
                " LLP":      "LLP",
                " PLC":      "PLC",
                " CORP":     "Corp",
                " CO.":       "Co.",
                " LTD":      "Ltd",
                "N.V.":     "N.V.",
                "S.A.":     "S.A.",
                "AG":       "AG",
                "S.P.A.":   "S.p.A."
            }
            # Convert the title to title case using the titlecase library
            title_cased = titlecase(text)

            # Replace exceptions with correct capitalization
            for term, replacement in exceptions.items():
                title_cased = title_cased.replace(term.title(), replacement)
            
            return title_cased
        
        
        def process_titles(data):
            for key, value in data.items():
                title = value.get('title', '')
                if title.isupper() or title.islower():  # Also handle titles that are all lowercase
                    value['title'] = custom_title_case_securityname(title)
            return data
        await self.archive_source_file(self.sec_ticker_dictionary_path)
        url = "https://www.sec.gov/files/company_tickers.json"
        response = await self.fetch_sec_url_once(url)
        data_dict = response.json()
        # Process the titles in the data dictionary
        data = process_titles(data_dict)
        # Save the new file to the data folder
        with open(self.sec_ticker_dictionary_path, "w") as f:
            json.dump(data, f, indent=4)
        return data
    async def get_current_sic_table(self):
        def clean_sic_dict(sic_dict):
            for key in sic_dict.keys():
                sic_dict[key]['Office'] = sic_dict[key]['Office'].replace('Office of', '').strip()
                sic_dict[key]['Office'] = sic_dict[key]['Office'].replace('and Services', '').strip()
                sic_dict[key]['Office'] = sic_dict[key]['Office'].replace('and Services', '').title()
                
                sic_dict[key]['Industry Title'] = sic_dict[key]['Industry Title'].replace('SERVICES-', '').strip()
                sic_dict[key]['Industry Title'] = sic_dict[key]['Industry Title'].replace('RETAIL-', '').strip()
                sic_dict[key]['Industry Title'] = sic_dict[key]['Industry Title'].replace('WHOLESALE-', '').strip()
                sic_dict[key]['Industry Title'] = sic_dict[key]['Industry Title'].replace('WHOLESALE-', '').title()
            
            return sic_dict
        
        # Define the URL
        url = 'https://www.sec.gov/corpfin/division-of-corporation-finance-standard-industrial-classification-sic-code-list'
        
        response = await self.fetch_sec_url_once(url)

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the table
        table = soup.find('table', class_='list')
        
        # Extract table headers
        headers = [th.text.strip() for th in table.find('thead').find_all('th')]
        
        # Extract table rows
        rows = []
        for tr in table.find('tbody').find_all('tr'):
            cells = [td.text.strip() for td in tr.find_all('td')]
            rows.append(cells)
        
        # Convert to DataFrame
        df = pd.DataFrame(rows, columns=headers)
        
        # Convert DataFrame to dictionary with formatted keys
        sic_dict = {
            f"{int(row['SIC Code']):04d}": {
                "Office": row["Office"],
                "Industry Title": row["Industry Title"]
            }
            for _, row in df.iterrows()
        }
        # Trim the Office and Industry values to remove unnecessary repetition
        sic_dict_4digit = clean_sic_dict(sic_dict)
        
        # Create a dictionary with 2-digit SIC codes to get approximate industry categories when
        # the 4-digit SIC code is not in the dictionary
        sic_dict_2digit = {}
        for key in sic_dict_4digit.keys():
            d2key = f"{key[:2]}"
            sic_dict_2digit[d2key] = sic_dict_4digit.get(key, {})
        
        sic_dict = { "TWO_DIGIT": sic_dict_2digit, "FOUR_DIGIT": sic_dict_4digit}
        
        await self.archive_source_file(self.sic_code_file_path)
        # Save the new file to the data folder
        with open(self.sic_code_file_path, "w") as f:
            json.dump(sic_dict, f, indent = 4)

        
        return sic_dict
    async def get_company_descriptions(self):
        with open(self.company_description_path, "r") as f:
            desc_list_dict = json.loads(f.read())
            desc_dict = {}
            for sec_data in desc_list_dict.get('data', []):
                desc_dict[sec_data.get('ticker', "")] = sec_data.get('description', "")
            with open(self.company_description_dictionary_path, "w") as f:
                f.write(json.dumps(desc_dict, indent=4))
        return desc_dict
    async def acquire_all_data(self):
        extraction_tasks = []
        extraction_tasks.append(self.get_all_nasdaq_files())
        extraction_tasks.append(self.get_sec_listed_tickers())
        extraction_tasks.append(self.get_current_sic_table())
        extraction_tasks.append(self.get_company_descriptions())
        await asyncio.gather(*extraction_tasks)


    #! Transform and Load Data
    async def load_security_master(self):
        # Open the TICKER.csv file (Nasdaq) and iterate through the rows. 
        # Securities that are old and no longer priced do not need to be included in the SecurityMaster for current positions.
        nasdaq_ticker_dict = {}
        with open(self.securitymaster_nasdaq_path, 'r') as f:
            date_14_days_ago = datetime.now() - timedelta(days=14) 
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('table', "") != "SF1":
                    continue
                
                last_price_date_str = row.get('lastpricedate', "")
                if last_price_date_str != "":
                    last_price_date = datetime.strptime(last_price_date_str, "%Y-%m-%d")
                    # if the timedelta is greater than 14 days ago, skip the row
                    if last_price_date < date_14_days_ago:
                        continue
                if row.get('ticker', "") == "":
                    continue
                if row.get('category', "") == "": #AssetClassLevel1
                    row['category'] = "Domestic Common Stock"
                if row.get('currency', "") == "": #CurrencyCode
                    continue
                ticker = row.get('ticker', "")
                nasdaq_ticker_dict[ticker] = row
        return nasdaq_ticker_dict





if __name__ == "__main__":
    etl = DatagenETL()
    # asyncio.run(etl.initialize_db())
    # asyncio.run(etl.acquire_all_data())
    print("Database initialization complete")