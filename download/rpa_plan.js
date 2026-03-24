const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, Header, Footer, 
        AlignmentType, PageNumber, LevelFormat, HeadingLevel, BorderStyle, WidthType, 
        ShadingType, VerticalAlign, TableOfContents, PageBreak } = require('docx');
const fs = require('fs');

const colors = {
  primary: "#020617",
  body: "#1E293B",
  secondary: "#64748B",
  accent: "#94A3B8",
  tableBg: "#F8FAFC",
  headerBg: "#0F172A",
  priorityHigh: "#DC2626",
  priorityMed: "#F59E0B"
};

const tableBorder = { style: BorderStyle.SINGLE, size: 1, color: colors.secondary };
const cellBorders = { top: tableBorder, bottom: tableBorder, left: tableBorder, right: tableBorder };

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Times New Roman", size: 24 } } },
    paragraphStyles: [
      { id: "Title", name: "Title", basedOn: "Normal",
        run: { size: 56, bold: true, color: colors.primary, font: "Times New Roman" },
        paragraph: { spacing: { before: 240, after: 120 }, alignment: AlignmentType.CENTER } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 36, bold: true, color: colors.primary, font: "Times New Roman" },
        paragraph: { spacing: { before: 400, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, color: colors.body, font: "Times New Roman" },
        paragraph: { spacing: { before: 300, after: 150 }, outlineLevel: 1 } }
    ]
  },
  numbering: {
    config: [
      { reference: "bullet-list", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }
    ]
  },
  sections: [
    {
      properties: { page: { margin: { top: 0, right: 0, bottom: 0, left: 0 } } },
      children: [
        new Paragraph({ spacing: { before: 3000 }, children: [] }),
        new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "RPA AI SYSTEM", size: 72, bold: true, color: colors.primary })] }),
        new Paragraph({ spacing: { before: 400 }, children: [] }),
        new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "IMPLEMENTATION PLAN", size: 48, color: colors.secondary })] }),
        new Paragraph({ spacing: { before: 200 }, children: [] }),
        new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Self-Improvement • Multi-Domain • Intelligence Demo", size: 28, color: colors.body })] }),
        new Paragraph({ spacing: { before: 4000 }, children: [] }),
        new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Priority: SELF-IMPROVEMENT", size: 32, bold: true, color: colors.priorityHigh })] }),
        new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Domains: Medicine • Health • Finance • Markets • Conversations", size: 22, color: colors.body })] }),
        new Paragraph({ spacing: { before: 2000 }, children: [] }),
        new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Version 1.0 | March 2026", size: 20, color: colors.secondary })] }),
        new Paragraph({ children: [new PageBreak()] })
      ]
    },
    {
      properties: { page: { margin: { top: 1800, right: 1440, bottom: 1440, left: 1440 } } },
      headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT, children: [new TextRun({ text: "RPA Implementation Plan", color: colors.secondary, size: 18 })] })] }) },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Page ", size: 18, color: colors.secondary }), new TextRun({ children: [PageNumber.CURRENT], size: 18, color: colors.secondary }), new TextRun({ text: " of ", size: 18, color: colors.secondary }), new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 18, color: colors.secondary })] })] }) },
      children: [
        new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun("Table of Contents")] }),
        new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-3" }),
        new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Note: Right-click the TOC and select 'Update Field' to refresh page numbers.", color: "999999", size: 18 })] }),
        new Paragraph({ children: [new PageBreak()] }),

        // Executive Summary
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Executive Summary")] }),
        new Paragraph({ spacing: { after: 200, line: 346 }, children: [new TextRun({ text: "This document outlines a comprehensive implementation plan for advancing the RPA (Recursive Pattern Architecture) AI system. The primary objective is to activate and integrate the self-improvement system as the core learning driver, followed by expanding domain capabilities into Medicine, Health, Finance, Markets Analysis, and Conversations. The final phase delivers a demonstrable intelligence showcase. All implementations follow a strict no-regression policy, ensuring existing functionality remains intact while new capabilities are added incrementally.", color: colors.body })] }),
        new Paragraph({ spacing: { after: 200, line: 346 }, children: [new TextRun({ text: "The RPA system currently maintains 5,263 learned patterns with a target of 1,000,000 patterns. The closed-loop self-improvement infrastructure exists and is active, but requires integration as the primary learning mechanism. This plan transforms the system from a passive curriculum learner into an actively self-improving AI that learns through experience, reflection, and autonomous knowledge gap detection.", color: colors.body })] }),

        // Current State
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Current System State")] }),
        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("Active Infrastructure")] }),
        new Paragraph({ spacing: { after: 100, line: 346 }, children: [new TextRun({ text: "The RPA system has a robust foundation with all core modules operational. The training pipeline successfully processes HuggingFace datasets including wikitext and mbpp, achieving 500+ patterns daily. The Long-Term Memory (LTM) system persist patterns across sessions, and the SM-2 spaced repetition algorithm schedules reviews for optimal retention. GitHub Actions automate daily training and weekly assessments.", color: colors.body })] }),

        // PHASE 1
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("PHASE 1: Self-Improvement Integration")] }),
        new Paragraph({ spacing: { after: 100, line: 346 }, children: [new TextRun({ text: "Priority: CRITICAL", bold: true, color: colors.priorityHigh })] }),
        new Paragraph({ spacing: { after: 200, line: 346 }, children: [new TextRun({ text: "This phase activates the existing closed-loop learning infrastructure as the primary driver of AI improvement. The self-improvement system enables the AI to evaluate its own outcomes, reinforce successful patterns, mutate underperforming patterns, and autonomously detect knowledge gaps.", color: colors.body })] }),

        // Phase 1 Tickets Table
        createTicketTable([
          ["SI-001", "Unified Self-Improvement Entry Point", "Create rpa/training/self_improvement.py as unified orchestrator for closed-loop learning. Coordinate OutcomeEvaluator, ReinforcementTracker, PatternMutator, SelfQuestioningGate, RetryEngine, MemoryEvolution."],
          ["SI-002", "Integrate with Daily Timetable", "Add SELF_IMPROVEMENT_CYCLE task type to DailyTimetable. Schedule 3 cycles per day (morning, midday, evening)."],
          ["SI-003", "Confidence Threshold Configuration", "Create config/self_improvement.yaml with tunable parameters: confidence_threshold (0.7), mutation_rate (0.1), reinforcement_decay (0.05)."],
          ["SI-004", "Knowledge Gap Detection Loop", "Connect GapDetector to self-improvement cycle. Auto-generate learning goals from detected gaps."],
          ["SI-005", "Pattern Mutation Pipeline", "Implement mutation strategies: parameter_tweak, structure_rearrange, cross_pattern_merge. Track mutation lineage."],
          ["SI-006", "Self-Improvement Metrics Dashboard", "Create API endpoints and Next.js dashboard showing: cycles completed, patterns mutated, confidence trends, gap closures."],
          ["SI-007", "Regression Test Suite", "Create tests/regression/ suite with baseline tests for: training pipeline, memory persistence, curriculum loading, exam system."]
        ]),

        // PHASE 2
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("PHASE 2: Domain Curriculum Expansion")] }),
        new Paragraph({ spacing: { after: 100, line: 346 }, children: [new TextRun({ text: "Priority: HIGH", bold: true, color: colors.priorityMed })] }),
        new Paragraph({ spacing: { after: 200, line: 346 }, children: [new TextRun({ text: "This phase adds specialized domain knowledge in Medicine, Health, Finance, and Markets Analysis. Each domain follows the established curriculum pattern with track definitions, curriculum files, domain handlers, and safety constraints.", color: colors.body })] }),

        // Medicine
        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("2.1 Medicine Domain")] }),
        createTicketTable([
          ["MED-001", "Medicine Track Definition", "Create curriculum/tracks/medicine.json with 5 levels: Anatomy Basics, Physiology, Pathology, Clinical Reasoning, Medical Specialties."],
          ["MED-002", "Anatomy Curriculum Content", "Create curriculum/medicine/anatomy_basics.json with 500 terms: body systems, organs, bones, muscles with definitions and relationships."],
          ["MED-003", "Medicine Domain Handler", "Create rpa/domains/medicine.py with MedicineDomain class. Implement inquiry handlers for: symptom_analysis, drug_interaction, anatomy_query."],
          ["MED-004", "Medical Safety Constraints", "Add medical disclaimer system to rpa/safety/medical_safety.py. Block diagnosis claims. Require source attribution."]
        ]),

        // Health
        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("2.2 Health Domain")] }),
        createTicketTable([
          ["HEA-001", "Health Track Definition", "Create curriculum/tracks/health.json with 4 levels: Wellness Basics, Nutrition Science, Exercise Physiology, Mental Health."],
          ["HEA-002", "Nutrition Curriculum Content", "Create curriculum/health/nutrition.json with 400 terms: macronutrients, micronutrients, dietary patterns, food interactions."],
          ["HEA-003", "Health Domain Handler", "Create rpa/domains/health.py with HealthDomain class. Implement handlers: nutrition_query, exercise_recommendation, wellness_tip."]
        ]),

        // Finance
        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("2.3 Finance Domain")] }),
        createTicketTable([
          ["FIN-001", "Finance Track Definition", "Create curriculum/tracks/finance.json with 5 levels: Financial Literacy, Personal Finance, Corporate Finance, Investment Analysis, Financial Markets."],
          ["FIN-002", "Financial Terms Curriculum", "Create curriculum/finance/financial_terms.json with 600 terms: accounting, investment, banking, taxation with formulas."],
          ["FIN-003", "Finance Domain Handler", "Create rpa/domains/finance.py with FinanceDomain class. Implement handlers: financial_calculation, investment_analysis, budgeting_advice."]
        ]),

        // Markets
        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("2.4 Markets Analyst Domain")] }),
        createTicketTable([
          ["MKT-001", "Markets Track Definition", "Create curriculum/tracks/markets.json with 5 levels: Market Basics, Technical Analysis, Fundamental Analysis, Portfolio Management, Algorithmic Trading."],
          ["MKT-002", "Technical Analysis Curriculum", "Create curriculum/markets/technical_analysis.json with 400 terms: chart patterns, indicators, oscillators, trading signals."],
          ["MKT-003", "Markets Domain Handler", "Create rpa/domains/markets.py with MarketsDomain class. Implement handlers: market_analysis, indicator_explanation, risk_assessment."],
          ["MKT-004", "Finance API Integration", "Integrate z-ai-web-dev-sdk finance skill for real-time market data. Create rpa/integrations/finance_api.py wrapper."]
        ]),

        // PHASE 3
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("PHASE 3: Conversation System")] }),
        new Paragraph({ spacing: { after: 100, line: 346 }, children: [new TextRun({ text: "Priority: HIGH", bold: true, color: colors.priorityMed })] }),
        new Paragraph({ spacing: { after: 200, line: 346 }, children: [new TextRun({ text: "This phase enables natural conversation capabilities, allowing the AI to engage in multi-turn dialogue, maintain context, and provide coherent responses across domains.", color: colors.body })] }),
        createTicketTable([
          ["CONV-001", "Conversation Agent", "Create rpa/agents/conversation_agent.py with ConversationAgent class. Implement multi-turn dialogue handling and context maintenance."],
          ["CONV-002", "Context Memory System", "Create rpa/memory/conversation_memory.py for session-based context storage. Track topics, entities, sentiment across turns."],
          ["CONV-003", "Intent Recognition Module", "Create rpa/conversation/intent_recognizer.py for intent classification. Support: question, command, clarification, chitchat intents."],
          ["CONV-004", "LLM Integration", "Integrate z-ai-web-dev-sdk LLM for response generation. Create rpa/integrations/llm_client.py with context injection."],
          ["CONV-005", "WebSocket Chat Interface", "Create WebSocket endpoint at /ws/chat for real-time conversation. Implement session management and broadcasting."]
        ]),

        // PHASE 4
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("PHASE 4: Intelligence Demo")] }),
        new Paragraph({ spacing: { after: 100, line: 346 }, children: [new TextRun({ text: "Priority: HIGH", bold: true, color: colors.priorityMed })] }),
        new Paragraph({ spacing: { after: 200, line: 346 }, children: [new TextRun({ text: "This phase creates demonstrable AI intelligence capabilities for showcasing the system's learning and reasoning abilities.", color: colors.body })] }),
        createTicketTable([
          ["DEMO-001", "Live Learning Demo Page", "Create app/demo/live-learning/page.tsx with real-time training visualization showing patterns learned, memory consolidation, confidence scores."],
          ["DEMO-002", "Cross-Domain Knowledge Query", "Create demo endpoint that queries knowledge across all domains. Show concept links (e.g., heart anatomy → cardiovascular health → exercise)."],
          ["DEMO-003", "Self-Improvement Timeline", "Create visualization showing self-improvement history: pattern mutations, gap closures, confidence improvements over time."],
          ["DEMO-004", "Interactive Intelligence Test", "Create interactive exam demo where users test AI knowledge across domains with real-time scoring and explanations."],
          ["DEMO-005", "Learning Speed Benchmark", "Create benchmark showing learning acceleration: patterns/hour before self-improvement vs after with statistical significance."]
        ]),

        // PHASE 5
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("PHASE 5: Testing & Regression Prevention")] }),
        new Paragraph({ spacing: { after: 100, line: 346 }, children: [new TextRun({ text: "Priority: MANDATORY", bold: true, color: colors.priorityHigh })] }),
        new Paragraph({ spacing: { after: 200, line: 346 }, children: [new TextRun({ text: "This phase establishes comprehensive testing infrastructure to ensure all implementations proceed without regression.", color: colors.body })] }),
        createTicketTable([
          ["TEST-001", "Baseline Regression Suite", "Document current test baseline: 697 passing tests. Create snapshot of expected behaviors. Establish execution time baseline."],
          ["TEST-002", "CI Pipeline Enhancement", "Enhance .github/workflows/ with regression check stage. Fail builds if baseline tests drop below 697. Add memory leak detection."],
          ["TEST-003", "Integration Test Suite", "Create tests/integration/ with cross-module tests: training→memory→retrieval, self-improvement→mutation→evaluation."],
          ["TEST-004", "Performance Benchmark Suite", "Create benchmarks/ with performance tests: pattern storage rate, retrieval latency, memory usage growth."],
          ["TEST-005", "Rollback Procedure", "Document rollback procedure for each phase. Create scripts for reverting database migrations, memory state, and code changes."]
        ]),

        // Timeline
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Implementation Timeline")] }),
        createTimelineTable(),

        // Risk Mitigation
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Risk Mitigation")] }),
        new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, spacing: { after: 100, line: 346 }, children: [new TextRun({ text: "Regression Risk: All changes require passing baseline tests (697+) before merge. CI pipeline enforces test count and performance thresholds.", color: colors.body })] }),
        new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, spacing: { after: 100, line: 346 }, children: [new TextRun({ text: "Memory Corruption: Each phase includes memory state backups. Rollback scripts restore previous LTM state if issues detected.", color: colors.body })] }),
        new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, spacing: { after: 100, line: 346 }, children: [new TextRun({ text: "Integration Failures: Integration tests run after each phase. Dependencies clearly documented. Staged rollout per domain.", color: colors.body })] }),
        new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, spacing: { after: 100, line: 346 }, children: [new TextRun({ text: "Performance Degradation: Performance benchmarks run in CI. Alert on >10% latency increase. Memory usage monitored.", color: colors.body })] }),
        new Paragraph({ numbering: { reference: "bullet-list", level: 0 }, spacing: { after: 200, line: 346 }, children: [new TextRun({ text: "API Dependencies: External APIs (LLM, Finance) have fallback modes. Graceful degradation when services unavailable.", color: colors.body })] }),

        // Next Steps
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Next Steps")] }),
        new Paragraph({ spacing: { after: 200, line: 346 }, children: [new TextRun({ text: "To begin implementation, proceed with Ticket SI-001: Unified Self-Improvement Entry Point. This ticket establishes the foundation for all subsequent work and activates the self-improvement infrastructure that will accelerate learning across all domains.", color: colors.body })] })
      ]
    }
  ]
});

function createTicketTable(tickets) {
  const rows = [
    new TableRow({
      tableHeader: true,
      children: [
        new TableCell({ borders: cellBorders, width: { size: 1300, type: WidthType.DXA }, shading: { fill: colors.headerBg, type: ShadingType.CLEAR }, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Ticket", bold: true, color: "FFFFFF", size: 20 })] })] }),
        new TableCell({ borders: cellBorders, width: { size: 2800, type: WidthType.DXA }, shading: { fill: colors.headerBg, type: ShadingType.CLEAR }, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Title", bold: true, color: "FFFFFF", size: 20 })] })] }),
        new TableCell({ borders: cellBorders, width: { size: 5260, type: WidthType.DXA }, shading: { fill: colors.headerBg, type: ShadingType.CLEAR }, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Description & Acceptance Criteria", bold: true, color: "FFFFFF", size: 20 })] })] })
      ]
    })
  ];

  tickets.forEach((ticket, i) => {
    const isAlt = i % 2 === 1;
    rows.push(new TableRow({
      children: [
        new TableCell({ borders: cellBorders, width: { size: 1300, type: WidthType.DXA }, shading: isAlt ? { fill: colors.tableBg, type: ShadingType.CLEAR } : undefined, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: ticket[0], bold: true, size: 20 })] })] }),
        new TableCell({ borders: cellBorders, width: { size: 2800, type: WidthType.DXA }, shading: isAlt ? { fill: colors.tableBg, type: ShadingType.CLEAR } : undefined, children: [new Paragraph({ children: [new TextRun({ text: ticket[1], size: 20 })] })] }),
        new TableCell({ borders: cellBorders, width: { size: 5260, type: WidthType.DXA }, shading: isAlt ? { fill: colors.tableBg, type: ShadingType.CLEAR } : undefined, children: [new Paragraph({ spacing: { after: 80 }, children: [new TextRun({ text: ticket[2], size: 20 })] })] })
      ]
    }));
  });

  return new Table({
    columnWidths: [1300, 2800, 5260],
    margins: { top: 100, bottom: 100, left: 150, right: 150 },
    rows: rows
  });
}

function createTimelineTable() {
  const data = [
    ["Phase 1: Self-Improvement", "2 weeks", "7", "None (foundation)"],
    ["Phase 2: Domain Expansion", "3 weeks", "15", "Phase 1 SI-001, SI-007"],
    ["Phase 3: Conversation", "2 weeks", "5", "Phase 2 domains"],
    ["Phase 4: Intelligence Demo", "1 week", "5", "Phases 1-3 complete"],
    ["Phase 5: Testing (ongoing)", "Continuous", "5", "Parallel with all phases"],
    ["TOTAL", "8 weeks", "37", ""]
  ];

  const rows = [
    new TableRow({
      tableHeader: true,
      children: [
        new TableCell({ borders: cellBorders, width: { size: 2800, type: WidthType.DXA }, shading: { fill: colors.headerBg, type: ShadingType.CLEAR }, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Phase", bold: true, color: "FFFFFF", size: 20 })] })] }),
        new TableCell({ borders: cellBorders, width: { size: 2000, type: WidthType.DXA }, shading: { fill: colors.headerBg, type: ShadingType.CLEAR }, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Duration", bold: true, color: "FFFFFF", size: 20 })] })] }),
        new TableCell({ borders: cellBorders, width: { size: 1800, type: WidthType.DXA }, shading: { fill: colors.headerBg, type: ShadingType.CLEAR }, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Tickets", bold: true, color: "FFFFFF", size: 20 })] })] }),
        new TableCell({ borders: cellBorders, width: { size: 2760, type: WidthType.DXA }, shading: { fill: colors.headerBg, type: ShadingType.CLEAR }, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Dependencies", bold: true, color: "FFFFFF", size: 20 })] })] })
      ]
    })
  ];

  data.forEach((row, i) => {
    const isAlt = i % 2 === 1;
    const isTotal = i === data.length - 1;
    rows.push(new TableRow({
      children: [
        new TableCell({ borders: cellBorders, width: { size: 2800, type: WidthType.DXA }, shading: isTotal ? { fill: colors.headerBg, type: ShadingType.CLEAR } : (isAlt ? { fill: colors.tableBg, type: ShadingType.CLEAR } : undefined), children: [new Paragraph({ children: [new TextRun({ text: row[0], bold: isTotal, color: isTotal ? "FFFFFF" : colors.body, size: 20 })] })] }),
        new TableCell({ borders: cellBorders, width: { size: 2000, type: WidthType.DXA }, shading: isTotal ? { fill: colors.headerBg, type: ShadingType.CLEAR } : (isAlt ? { fill: colors.tableBg, type: ShadingType.CLEAR } : undefined), children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: row[1], bold: isTotal, color: isTotal ? "FFFFFF" : colors.body, size: 20 })] })] }),
        new TableCell({ borders: cellBorders, width: { size: 1800, type: WidthType.DXA }, shading: isTotal ? { fill: colors.headerBg, type: ShadingType.CLEAR } : (isAlt ? { fill: colors.tableBg, type: ShadingType.CLEAR } : undefined), children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: row[2], bold: isTotal, color: isTotal ? "FFFFFF" : colors.body, size: 20 })] })] }),
        new TableCell({ borders: cellBorders, width: { size: 2760, type: WidthType.DXA }, shading: isTotal ? { fill: colors.headerBg, type: ShadingType.CLEAR } : (isAlt ? { fill: colors.tableBg, type: ShadingType.CLEAR } : undefined), children: [new Paragraph({ children: [new TextRun({ text: row[3], color: isTotal ? "FFFFFF" : colors.body, size: 20 })] })] })
      ]
    }));
  });

  return new Table({
    columnWidths: [2800, 2000, 1800, 2760],
    margins: { top: 100, bottom: 100, left: 150, right: 150 },
    rows: rows
  });
}

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync('/home/z/my-project/download/RPA_Implementation_Plan_v2.docx', buffer);
  console.log('Document created: /home/z/my-project/download/RPA_Implementation_Plan_v2.docx');
});
