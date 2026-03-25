const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, Header, Footer, 
        AlignmentType, HeadingLevel, BorderStyle, WidthType, PageNumber, PageBreak,
        TableOfContents, LevelFormat, ShadingType, VerticalAlign } = require('docx');
const fs = require('fs');

// Color scheme - Midnight Code (tech/AI focused)
const colors = {
  primary: "#020617",
  body: "#1E293B",
  secondary: "#64748B",
  accent: "#94A3B8",
  tableBg: "#F8FAFC",
  tableHeader: "#E2E8F0"
};

// Table border style
const tableBorder = { style: BorderStyle.SINGLE, size: 12, color: colors.secondary };
const cellBorders = { top: tableBorder, bottom: tableBorder, left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE } };
const allBorders = { top: tableBorder, bottom: tableBorder, left: tableBorder, right: tableBorder };

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Times New Roman", size: 22 } } },
    paragraphStyles: [
      { id: "Title", name: "Title", basedOn: "Normal",
        run: { size: 56, bold: true, color: colors.primary, font: "Times New Roman" },
        paragraph: { spacing: { before: 0, after: 200 }, alignment: AlignmentType.CENTER } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, color: colors.primary, font: "Times New Roman" },
        paragraph: { spacing: { before: 400, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, color: colors.primary, font: "Times New Roman" },
        paragraph: { spacing: { before: 300, after: 150 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, color: colors.secondary, font: "Times New Roman" },
        paragraph: { spacing: { before: 200, after: 100 }, outlineLevel: 2 } }
    ]
  },
  numbering: {
    config: [
      { reference: "bullet-list",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
      { reference: "numbered-1",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }
    ]
  },
  sections: [
    // Cover Page
    {
      properties: { page: { margin: { top: 0, right: 0, bottom: 0, left: 0 } } },
      children: [
        new Paragraph({ spacing: { before: 4000 }, children: [] }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 200 },
          children: [new TextRun({ text: "RESEARCH PROJECT RECAP", size: 28, color: colors.secondary, font: "Times New Roman" })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 400 },
          children: [new TextRun({ text: "RPA: Recursive Pattern Agent", size: 64, bold: true, color: colors.primary, font: "Times New Roman" })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 200 },
          children: [new TextRun({ text: "A Self-Improving AI Learning System", size: 32, color: colors.body, font: "Times New Roman" })]
        }),
        new Paragraph({ spacing: { before: 2000 }, children: [] }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "Multi-Interface Architecture with Web UI, Terminal UI, and REST API", size: 24, color: colors.secondary, font: "Times New Roman" })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 100 },
          children: [new TextRun({ text: "GitHub Actions Integration for Automated Learning Workflows", size: 24, color: colors.secondary, font: "Times New Roman" })]
        }),
        new Paragraph({ spacing: { before: 3000 }, children: [] }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "Version 1.0.0 | March 2026", size: 22, color: colors.secondary, font: "Times New Roman" })]
        }),
        new Paragraph({ children: [new PageBreak()] })
      ]
    },
    // Main Content
    {
      properties: { page: { margin: { top: 1800, right: 1440, bottom: 1440, left: 1440 } } },
      headers: {
        default: new Header({ children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: "RPA: Recursive Pattern Agent - Research Recap", size: 20, color: colors.secondary, italics: true, font: "Times New Roman" })]
        })] })
      },
      footers: {
        default: new Footer({ children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "Page ", size: 20, font: "Times New Roman" }), new TextRun({ children: [PageNumber.CURRENT], size: 20, font: "Times New Roman" }), new TextRun({ text: " of ", size: 20, font: "Times New Roman" }), new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 20, font: "Times New Roman" })]
        })] })
      },
      children: [
        // TOC
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("Table of Contents")] }),
        new TableOfContents("Table of Contents", { hyperlink: true, headingStyleRange: "1-3" }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { before: 100, after: 200 },
          children: [new TextRun({ text: "Note: Right-click the Table of Contents and select \"Update Field\" to refresh page numbers.", size: 18, color: "999999", italics: true, font: "Times New Roman" })]
        }),
        new Paragraph({ children: [new PageBreak()] }),

        // Executive Summary
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("1. Executive Summary")] }),
        new Paragraph({
          spacing: { after: 150, line: 312 },
          children: [new TextRun({ text: "The Recursive Pattern Agent (RPA) is a self-improving AI learning system designed to acquire, consolidate, and evolve knowledge through recursive inquiry and closed-loop feedback. This research project has developed a complete multi-interface architecture supporting web-based, terminal-based, and programmatic access to the learning system.", font: "Times New Roman", size: 22 })]
        }),
        new Paragraph({
          spacing: { after: 150, line: 312 },
          children: [new TextRun({ text: "The system implements spaced repetition algorithms (SM-2) for vocabulary learning, supports multiple learning domains including English language and Python programming, and features a comprehensive role-based access control system. The project has achieved significant milestones in creating a unified learning platform that maintains consistent user experiences across all interface modalities.", font: "Times New Roman", size: 22 })]
        }),
        new Paragraph({
          spacing: { after: 150, line: 312 },
          children: [new TextRun({ text: "The architecture demonstrates production-ready capabilities including JWT authentication, real-time session management, automated testing pipelines, and GitHub Actions integration for scheduled learning jobs. With 697 passing tests and 50+ API endpoints, the system provides a robust foundation for continued research and development.", font: "Times New Roman", size: 22 })]
        }),

        // Project Overview
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("2. Project Overview")] }),
        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("2.1 Project Vision")] }),
        new Paragraph({
          spacing: { after: 150, line: 312 },
          children: [new TextRun({ text: "The RPA project aims to create an intelligent learning system that can autonomously improve its knowledge acquisition capabilities. The system is built on principles of recursive pattern recognition, where learning patterns are identified, consolidated, and evolved through continuous feedback loops. This approach enables the system to adapt its teaching strategies based on learner performance and knowledge gaps.", font: "Times New Roman", size: 22 })]
        }),
        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("2.2 Core Capabilities")] }),
        new Paragraph({
          spacing: { after: 100, line: 312 },
          children: [new TextRun({ text: "The RPA system provides the following core capabilities:", font: "Times New Roman", size: 22 })]
        }),
        new Paragraph({ numbering: { reference: "numbered-1", level: 0 }, spacing: { line: 312 }, children: [new TextRun({ text: "Multi-Domain Learning: Support for English vocabulary, grammar, reading comprehension, writing assessment, and Python programming concepts", font: "Times New Roman", size: 22 })] }),
        new Paragraph({ numbering: { reference: "numbered-1", level: 0 }, spacing: { line: 312 }, children: [new TextRun({ text: "Spaced Repetition: Implementation of the SM-2 algorithm for optimal memory retention scheduling", font: "Times New Roman", size: 22 })] }),
        new Paragraph({ numbering: { reference: "numbered-1", level: 0 }, spacing: { line: 312 }, children: [new TextRun({ text: "Multi-Interface Access: Unified experience across Web UI (Next.js), Terminal UI (Textual), and REST API", font: "Times New Roman", size: 22 })] }),
        new Paragraph({ numbering: { reference: "numbered-1", level: 0 }, spacing: { line: 312 }, children: [new TextRun({ text: "Role-Based Access Control: Four-tier permission system (Superadmin, Admin, User, Guest)", font: "Times New Roman", size: 22 })] }),
        new Paragraph({ numbering: { reference: "numbered-1", level: 0 }, spacing: { line: 312 }, children: [new TextRun({ text: "Automated Learning Jobs: GitHub Actions integration for scheduled vocabulary reviews and reports", font: "Times New Roman", size: 22 })] }),
        new Paragraph({ numbering: { reference: "numbered-1", level: 0 }, spacing: { line: 312 }, children: [new TextRun({ text: "Real-Time Progress Tracking: Session management, streak tracking, and learning analytics", font: "Times New Roman", size: 22 })] }),

        // Architecture
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("3. System Architecture")] }),
        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("3.1 High-Level Architecture")] }),
        new Paragraph({
          spacing: { after: 150, line: 312 },
          children: [new TextRun({ text: "The RPA system follows a layered architecture pattern with clear separation between interface, business logic, and data layers. The architecture supports multiple client interfaces that communicate with a unified backend API, ensuring consistent behavior and data integrity across all access modalities.", font: "Times New Roman", size: 22 })]
        }),
        
        // Architecture Table
        new Table({
          columnWidths: [2340, 7020],
          margins: { top: 100, bottom: 100, left: 150, right: 150 },
          rows: [
            new TableRow({
              tableHeader: true,
              children: [
                new TableCell({ borders: allBorders, width: { size: 2340, type: WidthType.DXA }, shading: { fill: colors.tableHeader, type: ShadingType.CLEAR }, verticalAlign: VerticalAlign.CENTER, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Layer", bold: true, size: 22, font: "Times New Roman" })] })] }),
                new TableCell({ borders: allBorders, width: { size: 7020, type: WidthType.DXA }, shading: { fill: colors.tableHeader, type: ShadingType.CLEAR }, verticalAlign: VerticalAlign.CENTER, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Components", bold: true, size: 22, font: "Times New Roman" })] })] })
              ]
            }),
            new TableRow({ children: [
              new TableCell({ borders: cellBorders, width: { size: 2340, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Interface", size: 22, font: "Times New Roman" })] })] }),
              new TableCell({ borders: cellBorders, width: { size: 7020, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: "Web UI (Next.js 16), Terminal UI (Textual), REST API Clients", size: 22, font: "Times New Roman" })] })] })
            ]}),
            new TableRow({ children: [
              new TableCell({ borders: cellBorders, width: { size: 2340, type: WidthType.DXA }, shading: { fill: colors.tableBg, type: ShadingType.CLEAR }, verticalAlign: VerticalAlign.CENTER, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "API Gateway", size: 22, font: "Times New Roman" })] })] }),
              new TableCell({ borders: cellBorders, width: { size: 7020, type: WidthType.DXA }, shading: { fill: colors.tableBg, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "FastAPI Server with JWT Authentication, CORS, Rate Limiting", size: 22, font: "Times New Roman" })] })] })
            ]}),
            new TableRow({ children: [
              new TableCell({ borders: cellBorders, width: { size: 2340, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Business Logic", size: 22, font: "Times New Roman" })] })] }),
              new TableCell({ borders: cellBorders, width: { size: 7020, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: "VocabularyTrainer, GrammarEngine, Multi-Agent System, Assessment Engine", size: 22, font: "Times New Roman" })] })] })
            ]}),
            new TableRow({ children: [
              new TableCell({ borders: cellBorders, width: { size: 2340, type: WidthType.DXA }, shading: { fill: colors.tableBg, type: ShadingType.CLEAR }, verticalAlign: VerticalAlign.CENTER, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Memory Systems", size: 22, font: "Times New Roman" })] })] }),
              new TableCell({ borders: cellBorders, width: { size: 7020, type: WidthType.DXA }, shading: { fill: colors.tableBg, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "STM (Short-Term Memory), LTM (Long-Term Memory), Episodic Memory", size: 22, font: "Times New Roman" })] })] })
            ]}),
            new TableRow({ children: [
              new TableCell({ borders: cellBorders, width: { size: 2340, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Automation", size: 22, font: "Times New Roman" })] })] }),
              new TableCell({ borders: cellBorders, width: { size: 7020, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: "GitHub Actions Workflows, Webhook Handlers, Workflow Manager", size: 22, font: "Times New Roman" })] })] })
            ]})
          ]
        }),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 100, after: 200 }, children: [new TextRun({ text: "Table 1: System Architecture Layers", size: 20, italics: true, color: colors.secondary, font: "Times New Roman" })] }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("3.2 Technology Stack")] }),
        new Paragraph({
          spacing: { after: 150, line: 312 },
          children: [new TextRun({ text: "The project utilizes modern, production-ready technologies selected for reliability, performance, and developer experience. The backend is implemented in Python with FastAPI, while the web frontend uses Next.js 16 with TypeScript. The terminal interface leverages the Textual framework for rich console applications.", font: "Times New Roman", size: 22 })]
        }),

        // Tech Stack Table
        new Table({
          columnWidths: [2340, 3510, 3510],
          margins: { top: 100, bottom: 100, left: 150, right: 150 },
          rows: [
            new TableRow({
              tableHeader: true,
              children: [
                new TableCell({ borders: allBorders, width: { size: 2340, type: WidthType.DXA }, shading: { fill: colors.tableHeader, type: ShadingType.CLEAR }, verticalAlign: VerticalAlign.CENTER, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Category", bold: true, size: 22, font: "Times New Roman" })] })] }),
                new TableCell({ borders: allBorders, width: { size: 3510, type: WidthType.DXA }, shading: { fill: colors.tableHeader, type: ShadingType.CLEAR }, verticalAlign: VerticalAlign.CENTER, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Technology", bold: true, size: 22, font: "Times New Roman" })] })] }),
                new TableCell({ borders: allBorders, width: { size: 3510, type: WidthType.DXA }, shading: { fill: colors.tableHeader, type: ShadingType.CLEAR }, verticalAlign: VerticalAlign.CENTER, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Version", bold: true, size: 22, font: "Times New Roman" })] })] })
              ]
            }),
            new TableRow({ children: [
              new TableCell({ borders: cellBorders, width: { size: 2340, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Backend Framework", size: 22, font: "Times New Roman" })] })] }),
              new TableCell({ borders: cellBorders, width: { size: 3510, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: "FastAPI", size: 22, font: "Times New Roman" })] })] }),
              new TableCell({ borders: cellBorders, width: { size: 3510, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: "Latest", size: 22, font: "Times New Roman" })] })] })
            ]}),
            new TableRow({ children: [
              new TableCell({ borders: cellBorders, width: { size: 2340, type: WidthType.DXA }, shading: { fill: colors.tableBg, type: ShadingType.CLEAR }, verticalAlign: VerticalAlign.CENTER, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Web Frontend", size: 22, font: "Times New Roman" })] })] }),
              new TableCell({ borders: cellBorders, width: { size: 3510, type: WidthType.DXA }, shading: { fill: colors.tableBg, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "Next.js + TypeScript", size: 22, font: "Times New Roman" })] })] }),
              new TableCell({ borders: cellBorders, width: { size: 3510, type: WidthType.DXA }, shading: { fill: colors.tableBg, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "16.1 / 5.x", size: 22, font: "Times New Roman" })] })] })
            ]}),
            new TableRow({ children: [
              new TableCell({ borders: cellBorders, width: { size: 2340, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Terminal UI", size: 22, font: "Times New Roman" })] })] }),
              new TableCell({ borders: cellBorders, width: { size: 3510, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: "Textual (Python)", size: 22, font: "Times New Roman" })] })] }),
              new TableCell({ borders: cellBorders, width: { size: 3510, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: "Latest", size: 22, font: "Times New Roman" })] })] })
            ]}),
            new TableRow({ children: [
              new TableCell({ borders: cellBorders, width: { size: 2340, type: WidthType.DXA }, shading: { fill: colors.tableBg, type: ShadingType.CLEAR }, verticalAlign: VerticalAlign.CENTER, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "UI Components", size: 22, font: "Times New Roman" })] })] }),
              new TableCell({ borders: cellBorders, width: { size: 3510, type: WidthType.DXA }, shading: { fill: colors.tableBg, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "shadcn/ui + Tailwind CSS", size: 22, font: "Times New Roman" })] })] }),
              new TableCell({ borders: cellBorders, width: { size: 3510, type: WidthType.DXA }, shading: { fill: colors.tableBg, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "4.x", size: 22, font: "Times New Roman" })] })] })
            ]}),
            new TableRow({ children: [
              new TableCell({ borders: cellBorders, width: { size: 2340, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "State Management", size: 22, font: "Times New Roman" })] })] }),
              new TableCell({ borders: cellBorders, width: { size: 3510, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: "Zustand", size: 22, font: "Times New Roman" })] })] }),
              new TableCell({ borders: cellBorders, width: { size: 3510, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: "5.x", size: 22, font: "Times New Roman" })] })] })
            ]}),
            new TableRow({ children: [
              new TableCell({ borders: cellBorders, width: { size: 2340, type: WidthType.DXA }, shading: { fill: colors.tableBg, type: ShadingType.CLEAR }, verticalAlign: VerticalAlign.CENTER, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Authentication", size: 22, font: "Times New Roman" })] })] }),
              new TableCell({ borders: cellBorders, width: { size: 3510, type: WidthType.DXA }, shading: { fill: colors.tableBg, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "JWT + PyJWT", size: 22, font: "Times New Roman" })] })] }),
              new TableCell({ borders: cellBorders, width: { size: 3510, type: WidthType.DXA }, shading: { fill: colors.tableBg, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "2.x", size: 22, font: "Times New Roman" })] })] })
            ]})
          ]
        }),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 100, after: 200 }, children: [new TextRun({ text: "Table 2: Core Technology Stack", size: 20, italics: true, color: colors.secondary, font: "Times New Roman" })] }),

        // Development Phases
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("4. Development Phases")] }),
        new Paragraph({
          spacing: { after: 150, line: 312 },
          children: [new TextRun({ text: "The RPA project was developed through eight major phases, each building upon the previous to create a comprehensive learning system. This iterative approach allowed for continuous refinement and validation of the system architecture.", font: "Times New Roman", size: 22 })]
        }),

        // Phase summaries
        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("4.1 Phase 1: Foundation Hardening (75 tests)")] }),
        new Paragraph({ spacing: { after: 150, line: 312 }, children: [new TextRun({ text: "Established core infrastructure: Node, Edge, PatternGraph, Memory systems (STM, LTM, Episodic), Validation pipeline, Self-Assessment framework.", font: "Times New Roman", size: 22 })] }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("4.2 Phase 2: Intelligence Deepening (110 tests)")] }),
        new Paragraph({ spacing: { after: 150, line: 312 }, children: [new TextRun({ text: "Enhanced knowledge gap identification: GapDetector (6 strategies), QuestionGenerator, AnswerIntegrator, CorrectionAnalyzer for feedback loops.", font: "Times New Roman", size: 22 })] }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("4.3 Phase 3: Scaling & Integration (190 tests)")] }),
        new Paragraph({ spacing: { after: 150, line: 312 }, children: [new TextRun({ text: "Enabled real-world data integration: DatasetLoader (Hugging Face), DatasetInterpreter, REST API, WebSocket server, Curriculum files.", font: "Times New Roman", size: 22 })] }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("4.4 Phase 4: Production Hardening (256 tests)")] }),
        new Paragraph({ spacing: { after: 150, line: 312 }, children: [new TextRun({ text: "Added production-critical features: CodeSandbox, ErrorClassifier, ErrorCorrector, AbstractionEngine, KnowledgeIntegrity system.", font: "Times New Roman", size: 22 })] }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("4.5 Phase 5: Multi-Agent System (326 tests)")] }),
        new Paragraph({ spacing: { after: 150, line: 312 }, children: [new TextRun({ text: "Implemented multi-agent architecture: BaseAgent, CodingAgent, LanguageAgent, AgentRegistry, Orchestrator, SharedKnowledge, AgentMessenger.", font: "Times New Roman", size: 22 })] }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("4.6 Phase 6: System Integrity & Safety (405 tests)")] }),
        new Paragraph({ spacing: { after: 150, line: 312 }, children: [new TextRun({ text: "Added safety mechanisms: CurriculumIngestionGate, RecursiveLoopPrevention (DFS, Tarjan's algorithm), PatternValidationFramework (11 rules), SystemHealthMonitor.", font: "Times New Roman", size: 22 })] }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("4.7 Phase 7: English Domain & Intelligence")] }),
        new Paragraph({ spacing: { after: 150, line: 312 }, children: [new TextRun({ text: "Complete English learning domain: VocabularyTrainer (SM-2 algorithm), GrammarEngine, ProficiencyLevel tracking, ReinforcementTracker, OutcomeEvaluator.", font: "Times New Roman", size: 22 })] }),

        new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun("4.8 Phase 8: Multi-Interface Architecture (697 tests)")] }),
        new Paragraph({ spacing: { after: 150, line: 312 }, children: [new TextRun({ text: "Complete multi-interface support: Core API Layer (FastAPI, 70+ models, JWT auth), Terminal UI (Textual), Web UI (Next.js 16, 20+ components), GitHub Actions Integration (CI/CD, scheduled learning jobs, webhooks).", font: "Times New Roman", size: 22 })] }),

        // Key Metrics
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("5. Project Metrics")] }),
        
        new Table({
          columnWidths: [4680, 4680],
          margins: { top: 100, bottom: 100, left: 150, right: 150 },
          rows: [
            new TableRow({
              tableHeader: true,
              children: [
                new TableCell({ borders: allBorders, width: { size: 4680, type: WidthType.DXA }, shading: { fill: colors.tableHeader, type: ShadingType.CLEAR }, verticalAlign: VerticalAlign.CENTER, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Metric", bold: true, size: 22, font: "Times New Roman" })] })] }),
                new TableCell({ borders: allBorders, width: { size: 4680, type: WidthType.DXA }, shading: { fill: colors.tableHeader, type: ShadingType.CLEAR }, verticalAlign: VerticalAlign.CENTER, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Value", bold: true, size: 22, font: "Times New Roman" })] })] })
              ]
            }),
            new TableRow({ children: [
              new TableCell({ borders: cellBorders, width: { size: 4680, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: "Total Tests", size: 22, font: "Times New Roman" })] })] }),
              new TableCell({ borders: cellBorders, width: { size: 4680, type: WidthType.DXA }, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "697 passing", size: 22, font: "Times New Roman" })] })] })
            ]}),
            new TableRow({ children: [
              new TableCell({ borders: cellBorders, width: { size: 4680, type: WidthType.DXA }, shading: { fill: colors.tableBg, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "API Endpoints", size: 22, font: "Times New Roman" })] })] }),
              new TableCell({ borders: cellBorders, width: { size: 4680, type: WidthType.DXA }, shading: { fill: colors.tableBg, type: ShadingType.CLEAR }, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "50+ REST endpoints", size: 22, font: "Times New Roman" })] })] })
            ]}),
            new TableRow({ children: [
              new TableCell({ borders: cellBorders, width: { size: 4680, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: "Pydantic Models", size: 22, font: "Times New Roman" })] })] }),
              new TableCell({ borders: cellBorders, width: { size: 4680, type: WidthType.DXA }, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "70+ data models", size: 22, font: "Times New Roman" })] })] })
            ]}),
            new TableRow({ children: [
              new TableCell({ borders: cellBorders, width: { size: 4680, type: WidthType.DXA }, shading: { fill: colors.tableBg, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "React Components", size: 22, font: "Times New Roman" })] })] }),
              new TableCell({ borders: cellBorders, width: { size: 4680, type: WidthType.DXA }, shading: { fill: colors.tableBg, type: ShadingType.CLEAR }, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "20+ custom components", size: 22, font: "Times New Roman" })] })] })
            ]}),
            new TableRow({ children: [
              new TableCell({ borders: cellBorders, width: { size: 4680, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: "User Roles", size: 22, font: "Times New Roman" })] })] }),
              new TableCell({ borders: cellBorders, width: { size: 4680, type: WidthType.DXA }, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "4 roles (Superadmin, Admin, User, Guest)", size: 22, font: "Times New Roman" })] })] })
            ]}),
            new TableRow({ children: [
              new TableCell({ borders: cellBorders, width: { size: 4680, type: WidthType.DXA }, shading: { fill: colors.tableBg, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "GitHub Workflows", size: 22, font: "Times New Roman" })] })] }),
              new TableCell({ borders: cellBorders, width: { size: 4680, type: WidthType.DXA }, shading: { fill: colors.tableBg, type: ShadingType.CLEAR }, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "2 workflows (CI, Learning Jobs)", size: 22, font: "Times New Roman" })] })] })
            ]}),
            new TableRow({ children: [
              new TableCell({ borders: cellBorders, width: { size: 4680, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: "Development Phases", size: 22, font: "Times New Roman" })] })] }),
              new TableCell({ borders: cellBorders, width: { size: 4680, type: WidthType.DXA }, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "8 major phases completed", size: 22, font: "Times New Roman" })] })] })
            ]}),
            new TableRow({ children: [
              new TableCell({ borders: cellBorders, width: { size: 4680, type: WidthType.DXA }, shading: { fill: colors.tableBg, type: ShadingType.CLEAR }, children: [new Paragraph({ children: [new TextRun({ text: "Learning Domains", size: 22, font: "Times New Roman" })] })] }),
              new TableCell({ borders: cellBorders, width: { size: 4680, type: WidthType.DXA }, shading: { fill: colors.tableBg, type: ShadingType.CLEAR }, children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "English, Python (extensible)", size: 22, font: "Times New Roman" })] })] })
            ]})
          ]
        }),
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 100, after: 200 }, children: [new TextRun({ text: "Table 3: Project Metrics Summary", size: 20, italics: true, color: colors.secondary, font: "Times New Roman" })] }),

        // Conclusion
        new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun("6. Conclusion")] }),
        new Paragraph({
          spacing: { after: 150, line: 312 },
          children: [new TextRun({ text: "The RPA (Recursive Pattern Agent) project has successfully delivered a comprehensive, production-ready AI learning system with multi-interface support. The architecture demonstrates strong separation of concerns, with a unified Core API serving Web UI, Terminal UI, and programmatic clients. The implementation of spaced repetition algorithms, role-based access control, and GitHub Actions automation positions the system for real-world deployment and continuous improvement.", font: "Times New Roman", size: 22 })]
        }),
        new Paragraph({
          spacing: { after: 150, line: 312 },
          children: [new TextRun({ text: "Key achievements include the implementation of a sophisticated memory system architecture, a multi-agent coordination framework, comprehensive safety mechanisms, and a complete learning domain for English vocabulary and grammar. The 697 passing tests provide confidence in system reliability, while the CI/CD pipeline ensures ongoing code quality.", font: "Times New Roman", size: 22 })]
        }),
        new Paragraph({
          spacing: { after: 150, line: 312 },
          children: [new TextRun({ text: "Future development directions include expanding learning domains, enhancing the multi-agent coordination capabilities, and implementing additional spaced repetition algorithms. The modular architecture supports these extensions while maintaining backward compatibility with existing interfaces.", font: "Times New Roman", size: 22 })]
        }),

        // Document Info
        new Paragraph({ spacing: { before: 400 }, children: [] }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 100 },
          children: [new TextRun({ text: "Document Information", size: 24, bold: true, color: colors.primary, font: "Times New Roman" })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "Version: 1.0.0 | Generated: March 22, 2026", size: 20, color: colors.secondary, font: "Times New Roman" })]
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "RPA Research Project - All Rights Reserved", size: 20, color: colors.secondary, font: "Times New Roman" })]
        })
      ]
    }
  ]
});

// Generate document
Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("/home/z/my-project/download/RPA_Research_Recap.docx", buffer);
  console.log("Document created: /home/z/my-project/download/RPA_Research_Recap.docx");
});
