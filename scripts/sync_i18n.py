import os
import sys
import json
import subprocess
import argparse

def extract_keys_by_namespace(src_dir):
    import re
    import os
    
    IGNORE_KEYS = {
        '2d', 'react-markdown', 'token', 'utf-8', 'application/json',
        'POST', 'GET', 'PUT', 'DELETE', 'PATCH', 'Content-Type', 'Accept'
    }

    # Patterns for key extraction - revised to be more flexible (allow spaces, multiple args)
    patterns = [
        # t('key', ...) or t('key')
        r'\bt\(\s*[\'"`]\s*([a-zA-Z0-9_.-]+)\s*[\'"`]',
        # i18nKey="key"
        r'\bi18nKey\s*=\s*[\'"`]\s*([a-zA-Z0-9_.-]+)\s*[\'"`]',
        # i18nKey={'key'} or i18nKey={{'key'}}
        r'\bi18nKey\s*=\s*{\s*{?\s*[\'"`]\s*([a-zA-Z0-9_.-]+)\s*[\'"`]\s*}?\s*}',
        # someKey: "key"
        r'\b\w*[kK]ey\s*:\s*[\'"`]\s*([a-zA-Z0-9_.-]+)\s*[\'"`]'
    ]
    compiled_patterns = [re.compile(p) for p in patterns]
    
    # Pattern to find useTranslation namespace
    ns_pattern = re.compile(r'useTranslation\([\'"`]([a-zA-Z0-9_.-]+)[\'"`]\)')
    # Pattern to find explicit namespace hint: // i18n-namespace: name
    ns_hint_pattern = re.compile(r'i18n-namespace:\s*([a-zA-Z0-9_.-]+)')

    ns_map = {} # {namespace: set(keys)}
    
    # Walk through the source directory
    for root, _, files in os.walk(src_dir):
        for file in files:
            if not file.endswith(('.tsx', '.ts', '.jsx', '.js')):
                continue
                
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Determine namespace for this file
                    ns_match = ns_pattern.search(content) or ns_hint_pattern.search(content)
                    file_ns = ns_match.group(1) if ns_match else 'translation'
                    
                    if file_ns not in ns_map:
                        ns_map[file_ns] = set()
                        
                    # Extract keys
                    for p in compiled_patterns:
                        for match in p.finditer(content):
                            key = match.group(1)
                            if ':' in key:
                                # Explicit namespace
                                explicit_ns, actual_key = key.split(':', 1)
                                if explicit_ns not in ns_map:
                                    ns_map[explicit_ns] = set()
                                ns_map[explicit_ns].add(actual_key)
                            elif key not in IGNORE_KEYS:
                                # Inherited namespace
                                ns_map[file_ns].add(key)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                
    # Convert sets to sorted lists
    return {ns: sorted(list(keys)) for ns, keys in ns_map.items()}

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
        return []

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

def main():
    parser = argparse.ArgumentParser(description="Analyze and sync i18n translation keys based on source code usage.")
    parser.add_argument('--src', required=True, help="Path to the React source directory")
    parser.add_argument('--locales', required=True, help="Path to the locales directory")
    parser.add_argument('--sync', action='store_true', help="Apply synchronization")
    parser.add_argument('--langs', default='en,it,fr,de', help="Languages to process")
    parser.add_argument('--preserve', default='', help="Extra key prefixes to preserve manually")
    
    args = parser.parse_args()
    langs = [l.strip() for l in args.langs.split(',') if l.strip()]
    preserves = [p.strip() for p in args.preserve.split(',') if p.strip()]
    
    print(f"Analyzing source files in '{args.src}' for i18n usage...")
    ns_keys = extract_keys_by_namespace(args.src)
    
    dynamic_prefixes = extract_dynamic_prefixes_from_source(args.src)
    if dynamic_prefixes:
        print(f"Found dynamic prefixes: {', '.join(dynamic_prefixes)}")
        preserves.extend(dynamic_prefixes)
    
    # Discover namespaces from locales folder
    available_namespaces = set()
    for root, _, files in os.walk(os.path.join(args.locales, 'en')):
        for f in files:
            if f.endswith('.json'):
                available_namespaces.add(f.replace('.json', ''))
    
    print(f"Available namespaces in locales: {', '.join(available_namespaces)}")
    
    print("\n================== KEY COMPARISON REPORT ==================")
    
    # Multi-namespace data storage: {lang: {namespace: data}}
    all_locale_data = {lang: {} for lang in langs}
    
    for ns in sorted(available_namespaces):
        print(f"\n>>>> NAMESPACE: {ns} <<<<")
        
        # Load data for this namespace
        ns_data = {}
        for lang in langs:
            file_path = os.path.join(args.locales, lang, f'{ns}.json')
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    ns_data[lang] = json.load(f)
            else:
                ns_data[lang] = {}
            all_locale_data[lang][ns] = ns_data[lang]
            
        used_keys = ns_keys.get(ns, [])
        en_flat = flatten_dict(ns_data.get('en', {}))
        preserved_keys = [k for k in en_flat.keys() if any(k.startswith(p) for p in preserves)]
        
        used_set = set(used_keys).union(set(preserved_keys))
        
        print(f"Total Unique Keys Found in Code for '{ns}': {len(used_keys)}")
        print(f"Total Preserved Dynamic Keys for '{ns}': {len(preserved_keys)}")
        
        for lang in langs:
            flat = flatten_dict(ns_data[lang])
            defined_keys = set(flat.keys())
            
            missing = sorted(used_set - defined_keys)
            unused = sorted(defined_keys - used_set)
            
            print(f"--- Locale {lang.upper()}: Missing: {len(missing)}, Unused: {len(unused)}")
            if missing[:5]:
                print(f"    Missing examples: {', '.join(missing[:5])}")
            if unused:
                print(f"    Unused examples: {', '.join(unused[:20])}")
                if len(unused) > 20:
                    print(f"    ... and {len(unused) - 20} more unused keys.")

        if args.sync:
            print(f"Syncing '{ns}.json'...")
            for lang in langs:
                new_data = {}
                for k in used_set:
                    val = get_nested(ns_data[lang], k)
                    if not val and lang != 'en' and 'en' in ns_data:
                        val = get_nested(ns_data['en'], k)
                    if not val:
                        val = k.split('.')[-1]
                    set_nested(new_data, k, val)
                
                file_path = os.path.join(args.locales, lang, f'{ns}.json')
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(new_data, f, indent=4, ensure_ascii=False)
                    f.write('\n')

    if not args.sync:
        print("\nRun with --sync to automatically strip unused keys and add missing ones.")

if __name__ == '__main__':
    main()
