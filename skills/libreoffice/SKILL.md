---
name: libreoffice
description: "LibreOffice document manipulation. Use when user wants to create, edit, convert, or work with documents, spreadsheets, presentations, or PDFs. Supports .odt, .docx, .ods, .xlsx, .odp, .pptx, .pdf, .csv formats."
---

# LibreOffice Skill

This skill provides document creation, editing, and conversion using LibreOffice.

## Installation

LibreOffice is already installed at `/usr/bin/libreoffice` (version 7.3.7.2).

## Capabilities

- **Writer** - Documents (.odt, .docx, .doc)
- **Calc** - Spreadsheets (.ods, .xlsx, .csv)
- **Impress** - Presentations (.odp, .pptx)
- **Draw** - Graphics (.odg)
- **Export** - Convert to PDF

## Commands

### Convert Document to PDF
```bash
libreoffice --headless --convert-to pdf input.docx --outdir /output/path/
```

### Convert Between Formats
```bash
# DOCX to ODT
libreoffice --headless --convert-to odt file.docx

# CSV to XLSX
libreoffice --headless --convert-to xlsx file.csv

# ODP to PPTX
libreoffice --headless --convert-to pptx file.odp
```

### Create New Document
```bash
# New writer document
libreoffice --writer new-document.odt

# New spreadsheet
libreoffice --calc new-spreadsheet.ods
```

### Batch Convert
```bash
# Convert all docx in folder to pdf
for f in *.docx; do libreoffice --headless --convert-to pdf "$f"; done
```

## Script Usage

```bash
# Convert file
./scripts/libreoffice.sh convert input.docx output.pdf

# Create document
./scripts/libreoffice.sh create writer document.odt
```

## Common Formats

| Format | Extension | LibreOffice App |
|--------|-----------|-----------------|
| Document | .odt, .docx, .doc | Writer |
| Spreadsheet | .ods, .xlsx, .csv | Calc |
| Presentation | .odp, .pptx | Impress |
| PDF | .pdf | Export |
| Graphics | .odg | Draw |