import os
import sys

import yaml


def get_keys(data, prefix=""):
    """Recursively get all keys from a dictionary."""
    keys = set()
    for k, v in data.items():
        full_key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            keys.update(get_keys(v, full_key))
        else:
            keys.add(full_key)
    return keys


def main():
    # Tools are expected to be run from project root
    base_dir = os.path.join("resources", "translations")
    base_lang_file = os.path.join(base_dir, "en-US.yaml")

    if not os.path.exists(base_lang_file):
        print(f"Error: Base language file {base_lang_file} not found.")
        sys.exit(1)

    with open(base_lang_file, encoding="utf-8") as f:
        base_data = yaml.safe_load(f) or {}

    base_keys = get_keys(base_data)
    all_files = [f for f in os.listdir(base_dir) if f.endswith(".yaml") and f != "en-US.yaml"]

    errors_found = False

    print(f"Checking {len(all_files)} translation files against {base_lang_file} ({len(base_keys)} keys)...")

    for filename in all_files:
        filepath = os.path.join(base_dir, filename)
        with open(filepath, encoding="utf-8") as f:
            lang_data = yaml.safe_load(f) or {}

        lang_keys = get_keys(lang_data)

        missing = base_keys - lang_keys
        extra = lang_keys - base_keys

        if missing or extra:
            print(f"\n--- Results for {filename} ---")
            if missing:
                errors_found = True
                print(f"  [X] Missing keys ({len(missing)}):")
                for k in sorted(missing):
                    print(f"      - {k}")

            if extra:
                print(f"  [!] Extra/Stale keys ({len(extra)}):")
                for k in sorted(extra):
                    print(f"      - {k}")
        else:
            print(f"  [OK] {filename}")

    if errors_found:
        print("\nConclusion: Missing translation keys detected!")
        sys.exit(1)
    else:
        print("\nConclusion: All translation files are up to date.")
        sys.exit(0)


if __name__ == "__main__":
    main()
