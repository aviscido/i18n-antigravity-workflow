# Internationalization (i18n) Synchronization

This document describes how to properly analyze and synchronize the i18n translation dictionaries within front-end React projects.

## Problem Statement
Over time, as developers add, move, or remove React components, the `translation.json` files accumulate "dead" keys that bloat the bundle size. Additionally, newly introduced `t('some.key')` strings might lack entries in fallback languages (e.g., Italian, French, German), causing missing text on the UI.

## The Script
We rely on a consolidated Python script located at `scripts/sync_i18n.py`.
This script statically analyzes the source directories to find every instance of `t('...')` and uses these extracted keys as the single source of truth.
Please notice it only looks for t( ), variations like translations( ) are unsupported !

### What the script does:
1.  **Analysis**: Scans all `ts` and `tsx` files in the provided source directory and constructs a strict set of used keys via static regex.
2.  **Dynamic Key Preservation**: Scans the codebase for template literals (e.g., `t(\`prefix.${variable}\`)`) and automatically extracts and safeguards their prefixes from being culled during synchronization. 
3.  **Comparison**: Flattens the existing JSON translation files and cross-references them with the used keys to generate a report of "missing" and "unused" keys.
4.  **Synchronization (with `--sync`)**: 
    -   Purges any key not found in the codebase.
    -   Injects entirely missing keys.
    -   For missing translations in secondary locales, it gracefully falls back to the primary string, or the key name.
    -   Sorts and formats the resulting JSON structures identically across all languages.

## Limitations
**Multi-level dynamic variables** inside template strings (e.g. `t(\`namespace.${level1}.${level2}\`)`) are currently **unsupported**. The regex parsing is designed to only capture single-prefix variables `t(\`namespace.prefix.${var}\`)`. To preserve deeper dictionary structures, you must manually pass the `--preserve "namespace.prefix."` flag or refactor to single-depth template literals.

## Usage

You can run the script manually from the project root.

### Analyze Only (Dry Run)
Execute the script against your React `src` folder and its `locales` folder to see the dry-run output:
```bash
python3 scripts/sync_i18n.py --src path/to/src --locales path/to/locales
```

### Apply Synchronization
To actually rewrite the JSON files and clean them up, append the `--sync` flag.

```bash
python3 scripts/sync_i18n.py --src path/to/src --locales path/to/locales --sync
```

## Agent Workflows
You can ask your conversational agent (e.g. Gemini/Antigravity/Cursor) to perform this for you using the `.agent/workflows/sync-i18n.md` slash command definition.
