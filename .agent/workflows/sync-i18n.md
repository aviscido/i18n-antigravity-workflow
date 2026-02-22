description: Check and synchronize i18n translation keys across the frontend project
---

When the user asks you to check or sync translations, or use the `/sync-i18n` command, follow these steps:

0. **Inform the user about deeply nested dynamic keys (not more than 1 level supported)**
   In case users have more than 1 level (namespace.{dynamicKey} vs namespace.{dynamicKey}.{subKey}) then need to use the `--preseve` flag.
   Eventually offer the user to perform a scan and identify such cases. Also translation use of i18n should happen via t(), other forms are unsupported, eg. translations()

1. **Ask for target directories (Optional if clear from context)**:
   Determine the target `src` directory containing the application code and the target `locales` directory containing the `translation.json` files. If this is not provided by the user and is not obvious in the workspace, you should ask.

2. **Run the analysis script (Dry Run)**:
   Using the `run_command` tool, execute the analysis script to see what keys are missing or unused. Do not pass the `--sync` flag yet.
   Example:
   `python3 scripts/sync_i18n.py --src path/to/src --locales path/to/locales`

3. **Report the findings**:
   If the script reports missing or unused keys, tell the user the numbers of missing and unused keys, and provide a clear example of the output. 
   
   *Example Report Format*:
   "I have analyzed the translations. 
   The source code uses **609 unique keys** statically and **46 dynamic prefixes**.
   
   Here is the summary of discrepancies:
   - **`en` locale:** 21 missing keys, 149 unused keys.
   - **`it` locale:** 32 missing keys, 145 unused keys.
   
   *Examples of missing keys in `en`:*
   - `auth.security_alert`
   - `auth.noEmailError`
   
   Would you like me to synchronize these files now?"

4. **Run Synchronization**:
   If the user approves, or if they explicitly asked for synchronization originally with `/sync-i18n`, run the script with the `--sync` flag.
   Example:
   `python3 scripts/sync_i18n.py --src path/to/src --locales path/to/locales --sync`

5. **Verify the Build**:
   Navigate to the respective frontend directory and run `npm run build` to ensure the new consolidated translation files do not break the build.
