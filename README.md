# Antigravity i18n Synchronization Workflow

An automated, AI-first workflow and Python script repository designed to flawlessly synchronize `react-i18next` localized JSON files in dynamic front-end codebases.

## What is this?
When managing huge React projects over time, it's very easy to accumulate "dead" or unused translation keys, or conversely forget to add new `t('some.key')` strings to your secondary locale JSON files (Italian, French, German, etc.). 

This repository provides:
1. **`sync_i18n.py`**: A highly optimized, static, and dynamic AST-less regex parser that cross-references your NextJS/React source code against your JSON locales.
2. **Agent Workflows (`.agent/workflows`)**: A markdown workflow file designed specifically to teach Agentic LLMs (like Google's Antigravity or Cursor) how to parse, analyze, and automate the synchronization of your translations over chat interfaces.

## Features
- **Strict Tree Flattening**: Identifies missing and completely dead keys by flattening their dictionaries.
- **Automated Fallbacks**: When it injects missing keys into your secondary locales, it safely falls back to the English variant or the raw Key string to prevent UI crashing.
- **Dynamic Template Literal Support**: React relies heavily on `t(\`status.${statusKey}\`)`. The Python script automatically scans your source code for template literals and preserves their parent dictionary objects dynamically without manual configuration.

## Limitations
The template literal parsing is currently limited to single variables. 
Double-nested variables `t(\`namespace.${firstKey}.${secondKey}\`)` are **unsupported** by the automatic extraction. If you use deeply nested string interpolation, you will need to manually bypass the purge using the `--preserve` flag (e.g., `--preserve "namespace.key."`).
Also it only supports t() format, if you're using translations() or any other form, the script will not work.

## How to use

### Manually via CLI
Run the analysis by passing your React `src` and the folder containing your `translation.json` files.
```bash
# Dry run analysis
python3 scripts/sync_i18n.py --src frontend/src --locales frontend/src/locales

# Apply the rewrite
python3 scripts/sync_i18n.py --src frontend/src --locales frontend/src/locales --sync
```

### Via AI Agent
Copy the `.agent/workflows/sync-i18n.md` into your own project's `.agent/workflows/` or `.cursor/rules/` directory.

Then simply ask your AI Assistant:
> "/sync-i18n checkout my translations"

The agent will automatically run the Python script, analyze the keys, report the exact missing data count, and then execute the `--sync` parameter to inject and purge the translation files directly in your workspace.

## Contributing
Feel free to open PRs to support deeper AST parsing or expand language support!
