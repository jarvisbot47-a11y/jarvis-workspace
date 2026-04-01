#!/bin/bash
# LibreOffice wrapper script for document operations

COMMAND=$1
INPUT=$2
OUTPUT=$3

case "$COMMAND" in
  convert)
    if [ -z "$INPUT" ] || [ -z "$OUTPUT" ]; then
      echo "Usage: $0 convert <input> <output>"
      exit 1
    fi
    libreoffice --headless --convert-to "$OUTPUT" "$INPUT" 2>/dev/null
    echo "Converted $INPUT to $OUTPUT"
    ;;
  pdf)
    if [ -z "$INPUT" ]; then
      echo "Usage: $0 pdf <input>"
      exit 1
    fi
    BASE=$(basename "$INPUT" .${INPUT##*.})
    libreoffice --headless --convert-to pdf "$INPUT" --outdir "$(dirname "$INPUT")" 2>/dev/null
    echo "Converted $INPUT to $BASE.pdf"
    ;;
  create)
    TYPE=$INPUT
    NAME=$OUTPUT
    case "$TYPE" in
      writer)
        libreoffice --headless --writer "$NAME" 2>/dev/null
        ;;
      calc)
        libreoffice --headless --calc "$NAME" 2>/dev/null
        ;;
      impress)
        libreoffice --headless --impress "$NAME" 2>/dev/null
        ;;
      *)
        echo "Unknown type: $TYPE (writer, calc, impress)"
        exit 1
        ;;
    esac
    echo "Created $NAME"
    ;;
  *)
    echo "LibreOffice Wrapper"
    echo "Usage:"
    echo "  $0 convert <input> <output>  - Convert between formats"
    echo "  $0 pdf <input>               - Convert to PDF"
    echo "  $0 create <type> <name>     - Create new document"
    echo ""
    echo "Types: writer, calc, impress"
    ;;
esac