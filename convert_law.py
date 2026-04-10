import os
import re
from pathlib import Path

def clean_text(text: str) -> str:
    """
    Cleans up common artifacts in Vietnamese law text files.
    """
    # Remove HYPERLINK tags: HYPERLINK \l "_ftn1" [1] or similar
    text = re.sub(r'HYPERLINK \\l "_ftn\d+" \[\d+\]', '', text)
    # Remove residual HYPERLINK parts if any
    text = re.sub(r'HYPERLINK \\l "_ftnref\d+" \[\d+\]', '', text)
    
    # Clean up repeated underscores or dashes often used as separators
    text = re.sub(r'_{3,}', '', text)
    text = re.sub(r'-{3,}', '', text)
    
    # Fix spacing issues (multiple spaces to single space)
    # text = re.sub(r'[ \t]+', ' ', text)
    
    return text.strip()

def convert_to_markdown(file_path: Path):
    """
    Converts a single .txt law file to .md.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    output_lines = []
    
    title_found = False
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            output_lines.append("")
            continue
            
        cleaned_line = clean_text(line)
        if not cleaned_line:
            continue

        # Header detection
        # H1: LUẬT ...
        if not title_found and cleaned_line.isupper() and ("LUẬT" in cleaned_line or "NGHỊ ĐỊNH" in cleaned_line):
            # Try to grab the next line if it's also uppercase (often the title is split)
            full_title = cleaned_line
            if i + 1 < len(lines):
                next_line = lines[i+1].strip()
                if next_line and next_line.isupper():
                    full_title += " " + next_line
                    # We skip the next line in the loop by some logic? 
                    # Simpler: just detect "LUẬT" and make it H1
            output_lines.append(f"# {full_title}")
            title_found = True
            continue

        # H2: Chương ...
        if re.match(r'^Chương [IVXLCDM]+', cleaned_line, re.IGNORECASE):
            # Chapter titles are often on the following line
            title = cleaned_line
            if i + 1 < len(lines):
                next_line = lines[i+1].strip()
                if next_line and not re.match(r'^Điều \d+', next_line) and not re.match(r'^Mục \d+', next_line):
                    title += " - " + next_line
            output_lines.append(f"## {title}")
            continue
            
        # Skip lines that were likely part of a previously processed Chapter/Section title
        if i > 0:
            prev_line = lines[i-1].strip()
            if re.match(r'^(Chương [IVXLCDM]+|Mục \d+)', prev_line, re.IGNORECASE):
                # Check if this line was assimilated into the header
                continue

        # H3: Mục ...
        if re.match(r'^Mục \d+', cleaned_line, re.IGNORECASE):
            title = cleaned_line
            if i + 1 < len(lines):
                next_line = lines[i+1].strip()
                if next_line and not re.match(r'^Điều \d+', next_line):
                    title += " - " + next_line
            output_lines.append(f"### {title}")
            continue

        # H4: Điều ...
        if re.match(r'^Điều \d+', cleaned_line):
            output_lines.append(f"#### {cleaned_line}")
            continue

        # Default: just append the cleaned line
        output_lines.append(cleaned_line)

    # Write output
    output_path = file_path.with_suffix('.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(output_lines))
    print(f"Converted: {file_path.name} -> {output_path.name}")

def main():
    law_dir = Path("/Users/khanhnq35/Documents/AI_Vin/assignments/2A202600199-Nguyen_Quoc_Khanh--Day07/data/law")
    txt_files = list(law_dir.glob("*.txt"))
    
    if not txt_files:
        print("No .txt files found in data/law")
        return

    for txt_file in txt_files:
        convert_to_markdown(txt_file)

if __name__ == "__main__":
    main()
