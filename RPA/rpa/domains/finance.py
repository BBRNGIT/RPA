"""
Finance Domain Learning Module for RPA.

This module provides comprehensive finance and economics knowledge:
- Financial terminology and concepts
- Accounting fundamentals
- Investment principles
- Economic indicators and analysis
- Time-value of money calculations
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import json
import math
import random
import uuid
import logging

from rpa.memory.ltm import LongTermMemory
from rpa.memory.episodic import EpisodicMemory, EventType
from rpa.core.graph import Node, NodeType

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND DATA STRUCTURES
# ============================================================================

class FinancialCategory(Enum):
    """Categories of financial knowledge."""
    TERMINOLOGY = "terminology"
    ACCOUNTING = "accounting"
    INVESTING = "investing"
    ECONOMICS = "economics"
    BANKING = "banking"
    TAXATION = "taxation"


class AssetClass(Enum):
    """Major asset classes."""
    EQUITY = "equity"
    FIXED_INCOME = "fixed_income"
    CASH = "cash"
    REAL_ESTATE = "real_estate"
    COMMODITIES = "commodities"
    CRYPTO = "crypto"


class FinancialRatioType(Enum):
    """Types of financial ratios."""
    PROFITABILITY = "profitability"
    LIQUIDITY = "liquidity"
    LEVERAGE = "leverage"
    EFFICIENCY = "efficiency"
    VALUATION = "valuation"


class EconomicIndicatorType(Enum):
    """Types of economic indicators."""
    LEADING = "leading"
    COINCIDENT = "coincident"
    LAGGING = "lagging"


class FinanceProficiency(Enum):
    """Proficiency levels for finance knowledge."""
    NOVICE = "novice"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


# ============================================================================
# FINANCIAL TERM
# ============================================================================

@dataclass
class FinancialTerm:
    """A financial term or concept."""
    term_id: str
    term: str
    definition: str
    category: FinancialCategory
    
    examples: List[str] = field(default_factory=list)
    related_terms: List[str] = field(default_factory=list)
    formulas: List[str] = field(default_factory=list)
    
    difficulty: int = 1
    proficiency: FinanceProficiency = FinanceProficiency.NOVICE
    total_reviews: int = 0
    correct_reviews: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "term_id": self.term_id,
            "term": self.term,
            "definition": self.definition,
            "category": self.category.value,
            "examples": self.examples,
            "related_terms": self.related_terms,
            "formulas": self.formulas,
            "difficulty": self.difficulty,
            "proficiency": self.proficiency.value,
            "total_reviews": self.total_reviews,
            "correct_reviews": self.correct_reviews,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FinancialTerm":
        return cls(
            term_id=data["term_id"],
            term=data["term"],
            definition=data["definition"],
            category=FinancialCategory(data["category"]),
            examples=data.get("examples", []),
            related_terms=data.get("related_terms", []),
            formulas=data.get("formulas", []),
            difficulty=data.get("difficulty", 1),
            proficiency=FinanceProficiency(data.get("proficiency", "novice")),
            total_reviews=data.get("total_reviews", 0),
            correct_reviews=data.get("correct_reviews", 0),
        )


# ============================================================================
# FINANCIAL RATIO
# ============================================================================

@dataclass
class FinancialRatio:
    """A financial ratio with calculation and interpretation."""
    ratio_id: str
    name: str
    ratio_type: FinancialRatioType
    formula: str
    description: str
    interpretation: str
    good_range: str = ""
    warning_signs: List[str] = field(default_factory=list)
    example_calculation: str = ""
    
    difficulty: int = 2
    proficiency: FinanceProficiency = FinanceProficiency.NOVICE
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ratio_id": self.ratio_id,
            "name": self.name,
            "ratio_type": self.ratio_type.value,
            "formula": self.formula,
            "description": self.description,
            "interpretation": self.interpretation,
            "good_range": self.good_range,
            "warning_signs": self.warning_signs,
            "example_calculation": self.example_calculation,
            "difficulty": self.difficulty,
            "proficiency": self.proficiency.value,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FinancialRatio":
        return cls(
            ratio_id=data["ratio_id"],
            name=data["name"],
            ratio_type=FinancialRatioType(data["ratio_type"]),
            formula=data["formula"],
            description=data["description"],
            interpretation=data["interpretation"],
            good_range=data.get("good_range", ""),
            warning_signs=data.get("warning_signs", []),
            example_calculation=data.get("example_calculation", ""),
            difficulty=data.get("difficulty", 2),
            proficiency=FinanceProficiency(data.get("proficiency", "novice")),
        )


# ============================================================================
# INVESTMENT CONCEPT
# ============================================================================

@dataclass
class InvestmentConcept:
    """An investment concept or strategy."""
    concept_id: str
    name: str
    asset_class: Optional[AssetClass] = None
    description: str = ""
    key_principles: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)
    
    difficulty: int = 1
    proficiency: FinanceProficiency = FinanceProficiency.NOVICE
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "concept_id": self.concept_id,
            "name": self.name,
            "asset_class": self.asset_class.value if self.asset_class else None,
            "description": self.description,
            "key_principles": self.key_principles,
            "risks": self.risks,
            "benefits": self.benefits,
            "difficulty": self.difficulty,
            "proficiency": self.proficiency.value,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InvestmentConcept":
        return cls(
            concept_id=data["concept_id"],
            name=data["name"],
            asset_class=AssetClass(data["asset_class"]) if data.get("asset_class") else None,
            description=data.get("description", ""),
            key_principles=data.get("key_principles", []),
            risks=data.get("risks", []),
            benefits=data.get("benefits", []),
            difficulty=data.get("difficulty", 1),
            proficiency=FinanceProficiency(data.get("proficiency", "novice")),
        )


# ============================================================================
# ECONOMIC INDICATOR
# ============================================================================

@dataclass
class EconomicIndicator:
    """An economic indicator with interpretation."""
    indicator_id: str
    name: str
    indicator_type: EconomicIndicatorType
    description: str = ""
    measurement: str = ""  # How it's measured
    frequency: str = ""  # Monthly, quarterly, etc.
    importance: str = ""  # High, medium, low
    interpretation: str = ""
    impact_on_markets: List[str] = field(default_factory=list)
    
    difficulty: int = 2
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "indicator_id": self.indicator_id,
            "name": self.name,
            "indicator_type": self.indicator_type.value,
            "description": self.description,
            "measurement": self.measurement,
            "frequency": self.frequency,
            "importance": self.importance,
            "interpretation": self.interpretation,
            "impact_on_markets": self.impact_on_markets,
            "difficulty": self.difficulty,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EconomicIndicator":
        return cls(
            indicator_id=data["indicator_id"],
            name=data["name"],
            indicator_type=EconomicIndicatorType(data["indicator_type"]),
            description=data.get("description", ""),
            measurement=data.get("measurement", ""),
            frequency=data.get("frequency", ""),
            importance=data.get("importance", ""),
            interpretation=data.get("interpretation", ""),
            impact_on_markets=data.get("impact_on_markets", []),
            difficulty=data.get("difficulty", 2),
        )


# ============================================================================
# FINANCE DOMAIN CLASS
# ============================================================================

class FinanceDomain:
    """
    Finance and economics knowledge domain for RPA.
    
    Features:
    - Financial terminology and concepts
    - Accounting fundamentals and ratios
    - Investment principles and strategies
    - Economic indicators analysis
    - Time-value of money calculations
    """
    
    def __init__(
        self,
        ltm: Optional[LongTermMemory] = None,
        episodic: Optional[EpisodicMemory] = None,
    ):
        """Initialize finance domain."""
        self.ltm = ltm or LongTermMemory()
        self.episodic = episodic or EpisodicMemory()
        
        # Knowledge stores
        self._terms: Dict[str, FinancialTerm] = {}
        self._ratios: Dict[str, FinancialRatio] = {}
        self._concepts: Dict[str, InvestmentConcept] = {}
        self._indicators: Dict[str, EconomicIndicator] = {}
        
        # Review history
        self._review_history: List[Dict[str, Any]] = []
        
        # Initialize with foundational knowledge
        self._initialize_terms()
        self._initialize_ratios()
        self._initialize_concepts()
        self._initialize_indicators()
    
    def _initialize_terms(self) -> None:
        """Initialize with essential financial terms."""
        # Basic terminology
        terms = [
            # Basic concepts
            ("Asset", "A resource with economic value owned by an individual or corporation",
             FinancialCategory.TERMINOLOGY, ["Cash", "Inventory", "Equipment", "Real estate"], 1),
            ("Liability", "A financial obligation or debt owed to another party",
             FinancialCategory.TERMINOLOGY, ["Accounts payable", "Loans", "Mortgages"], 1),
            ("Equity", "The residual interest in assets after deducting liabilities; ownership value",
             FinancialCategory.TERMINOLOGY, ["Stockholders' equity", "Home equity"], 1),
            ("Revenue", "Income generated from normal business operations",
             FinancialCategory.TERMINOLOGY, ["Sales revenue", "Service revenue"], 1),
            ("Expense", "Costs incurred in generating revenue",
             FinancialCategory.TERMINOLOGY, ["Rent", "Salaries", "Utilities"], 1),
            ("Net Income", "Total revenue minus total expenses; profit",
             FinancialCategory.ACCOUNTING, ["Also called net profit or earnings"], 1),
            
            # Investment terms
            ("Dividend", "Distribution of a company's earnings to shareholders",
             FinancialCategory.INVESTING, ["Quarterly dividends", "Dividend yield"], 1),
            ("Capital Gain", "Profit from selling an asset above its purchase price",
             FinancialCategory.INVESTING, ["Realized vs unrealized gains"], 1),
            ("Portfolio", "Collection of financial investments owned by an individual or institution",
             FinancialCategory.INVESTING, ["Diversified portfolio"], 1),
            ("Diversification", "Risk management strategy of mixing investments within a portfolio",
             FinancialCategory.INVESTING, ["Asset allocation", "Risk reduction"], 2),
            ("Compound Interest", "Interest calculated on both initial principal and accumulated interest",
             FinancialCategory.BANKING, ["Compound annual growth rate (CAGR)"], 1),
            
            # Banking terms
            ("Principal", "The original amount of money invested or borrowed",
             FinancialCategory.BANKING, ["Loan principal", "Investment principal"], 1),
            ("Interest Rate", "Percentage charged for borrowing or earned from investing money",
             FinancialCategory.BANKING, ["Annual percentage rate (APR)"], 1),
            ("Liquidity", "Ease with which an asset can be converted to cash",
             FinancialCategory.BANKING, ["Liquid assets", "Market liquidity"], 1),
            
            # Economics terms
            ("Inflation", "Rate at which the general level of prices for goods and services rises",
             FinancialCategory.ECONOMICS, ["Consumer Price Index (CPI)", "Purchasing power"], 1),
            ("Deflation", "Decrease in the general price level of goods and services",
             FinancialCategory.ECONOMICS, ["Opposite of inflation"], 2),
            ("GDP", "Gross Domestic Product - total value of goods and services produced in a country",
             FinancialCategory.ECONOMICS, ["Real GDP vs Nominal GDP"], 1),
            ("Recession", "Period of temporary economic decline with falling GDP and rising unemployment",
             FinancialCategory.ECONOMICS, ["Two consecutive quarters of negative GDP growth"], 2),
            ("Monetary Policy", "Central bank actions to control money supply and interest rates",
             FinancialCategory.ECONOMICS, ["Federal Reserve", "Interest rate adjustments"], 2),
            ("Fiscal Policy", "Government use of taxation and spending to influence the economy",
             FinancialCategory.ECONOMICS, ["Government spending", "Tax policy"], 2),
            
            # Market terms
            ("Bull Market", "Period of rising stock prices and investor optimism",
             FinancialCategory.INVESTING, ["Bear market opposite"], 1),
            ("Bear Market", "Period of falling stock prices and investor pessimism",
             FinancialCategory.INVESTING, ["Typically 20% decline from recent highs"], 1),
            ("Volatility", "Measure of price variation of a financial instrument over time",
             FinancialCategory.INVESTING, ["Standard deviation", "VIX index"], 2),
            ("Market Capitalization", "Total value of a company's outstanding shares",
             FinancialCategory.INVESTING, ["Large cap", "Mid cap", "Small cap"], 1),
        ]
        
        for term, definition, category, examples, difficulty in terms:
            t = FinancialTerm(
                term_id=f"fin_term_{uuid.uuid4().hex[:8]}",
                term=term,
                definition=definition,
                category=category,
                examples=examples,
                difficulty=difficulty,
            )
            self._terms[t.term_id] = t
    
    def _initialize_ratios(self) -> None:
        """Initialize with essential financial ratios."""
        ratios = [
            # Profitability ratios
            ("Return on Equity (ROE)", FinancialRatioType.PROFITABILITY,
             "Net Income / Shareholders' Equity",
             "Measures how efficiently a company generates profits from shareholders' equity",
             "Higher is better; compare to industry average; very high may indicate leverage risk",
             "15-20%", ["Declining trend", "Below industry average", "Very high with high debt"]),
            
            ("Profit Margin", FinancialRatioType.PROFITABILITY,
             "Net Income / Revenue",
             "Shows what percentage of revenue becomes profit",
             "Higher margins indicate better cost control and pricing power",
             "Varies by industry", ["Declining margins", "Below competitors", "Negative margins"]),
            
            ("Return on Assets (ROA)", FinancialRatioType.PROFITABILITY,
             "Net Income / Total Assets",
             "Measures how efficiently a company uses its assets to generate profit",
             "Higher is better; capital-intensive industries typically have lower ROA",
             "5-10%", ["Below industry average", "Declining trend"]),
            
            # Liquidity ratios
            ("Current Ratio", FinancialRatioType.LIQUIDITY,
             "Current Assets / Current Liabilities",
             "Measures ability to pay short-term obligations",
             "Above 1.0 means current assets exceed current liabilities",
             "1.5-2.0", ["Below 1.0", "Rapidly declining"]),
            
            ("Quick Ratio", FinancialRatioType.LIQUIDITY,
             "(Current Assets - Inventory) / Current Liabilities",
             "More strict liquidity measure excluding inventory",
             "Above 1.0 indicates good short-term financial health",
             "1.0-1.5", ["Below 1.0 for extended periods"]),
            
            # Leverage ratios
            ("Debt-to-Equity Ratio", FinancialRatioType.LEVERAGE,
             "Total Debt / Total Equity",
             "Measures the proportion of debt financing relative to equity",
             "Lower is generally safer; varies significantly by industry",
             "0.5-1.5", ["Above 2.0", "Rapidly increasing"]),
            
            ("Interest Coverage Ratio", FinancialRatioType.LEVERAGE,
             "EBIT / Interest Expense",
             "Measures ability to pay interest on outstanding debt",
             "Higher is better; indicates financial stability",
             "> 3.0", ["Below 1.5", "Declining trend"]),
            
            # Valuation ratios
            ("Price-to-Earnings (P/E) Ratio", FinancialRatioType.VALUATION,
             "Stock Price / Earnings Per Share",
             "Measures how much investors pay for each dollar of earnings",
             "Lower may indicate undervaluation; compare to industry and growth rate",
             "15-25 for mature companies", ["Very high P/E", "Negative earnings"]),
            
            ("Price-to-Book (P/B) Ratio", FinancialRatioType.VALUATION,
             "Stock Price / Book Value Per Share",
             "Compares market value to book value of equity",
             "Below 1.0 may indicate undervaluation; above 1.0 indicates market expects growth",
             "1.0-3.0", ["Very high P/B for declining company", "Below 0.5"]),
            
            # Efficiency ratios
            ("Asset Turnover", FinancialRatioType.EFFICIENCY,
             "Revenue / Total Assets",
             "Measures how efficiently a company uses assets to generate revenue",
             "Higher indicates better efficiency; varies by industry",
             "Varies by industry", ["Declining trend", "Below industry average"]),
        ]
        
        for name, ratio_type, formula, desc, interp, good_range, warnings in ratios:
            r = FinancialRatio(
                ratio_id=f"fin_ratio_{uuid.uuid4().hex[:8]}",
                name=name,
                ratio_type=ratio_type,
                formula=formula,
                description=desc,
                interpretation=interp,
                good_range=good_range,
                warning_signs=warnings,
                difficulty=2,
            )
            self._ratios[r.ratio_id] = r
    
    def _initialize_concepts(self) -> None:
        """Initialize with investment concepts."""
        concepts = [
            # Basic concepts
            ("Time Value of Money", None,
             "Money available now is worth more than the same amount in the future",
             ["Present value calculations", "Future value calculations", "Discount rates"],
             ["Inflation risk", "Opportunity cost considerations"],
             ["Better investment decisions", "Loan evaluation", "Retirement planning"], 1),
            
            ("Risk vs Return", None,
             "Higher potential returns come with higher risk",
             ["Risk premium", "Risk tolerance assessment", "Expected return calculations"],
             ["Market risk", "Specific risk", "Liquidity risk"],
             ["Appropriate risk-taking", "Portfolio construction"], 1),
            
            ("Dollar Cost Averaging", None,
             "Investing fixed amounts at regular intervals regardless of price",
             ["Consistent investment schedule", "Fixed dollar amounts", "Long-term focus"],
             ["May miss timing opportunities", "Requires discipline", "Market timing temptation"],
             ["Reduces timing risk", "Builds investing habit", "Emotional discipline"], 1),
            
            # Asset class concepts
            ("Stock Investing", AssetClass.EQUITY,
             "Buying ownership shares in publicly traded companies",
             ["Fundamental analysis", "Technical analysis", "Diversification"],
             ["Market risk", "Company-specific risk", "Volatility"],
             ["Potential for high returns", "Dividend income", "Ownership stake"], 2),
            
            ("Bond Investing", AssetClass.FIXED_INCOME,
             "Lending money to governments or corporations in exchange for interest payments",
             ["Credit quality assessment", "Duration management", "Yield analysis"],
             ["Interest rate risk", "Credit risk", "Inflation risk"],
             ["Regular income", "Lower volatility than stocks", "Portfolio diversification"], 2),
            
            ("Index Funds", AssetClass.EQUITY,
             "Passive investment funds that track a market index",
             ["Low costs", "Broad market exposure", "Passive management"],
             ["Market risk", "Cannot beat the market", "Limited customization"],
             ["Diversification", "Low fees", "Consistent performance"], 1),
            
            ("ETFs", AssetClass.EQUITY,
             "Exchange-traded funds that trade like stocks",
             ["Intraday trading", "Lower minimums", "Tax efficiency"],
             ["Trading costs", "Bid-ask spreads", "Premiums/discounts to NAV"],
             ["Flexibility", "Transparency", "Diversification"], 1),
            
            # Strategy concepts
            ("Value Investing", AssetClass.EQUITY,
             "Buying stocks that appear underpriced relative to their intrinsic value",
             ["Margin of safety", "Intrinsic value estimation", "Contrarian approach"],
             ["Value traps", "Extended underperformance", "Analysis errors"],
             ["Potential for significant gains", "Lower downside risk"], 3),
            
            ("Growth Investing", AssetClass.EQUITY,
             "Buying stocks of companies expected to grow at an above-average rate",
             ["Revenue growth focus", "Earnings growth", "Market expansion"],
             ["Overvaluation risk", "Growth slowdown", "High volatility"],
             ["Potential for high returns", "Momentum benefits"], 3),
            
            ("Dividend Investing", AssetClass.EQUITY,
             "Focusing on stocks that pay regular dividends",
             ["Dividend yield", "Dividend growth", "Payout ratio analysis"],
             ["Dividend cuts", "Limited growth potential", "Tax considerations"],
             ["Regular income", "Lower volatility", "Inflation hedge"], 2),
        ]
        
        for name, asset_class, desc, principles, risks, benefits, difficulty in concepts:
            c = InvestmentConcept(
                concept_id=f"fin_concept_{uuid.uuid4().hex[:8]}",
                name=name,
                asset_class=asset_class,
                description=desc,
                key_principles=principles,
                risks=risks,
                benefits=benefits,
                difficulty=difficulty,
            )
            self._concepts[c.concept_id] = c
    
    def _initialize_indicators(self) -> None:
        """Initialize with economic indicators."""
        indicators = [
            # Leading indicators
            ("Stock Market Returns", EconomicIndicatorType.LEADING,
             "Performance of major stock indices",
             "Index values (S&P 500, Dow Jones, NASDAQ)",
             "Daily",
             "High",
             "Rising markets often predict economic expansion; falling markets may signal recession",
             ["Consumer confidence", "Business investment", "Wealth effect"]),
            
            ("Building Permits", EconomicIndicatorType.LEADING,
             "Number of new building permits issued",
             "Permits issued for new residential construction",
             "Monthly",
             "Medium",
             "Increase suggests economic confidence and future construction activity",
             ["Construction employment", "Building materials demand", "Housing market"]),
            
            ("Consumer Confidence Index", EconomicIndicatorType.LEADING,
             "Survey measuring consumer optimism about the economy",
             "Survey of 5,000 households by The Conference Board",
             "Monthly",
             "High",
             "Higher confidence suggests increased consumer spending",
             ["Retail sales", "Auto sales", "Housing demand"]),
            
            # Coincident indicators
            ("GDP Growth", EconomicIndicatorType.COINCIDENT,
             "Rate of change in gross domestic product",
             "Total value of goods and services produced",
             "Quarterly",
             "Very High",
             "Primary measure of economic health; positive growth indicates expansion",
             ["Employment", "Corporate profits", "Government revenue"]),
            
            ("Employment Level", EconomicIndicatorType.COINCIDENT,
             "Total number of employed workers",
             "Payroll survey, household survey",
             "Monthly",
             "Very High",
             "Rising employment indicates economic expansion",
             ["Consumer spending", "Tax revenue", "Social stability"]),
            
            ("Industrial Production", EconomicIndicatorType.COINCIDENT,
             "Output of factories, mines, and utilities",
             "Federal Reserve index of industrial output",
             "Monthly",
             "High",
             "Rising production indicates manufacturing strength",
             ["Manufacturing employment", "Energy demand", "Freight volumes"]),
            
            # Lagging indicators
            ("Unemployment Rate", EconomicIndicatorType.LAGGING,
             "Percentage of labor force that is unemployed",
             "Labor force survey",
             "Monthly",
             "Very High",
             "Unemployment typically peaks after recession ends",
             ["Consumer spending", "Government spending", "Social programs"]),
            
            ("Inflation Rate (CPI)", EconomicIndicatorType.LAGGING,
             "Rate of change in consumer prices",
             "Consumer Price Index basket of goods",
             "Monthly",
             "Very High",
             "Rising inflation may indicate overheating economy; falling may signal weakness",
             ["Interest rates", "Wage negotiations", "Purchasing power"]),
            
            ("Interest Rates", EconomicIndicatorType.LAGGING,
             "Cost of borrowing money",
             "Federal funds rate, treasury yields",
             "Daily/continuous",
             "Very High",
             "Central banks raise rates to cool economy, lower to stimulate",
             ["Bond prices", "Mortgage rates", "Currency values"]),
        ]
        
        for name, ind_type, desc, measurement, freq, importance, interp, impacts in indicators:
            ind = EconomicIndicator(
                indicator_id=f"econ_ind_{uuid.uuid4().hex[:8]}",
                name=name,
                indicator_type=ind_type,
                description=desc,
                measurement=measurement,
                frequency=freq,
                importance=importance,
                interpretation=interp,
                impact_on_markets=impacts,
                difficulty=2,
            )
            self._indicators[ind.indicator_id] = ind
    
    # ========================================================================
    # TERM MANAGEMENT
    # ========================================================================
    
    def add_term(self, term: str, definition: str, category: FinancialCategory,
                 examples: Optional[List[str]] = None, difficulty: int = 1) -> FinancialTerm:
        """Add a financial term."""
        t = FinancialTerm(
            term_id=f"fin_term_{uuid.uuid4().hex[:8]}",
            term=term,
            definition=definition,
            category=category,
            examples=examples or [],
            difficulty=difficulty,
        )
        self._terms[t.term_id] = t
        return t
    
    def get_term(self, term_id: str) -> Optional[FinancialTerm]:
        """Get a term by ID."""
        return self._terms.get(term_id)
    
    def search_terms(self, query: str) -> List[FinancialTerm]:
        """Search terms by text."""
        query_lower = query.lower()
        return [
            t for t in self._terms.values()
            if query_lower in t.term.lower() or query_lower in t.definition.lower()
        ]
    
    def get_terms_by_category(self, category: FinancialCategory) -> List[FinancialTerm]:
        """Get terms by category."""
        return [t for t in self._terms.values() if t.category == category]
    
    # ========================================================================
    # RATIO MANAGEMENT
    # ========================================================================
    
    def add_ratio(self, name: str, ratio_type: FinancialRatioType,
                  formula: str, description: str, interpretation: str) -> FinancialRatio:
        """Add a financial ratio."""
        r = FinancialRatio(
            ratio_id=f"fin_ratio_{uuid.uuid4().hex[:8]}",
            name=name,
            ratio_type=ratio_type,
            formula=formula,
            description=description,
            interpretation=interpretation,
        )
        self._ratios[r.ratio_id] = r
        return r
    
    def get_ratio(self, ratio_id: str) -> Optional[FinancialRatio]:
        """Get a ratio by ID."""
        return self._ratios.get(ratio_id)
    
    def get_ratios_by_type(self, ratio_type: FinancialRatioType) -> List[FinancialRatio]:
        """Get ratios by type."""
        return [r for r in self._ratios.values() if r.ratio_type == ratio_type]
    
    # ========================================================================
    # CONCEPT MANAGEMENT
    # ========================================================================
    
    def add_concept(self, name: str, description: str,
                    asset_class: Optional[AssetClass] = None,
                    key_principles: Optional[List[str]] = None) -> InvestmentConcept:
        """Add an investment concept."""
        c = InvestmentConcept(
            concept_id=f"fin_concept_{uuid.uuid4().hex[:8]}",
            name=name,
            asset_class=asset_class,
            description=description,
            key_principles=key_principles or [],
        )
        self._concepts[c.concept_id] = c
        return c
    
    def get_concept(self, concept_id: str) -> Optional[InvestmentConcept]:
        """Get a concept by ID."""
        return self._concepts.get(concept_id)
    
    def search_concepts(self, query: str) -> List[InvestmentConcept]:
        """Search concepts by text."""
        query_lower = query.lower()
        return [
            c for c in self._concepts.values()
            if query_lower in c.name.lower() or query_lower in c.description.lower()
        ]
    
    # ========================================================================
    # INDICATOR MANAGEMENT
    # ========================================================================
    
    def add_indicator(self, name: str, indicator_type: EconomicIndicatorType,
                      description: str = "") -> EconomicIndicator:
        """Add an economic indicator."""
        ind = EconomicIndicator(
            indicator_id=f"econ_ind_{uuid.uuid4().hex[:8]}",
            name=name,
            indicator_type=indicator_type,
            description=description,
        )
        self._indicators[ind.indicator_id] = ind
        return ind
    
    def get_indicator(self, indicator_id: str) -> Optional[EconomicIndicator]:
        """Get an indicator by ID."""
        return self._indicators.get(indicator_id)
    
    def get_indicators_by_type(self, ind_type: EconomicIndicatorType) -> List[EconomicIndicator]:
        """Get indicators by type."""
        return [i for i in self._indicators.values() if i.indicator_type == ind_type]
    
    # ========================================================================
    # CALCULATIONS
    # ========================================================================
    
    def calculate_present_value(self, future_value: float, rate: float, periods: int) -> float:
        """Calculate present value of a future amount."""
        return future_value / ((1 + rate) ** periods)
    
    def calculate_future_value(self, present_value: float, rate: float, periods: int) -> float:
        """Calculate future value of a present amount."""
        return present_value * ((1 + rate) ** periods)
    
    def calculate_compound_annual_growth_rate(self, beginning_value: float,
                                              ending_value: float, years: int) -> float:
        """Calculate CAGR."""
        return (ending_value / beginning_value) ** (1 / years) - 1
    
    def calculate_ratio(self, ratio_name: str, values: Dict[str, float]) -> Optional[float]:
        """Calculate a financial ratio from provided values."""
        ratio_name_lower = ratio_name.lower()
        
        if "current ratio" in ratio_name_lower:
            if "current_assets" in values and "current_liabilities" in values:
                return values["current_assets"] / values["current_liabilities"]
        elif "quick ratio" in ratio_name_lower:
            if all(k in values for k in ["current_assets", "inventory", "current_liabilities"]):
                return (values["current_assets"] - values["inventory"]) / values["current_liabilities"]
        elif "debt" in ratio_name_lower and "equity" in ratio_name_lower:
            if "total_debt" in values and "total_equity" in values:
                return values["total_debt"] / values["total_equity"]
        elif "pe" in ratio_name_lower or "price-to-earnings" in ratio_name_lower:
            if "stock_price" in values and "eps" in values:
                return values["stock_price"] / values["eps"]
        elif "roe" in ratio_name_lower or "return on equity" in ratio_name_lower:
            if "net_income" in values and "shareholders_equity" in values:
                return values["net_income"] / values["shareholders_equity"]
        elif "profit margin" in ratio_name_lower:
            if "net_income" in values and "revenue" in values:
                return values["net_income"] / values["revenue"]
        
        return None
    
    # ========================================================================
    # EXERCISE GENERATION
    # ========================================================================
    
    def generate_term_exercise(self, term: Optional[FinancialTerm] = None) -> Dict[str, Any]:
        """Generate a terminology exercise."""
        if term is None:
            terms = list(self._terms.values())
            if not terms:
                return {"error": "No terms available"}
            term = random.choice(terms)
        
        # Get distractors
        all_definitions = [t.definition for t in self._terms.values() if t.term_id != term.term_id]
        distractors = random.sample(all_definitions, min(3, len(all_definitions)))
        
        options = [term.definition] + distractors
        random.shuffle(options)
        
        return {
            "exercise_id": f"ex_{uuid.uuid4().hex[:8]}",
            "type": "term_definition",
            "question": f"What is the definition of '{term.term}'?",
            "category": term.category.value,
            "options": options,
            "correct_answer": term.definition,
            "correct_index": options.index(term.definition),
            "difficulty": term.difficulty,
        }
    
    def generate_ratio_exercise(self, ratio: Optional[FinancialRatio] = None) -> Dict[str, Any]:
        """Generate a ratio exercise."""
        if ratio is None:
            ratios = list(self._ratios.values())
            if not ratios:
                return {"error": "No ratios available"}
            ratio = random.choice(ratios)
        
        # Generate calculation problem
        return {
            "exercise_id": f"ex_{uuid.uuid4().hex[:8]}",
            "type": "ratio_calculation",
            "question": f"Calculate the {ratio.name} using the formula: {ratio.formula}",
            "ratio_name": ratio.name,
            "formula": ratio.formula,
            "description": ratio.description,
            "interpretation": ratio.interpretation,
            "difficulty": ratio.difficulty,
        }
    
    def generate_concept_exercise(self, concept: Optional[InvestmentConcept] = None) -> Dict[str, Any]:
        """Generate a concept exercise."""
        if concept is None:
            concepts = list(self._concepts.values())
            if not concepts:
                return {"error": "No concepts available"}
            concept = random.choice(concepts)
        
        return {
            "exercise_id": f"ex_{uuid.uuid4().hex[:8]}",
            "type": "concept_understanding",
            "question": f"Explain the concept of {concept.name}",
            "concept_name": concept.name,
            "description": concept.description,
            "key_principles": concept.key_principles,
            "risks": concept.risks,
            "benefits": concept.benefits,
            "difficulty": concept.difficulty,
        }
    
    def generate_calculation_exercise(self) -> Dict[str, Any]:
        """Generate a time-value-of-money calculation exercise."""
        exercise_type = random.choice(["present_value", "future_value", "cagr"])
        
        if exercise_type == "present_value":
            fv = random.randint(1000, 10000)
            rate = random.choice([0.05, 0.08, 0.10, 0.12])
            periods = random.randint(1, 10)
            answer = round(self.calculate_present_value(fv, rate, periods), 2)
            
            return {
                "exercise_id": f"ex_{uuid.uuid4().hex[:8]}",
                "type": "calculation",
                "question": f"Calculate the present value of ${fv:,} to be received in {periods} years, assuming a {rate*100:.0f}% discount rate.",
                "given": {"future_value": fv, "rate": rate, "periods": periods},
                "correct_answer": answer,
                "formula": "PV = FV / (1 + r)^n",
                "difficulty": 2,
            }
        elif exercise_type == "future_value":
            pv = random.randint(1000, 10000)
            rate = random.choice([0.05, 0.08, 0.10, 0.12])
            periods = random.randint(1, 10)
            answer = round(self.calculate_future_value(pv, rate, periods), 2)
            
            return {
                "exercise_id": f"ex_{uuid.uuid4().hex[:8]}",
                "type": "calculation",
                "question": f"Calculate the future value of ${pv:,} invested for {periods} years at {rate*100:.0f}% annual return.",
                "given": {"present_value": pv, "rate": rate, "periods": periods},
                "correct_answer": answer,
                "formula": "FV = PV × (1 + r)^n",
                "difficulty": 2,
            }
        else:
            begin = random.randint(100, 1000)
            end = random.randint(begin + 100, begin * 3)
            years = random.randint(3, 10)
            answer = round(self.calculate_compound_annual_growth_rate(begin, end, years) * 100, 2)
            
            return {
                "exercise_id": f"ex_{uuid.uuid4().hex[:8]}",
                "type": "calculation",
                "question": f"An investment grew from ${begin:,} to ${end:,} over {years} years. Calculate the CAGR.",
                "given": {"beginning_value": begin, "ending_value": end, "years": years},
                "correct_answer": f"{answer}%",
                "formula": "CAGR = (End/Begin)^(1/n) - 1",
                "difficulty": 3,
            }
    
    # ========================================================================
    # STATISTICS AND EXPORT
    # ========================================================================
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get finance domain learning statistics."""
        return {
            "terms": {
                "total": len(self._terms),
                "by_category": {
                    cat.value: sum(1 for t in self._terms.values() if t.category == cat)
                    for cat in FinancialCategory
                },
            },
            "ratios": {
                "total": len(self._ratios),
                "by_type": {
                    rt.value: sum(1 for r in self._ratios.values() if r.ratio_type == rt)
                    for rt in FinancialRatioType
                },
            },
            "concepts": {
                "total": len(self._concepts),
                "by_asset_class": {
                    ac.value if ac else "general": sum(
                        1 for c in self._concepts.values() 
                        if (c.asset_class.value if c.asset_class else "general") == (ac.value if ac else "general")
                    )
                    for ac in list(AssetClass) + [None]
                },
            },
            "indicators": {
                "total": len(self._indicators),
                "by_type": {
                    it.value: sum(1 for i in self._indicators.values() if i.indicator_type == it)
                    for it in EconomicIndicatorType
                },
            },
            "total_reviews": len(self._review_history),
        }
    
    def export_progress(self) -> Dict[str, Any]:
        """Export learning progress for persistence."""
        return {
            "terms": {k: v.to_dict() for k, v in self._terms.items()},
            "ratios": {k: v.to_dict() for k, v in self._ratios.items()},
            "concepts": {k: v.to_dict() for k, v in self._concepts.items()},
            "indicators": {k: v.to_dict() for k, v in self._indicators.items()},
            "review_history": self._review_history,
            "statistics": self.get_statistics(),
        }
    
    def import_progress(self, data: Dict[str, Any]) -> None:
        """Import learning progress from persistence."""
        if "terms" in data:
            for k, v in data["terms"].items():
                self._terms[k] = FinancialTerm.from_dict(v)
        
        if "ratios" in data:
            for k, v in data["ratios"].items():
                self._ratios[k] = FinancialRatio.from_dict(v)
        
        if "concepts" in data:
            for k, v in data["concepts"].items():
                self._concepts[k] = InvestmentConcept.from_dict(v)
        
        if "indicators" in data:
            for k, v in data["indicators"].items():
                self._indicators[k] = EconomicIndicator.from_dict(v)
        
        if "review_history" in data:
            self._review_history = data["review_history"]
    
    def save_patterns_to_ltm(self) -> int:
        """Save learned finance patterns to Long-Term Memory."""
        from rpa.core.node import Node, NodeType
        
        count = 0
        
        # Save terms
        for term in self._terms.values():
            node = Node(
                node_id=f"fin_term:{term.term_id}",
                label=term.term,
                node_type=NodeType.CONCEPT,
                content=term.definition,
                domain="finance",
                hierarchy_level=1,
                metadata={
                    "type": "financial_term",
                    "category": term.category.value,
                    "examples": term.examples,
                },
            )
            self.ltm.consolidate(node, source="finance_domain")
            count += 1
        
        # Save ratios
        for ratio in self._ratios.values():
            node = Node(
                node_id=f"fin_ratio:{ratio.ratio_id}",
                label=ratio.name,
                node_type=NodeType.CONCEPT,
                content=ratio.formula,
                domain="finance",
                hierarchy_level=2,
                metadata={
                    "type": "financial_ratio",
                    "ratio_type": ratio.ratio_type.value,
                    "interpretation": ratio.interpretation,
                },
            )
            self.ltm.consolidate(node, source="finance_domain")
            count += 1
        
        # Save concepts
        for concept in self._concepts.values():
            node = Node(
                node_id=f"fin_concept:{concept.concept_id}",
                label=concept.name,
                node_type=NodeType.CONCEPT,
                content=concept.description,
                domain="finance",
                hierarchy_level=2,
                metadata={
                    "type": "investment_concept",
                    "asset_class": concept.asset_class.value if concept.asset_class else None,
                    "key_principles": concept.key_principles,
                },
            )
            self.ltm.consolidate(node, source="finance_domain")
            count += 1
        
        # Save indicators
        for indicator in self._indicators.values():
            node = Node(
                node_id=f"econ_indicator:{indicator.indicator_id}",
                label=indicator.name,
                node_type=NodeType.CONCEPT,
                content=indicator.description,
                domain="finance",
                hierarchy_level=2,
                metadata={
                    "type": "economic_indicator",
                    "indicator_type": indicator.indicator_type.value,
                    "interpretation": indicator.interpretation,
                },
            )
            self.ltm.consolidate(node, source="finance_domain")
            count += 1
        
        logger.info(f"Saved {count} finance patterns to LTM")
        return count
