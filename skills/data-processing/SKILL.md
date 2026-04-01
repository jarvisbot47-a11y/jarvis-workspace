---
name: data-processing
description: File and data processing workflow for CSVs, spreadsheets, JSON, and documents. Use when Mystik needs to process files, parse data, convert formats, extract info from documents, or automate spreadsheet tasks. Triggers on: "process this file", "parse the CSV", "extract from spreadsheet", "convert this document", "analyze this data", "import this".
---

# Data Processing Workflow

## Core Principle
Always spawn a SUBAGENT for file/data processing tasks. Your only job: delegate, monitor, synthesize.

## Workflow

### 1. Identify
- What type of file? (CSV, JSON, XLSX, PDF, DOCX, etc.)
- What's the input? (file path or upload)
- What's the desired output? (processed data, new format, extracted info, summary)

### 2. Spawn Processing Subagent
```bash
sessions_spawn task:"<task>" runtime:"subagent" sandbox:"require" runTimeoutSeconds:300
```
Include:
- Exact file location or path
- Specific processing needed
- Output format/destination
- Any formulas, filters, or transformations

### 3. Monitor
- Poll via `process action=poll sessionId:<id> timeout:30000`
- For large files, give more time (600s)

### 4. Deliver
- Save output to workspace
- Report results
- Confirm output location

## Tool Stack
- **exec**: Run Python for CSV/JSON processing
- **LibreOffice**: Document conversion (see TOOLS.md for path)
- **image**: Extract data from images/screenshots
