---
description: Check and synchronize i18n translation keys across the frontend project
---

When the user asks you to check or sync translations, or use the `/sync-i18n` command, follow these steps:

0. **Inform the user about deeply nested dynamic keys (not more than 1 level supported)**
   In case users have more than 1 level (namespace.{dynamicKey} vs namespace.{dynamicKey}.{subKey}) then need to use the `--preserve` flag.
   Eventually offer the user to perform a scan and identify such cases. Also translation use of i18n should happen via t(), other forms are unsupported, eg. translations()

1. **Ask for target directories (Optional if clear from context)**:
   Determine the target `src` directory containing the application code and the target `locales` directory containing the `.json` files. 

2. **Discover Namespaces**:
   The script automatically handles multiple namespaces by scanning the `locales` folder for all `.json` files.
   *   **Implicit Discovery**: Source files using `useTranslation('ns')` will have their keys attributed to `ns.json`.
   *   **Explicit Hints**: For data files or components where hooks aren't used, you can add `// i18n-namespace: name` at the top of the file to guide the sync script.
   *   **Explicit Keys**: Keys used as `ns:key` are automatically attributed to the correct namespace.

3. **Run the analysis script (Dry Run)**:
   Using the `run_command` tool, execute the analysis script to see what keys are missing or unused. Do not pass the `--sync` flag yet.
   Example:
   `python3 scripts/sync_i18n.py --src path/to/src --locales path/to/locales`

4. **Report the findings**:
   The script reports missing or unused keys per namespace. Tell the user the summary for each namespace.
   
   *Example Report Format*:
   "I have analyzed the translations. 
   
   **NAMESPACE: translation**
   - **`en` locale:** 0 missing keys, 4 unused keys.
   - **`it` locale:** 0 missing keys, 4 unused keys.
   
   **NAMESPACE: help**
   - **`en` locale:** 0 missing keys, 0 unused keys.
   
   Would you like me to synchronize these files now?"

5. **Run Synchronization**:
   If the user approves, run the script with the `--sync` flag.
   `python3 scripts/sync_i18n.py --src path/to/src --locales path/to/locales --sync`

6. **Verify the Build**:
   Navigate to the respective frontend directory and run `npm run build` to ensure the new consolidated translation files do not break the build.
