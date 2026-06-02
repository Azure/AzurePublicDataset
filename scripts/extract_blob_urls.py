#!/usr/bin/env python3
"""
Extract blob storage URLs from a markdown file and write them to a .txt link file.

Usage:
    python3 scripts/extract_blob_urls.py <markdown_file> [output_file]

If output_file is omitted, it is derived from the markdown filename:
    AzureLLMInferenceDataset2024.md  ->  AzureLLMInferenceDataset2024Links.txt

Example:
    python3 scripts/extract_blob_urls.py AzureLLMInferenceDataset2024.md
    python3 scripts/extract_blob_urls.py AzureLMMInferenceDataset2025.md AzureLMMInferenceDataset2025Links.txt
"""

import re
import sys
from pathlib import Path

BLOB_PATTERN = re.compile(r'https://[a-z0-9]+\.blob\.core\.windows\.net/[^\s\"\'\)\]]+')


def extract_urls(md_path: Path) -> list[str]:
    text = md_path.read_text(encoding="utf-8")
    urls = BLOB_PATTERN.findall(text)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for url in urls:
        url = url.rstrip(".,;)")   # strip accidental trailing punctuation
        if url not in seen:
            seen.add(url)
            unique.append(url)
    return unique


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    md_path = Path(sys.argv[1])
    if not md_path.exists():
        print(f"Error: {md_path} not found", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) >= 3:
        out_path = Path(sys.argv[2])
    else:
        out_path = md_path.with_name(md_path.stem + "Links.txt")

    urls = extract_urls(md_path)
    if not urls:
        print(f"No blob URLs found in {md_path}")
        sys.exit(0)

    out_path.write_text("\n".join(urls) + "\n", encoding="utf-8")
    print(f"Wrote {len(urls)} URL(s) to {out_path}")


if __name__ == "__main__":
    main()
