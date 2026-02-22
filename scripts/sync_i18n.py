import os
import sys
import json
import subprocess
import argparse

def extract_keys_from_source(src_dir):
    """Uses grep to extract t('key') and t("key") occurrences from TS/TSX files."""
    cmd = f'grep -rI -oP "(?<=\\Wt\\([\'\\"\\`])[a-zA-Z0-9_.-]+(?=[\'\\"\\`])" {src_dir} | cut -d: -f2 | sort | uniq'
    try:
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        keys = set(line.strip() for line in result.stdout.splitlines() if line.strip())
        return sorted(list(keys))
    except subprocess.CalledProcessError as e:
        if e.returncode == 1: # Grep returns 1 if no matches found
            return []
        print(f"Error extracting keys from {src_dir}: {e.stderr}")
        sys.exit(1)

def extract_dynamic_prefixes_from_source(src_dir):
    """Uses grep to extract prefixes from dynamic t(`prefix.${var}`) occurrences."""
    cmd = f"grep -rI -oP '(?<=\\Wt\\(\\`)[a-zA-Z0-9_.-]+(?=\\$\\{{)' {src_dir} | cut -d: -f2 | sort | uniq"
    try:
        result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        prefixes = set(line.strip() for line in result.stdout.splitlines() if line.strip())
        return sorted(list(prefixes))
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            return []
        print(f"Error extracting dynamic prefixes from {src_dir}: {e.stderr}")
        sys.exit(1)

def get_nested(d, key_path):
    parts = key_path.split('.')
    cur = d
    for p in parts:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return None
    return cur if isinstance(cur, str) else None

def set_nested(d, key_path, value):
    parts = key_path.split('.')
    cur = d
    for p in parts[:-1]:
        if p not in cur or not isinstance(cur[p], dict):
            cur[p] = {}
        cur = cur[p]
    cur[parts[-1]] = value

def flatten_dict(d, parent_key='', sep='.'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def analyze_locales(locales_dir, used_keys, locales, preserve_prefixes=None):
    if preserve_prefixes is None:
        preserve_prefixes = []
        
    data = {}
    for loc in locales:
        file_path = os.path.join(locales_dir, loc, 'translation.json')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                data[loc] = json.load(f)
        else:
            data[loc] = {}
            
    # Include keys from EN that match the preserve prefixes
    en_flat = flatten_dict(data.get('en', {}))
    preserved_keys = [k for k in en_flat.keys() if any(k.startswith(p) for p in preserve_prefixes)]
    used_set = set(used_keys).union(set(preserved_keys))

    print("\n================== KEY COMPARISON REPORT ==================")
    print(f"Total Unique Keys Found in Source Code (Static): {len(used_keys)}")
    print(f"Total Preserved Dynamic Keys: {len(preserved_keys)}")
    
    for loc in locales:
        print(f"\n--- LOCALE: {loc.upper()} ---")
        flat = flatten_dict(data[loc])
        defined_keys = set(flat.keys())
        
        missing_keys = sorted(used_set - defined_keys)
        extra_keys = sorted(defined_keys - used_set)
        
        print(f"Missing Keys (Used in code, missing in {loc}): {len(missing_keys)}")
        if missing_keys:
            for k in missing_keys[:10]:
                print(f"  - {k}")
            if len(missing_keys) > 10: print("  ... and more")
            
        print(f"Unused Keys (In {loc}, not found in code): {len(extra_keys)}")
    return data, used_set

def sync_locales(locales_dir, used_keys, locales, data):
    print("\nSynchronizing locale files by strictly enforcing used keys...")
    for loc in locales:
        new_data = {}
        for k in used_keys:
            val = get_nested(data[loc], k)
            if not val and loc != 'en' and 'en' in data:
                val = get_nested(data['en'], k)
            if not val:
                val = k.split('.')[-1]
            set_nested(new_data, k, val)
            
        file_path = os.path.join(locales_dir, loc, 'translation.json')
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(new_data, f, indent=4, ensure_ascii=False)
            f.write('\n')
    print("Optimization and key synchronization completed.")

def main():
    parser = argparse.ArgumentParser(description="Analyze and sync i18n translation keys based on source code usage.")
    parser.add_argument('--src', required=True, help="Path to the React source directory (e.g., frontend/src)")
    parser.add_argument('--locales', required=True, help="Path to the locales directory (e.g., frontend/src/locales)")
    parser.add_argument('--sync', action='store_true', help="Apply synchronization (remove unused, add missing with fallbacks)")
    parser.add_argument('--langs', default='en,it,fr,de', help="Comma-separated list of languages to process. Default is en,it,fr,de")
    parser.add_argument('--preserve', default='', help="Optional comma-separated list of extra key prefixes to preserve manually.")
    
    args = parser.parse_args()
    
    langs = [l.strip() for l in args.langs.split(',') if l.strip()]
    preserves = [p.strip() for p in args.preserve.split(',') if p.strip()]
    
    print(f"Extracting used tags from '{args.src}'...")
    used_keys = extract_keys_from_source(args.src)
    
    print(f"Extracting dynamic prefixes from '{args.src}'...")
    dynamic_prefixes = extract_dynamic_prefixes_from_source(args.src)
    if dynamic_prefixes:
        print(f"Found dynamic prefixes: {', '.join(dynamic_prefixes)}")
        preserves.extend(dynamic_prefixes)
    
    data, final_used_set = analyze_locales(args.locales, used_keys, langs, preserves)
    
    if args.sync:
        sync_locales(args.locales, final_used_set, langs, data)
    else:
        print("\nRun with --sync to automatically strip unused keys and add missing ones.")

if __name__ == '__main__':
    main()
