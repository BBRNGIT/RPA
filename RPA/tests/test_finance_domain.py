"""
Tests for the Finance Domain module.
"""

import pytest

from rpa.domains.finance import (
    FinanceDomain,
    FinancialTerm,
    FinancialRatio,
    InvestmentConcept,
    EconomicIndicator,
    FinancialCategory,
    FinancialRatioType,
    AssetClass,
    EconomicIndicatorType,
    FinanceProficiency,
)


class TestFinanceEnums:
    """Test enum definitions."""
    
    def test_financial_category_enum(self):
        assert FinancialCategory.TERMINOLOGY.value == "terminology"
        assert FinancialCategory.INVESTING.value == "investing"
        assert len(list(FinancialCategory)) == 6
    
    def test_asset_class_enum(self):
        assert AssetClass.EQUITY.value == "equity"
        assert AssetClass.FIXED_INCOME.value == "fixed_income"
    
    def test_financial_ratio_type_enum(self):
        assert FinancialRatioType.PROFITABILITY.value == "profitability"
        assert FinancialRatioType.LIQUIDITY.value == "liquidity"
    
    def test_economic_indicator_type_enum(self):
        assert EconomicIndicatorType.LEADING.value == "leading"
        assert EconomicIndicatorType.LAGGING.value == "lagging"


class TestFinancialTerm:
    """Test FinancialTerm dataclass."""
    
    def test_term_creation(self):
        term = FinancialTerm(
            term_id="test_1",
            term="Asset",
            definition="A resource with economic value",
            category=FinancialCategory.TERMINOLOGY,
        )
        assert term.term == "Asset"
        assert term.proficiency == FinanceProficiency.NOVICE
    
    def test_term_serialization(self):
        term = FinancialTerm(
            term_id="test_2",
            term="Equity",
            definition="Ownership value",
            category=FinancialCategory.TERMINOLOGY,
            examples=["Stock"],
        )
        data = term.to_dict()
        restored = FinancialTerm.from_dict(data)
        assert restored.term == term.term


class TestFinancialRatio:
    """Test FinancialRatio dataclass."""
    
    def test_ratio_creation(self):
        ratio = FinancialRatio(
            ratio_id="test_ratio_1",
            name="Test Ratio",
            ratio_type=FinancialRatioType.PROFITABILITY,
            formula="A / B",
            description="Test ratio",
            interpretation="Higher is better",
        )
        assert ratio.name == "Test Ratio"
    
    def test_ratio_serialization(self):
        ratio = FinancialRatio(
            ratio_id="test_ratio_2",
            name="ROE",
            ratio_type=FinancialRatioType.PROFITABILITY,
            formula="Net Income / Equity",
            description="Return on Equity",
            interpretation="Higher is better",
        )
        data = ratio.to_dict()
        restored = FinancialRatio.from_dict(data)
        assert restored.formula == ratio.formula


class TestInvestmentConcept:
    """Test InvestmentConcept dataclass."""
    
    def test_concept_creation(self):
        concept = InvestmentConcept(
            concept_id="test_c_1",
            name="Diversification",
            asset_class=None,
            description="Risk management strategy",
        )
        assert concept.name == "Diversification"
    
    def test_concept_with_asset_class(self):
        concept = InvestmentConcept(
            concept_id="test_c_2",
            name="Stock Investing",
            asset_class=AssetClass.EQUITY,
            description="Buying company shares",
        )
        assert concept.asset_class == AssetClass.EQUITY


class TestEconomicIndicator:
    """Test EconomicIndicator dataclass."""
    
    def test_indicator_creation(self):
        indicator = EconomicIndicator(
            indicator_id="test_ind_1",
            name="GDP",
            indicator_type=EconomicIndicatorType.COINCIDENT,
            description="Gross Domestic Product",
        )
        assert indicator.name == "GDP"
        assert indicator.indicator_type == EconomicIndicatorType.COINCIDENT


class TestFinanceDomain:
    """Test FinanceDomain class."""
    
    @pytest.fixture
    def finance_domain(self):
        return FinanceDomain()
    
    def test_domain_creation(self, finance_domain):
        assert finance_domain is not None
        assert len(finance_domain._terms) > 0
    
    def test_has_terminology(self, finance_domain):
        assert len(finance_domain._terms) >= 20
        terms = list(finance_domain._terms.values())
        term_names = [t.term for t in terms]
        assert "Asset" in term_names
        assert "Liability" in term_names
    
    def test_has_ratios(self, finance_domain):
        assert len(finance_domain._ratios) >= 8
        ratios = list(finance_domain._ratios.values())
        ratio_names = [r.name for r in ratios]
        assert any("P/E" in n or "Price-to-Earnings" in n for n in ratio_names)
    
    def test_has_concepts(self, finance_domain):
        assert len(finance_domain._concepts) >= 8
    
    def test_has_indicators(self, finance_domain):
        assert len(finance_domain._indicators) >= 6
    
    def test_add_term(self, finance_domain):
        term = finance_domain.add_term(
            term="Test Term",
            definition="Test definition",
            category=FinancialCategory.TERMINOLOGY,
        )
        assert term.term == "Test Term"
        assert term.term_id in finance_domain._terms
    
    def test_search_terms(self, finance_domain):
        results = finance_domain.search_terms("asset")
        assert len(results) > 0
    
    def test_get_terms_by_category(self, finance_domain):
        investing_terms = finance_domain.get_terms_by_category(FinancialCategory.INVESTING)
        assert len(investing_terms) > 0
    
    def test_add_ratio(self, finance_domain):
        ratio = finance_domain.add_ratio(
            name="Test Ratio",
            ratio_type=FinancialRatioType.LIQUIDITY,
            formula="X / Y",
            description="Test",
            interpretation="Test",
        )
        assert ratio.name == "Test Ratio"
    
    def test_get_ratios_by_type(self, finance_domain):
        profitability = finance_domain.get_ratios_by_type(FinancialRatioType.PROFITABILITY)
        assert len(profitability) > 0
    
    def test_add_concept(self, finance_domain):
        concept = finance_domain.add_concept(
            name="Test Concept",
            description="Test description",
        )
        assert concept.name == "Test Concept"
    
    def test_get_indicators_by_type(self, finance_domain):
        leading = finance_domain.get_indicators_by_type(EconomicIndicatorType.LEADING)
        assert len(leading) >= 2


class TestCalculations:
    """Test financial calculations."""
    
    @pytest.fixture
    def finance_domain(self):
        return FinanceDomain()
    
    def test_present_value(self, finance_domain):
        pv = finance_domain.calculate_present_value(1100, 0.10, 1)
        assert abs(pv - 1000) < 1
    
    def test_future_value(self, finance_domain):
        fv = finance_domain.calculate_future_value(1000, 0.10, 1)
        assert abs(fv - 1100) < 1
    
    def test_cagr(self, finance_domain):
        cagr = finance_domain.calculate_compound_annual_growth_rate(100, 121, 2)
        assert abs(cagr - 0.10) < 0.001
    
    def test_calculate_ratio(self, finance_domain):
        # Test current ratio
        result = finance_domain.calculate_ratio(
            "Current Ratio",
            {"current_assets": 200, "current_liabilities": 100}
        )
        assert result == 2.0
    
    def test_calculate_debt_to_equity(self, finance_domain):
        result = finance_domain.calculate_ratio(
            "Debt-to-Equity",
            {"total_debt": 150, "total_equity": 100}
        )
        assert result == 1.5


class TestExerciseGeneration:
    """Test exercise generation."""
    
    @pytest.fixture
    def finance_domain(self):
        return FinanceDomain()
    
    def test_generate_term_exercise(self, finance_domain):
        exercise = finance_domain.generate_term_exercise()
        assert "exercise_id" in exercise
        assert "question" in exercise
    
    def test_generate_ratio_exercise(self, finance_domain):
        exercise = finance_domain.generate_ratio_exercise()
        assert "exercise_id" in exercise
        assert "formula" in exercise
    
    def test_generate_calculation_exercise(self, finance_domain):
        exercise = finance_domain.generate_calculation_exercise()
        assert "exercise_id" in exercise
        assert "correct_answer" in exercise


class TestStatisticsAndExport:
    """Test statistics and export."""
    
    @pytest.fixture
    def finance_domain(self):
        return FinanceDomain()
    
    def test_get_statistics(self, finance_domain):
        stats = finance_domain.get_statistics()
        assert "terms" in stats
        assert "ratios" in stats
        assert stats["terms"]["total"] > 0
    
    def test_export_import_progress(self, finance_domain):
        exported = finance_domain.export_progress()
        assert "terms" in exported
        assert "statistics" in exported
        
        new_domain = FinanceDomain()
        initial_count = len(new_domain._terms)
        new_domain.import_progress(exported)
        assert len(new_domain._terms) >= initial_count
    
    def test_save_patterns_to_ltm(self, finance_domain):
        count = finance_domain.save_patterns_to_ltm()
        expected = (
            len(finance_domain._terms) +
            len(finance_domain._ratios) +
            len(finance_domain._concepts) +
            len(finance_domain._indicators)
        )
        assert count >= expected
