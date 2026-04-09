#!/usr/bin/env python3
"""
Convert markdown files to styled HTML for browser preview
"""

import sys
import re
from pathlib import Path


def markdown_to_html(md_text):
    """Simple markdown to HTML converter"""
    html = md_text

    # Headers
    html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
    html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
    html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)
    html = re.sub(r"^#### (.+)$", r"<h4>\1</h4>", html, flags=re.MULTILINE)

    # Bold and italic
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html)

    # Code blocks
    html = re.sub(r"`([^`]+)`", r"<code>\1</code>", html)

    # Links
    html = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', html)

    # Horizontal rules
    html = re.sub(r"^---$", "<hr>", html, flags=re.MULTILINE)

    # Checkboxes
    html = re.sub(r"- \[ \]", "☐", html)
    html = re.sub(r"- \[x\]", "☑", html)

    # Unordered lists
    lines = html.split("\n")
    in_list = False
    result = []

    for line in lines:
        if line.strip().startswith("- ") or line.strip().startswith("* "):
            if not in_list:
                result.append("<ul>")
                in_list = True
            # Remove the leading dash/asterisk and wrap in <li>
            item = re.sub(r"^\s*[-*]\s+", "", line)
            result.append(f"<li>{item}</li>")
        else:
            if in_list:
                result.append("</ul>")
                in_list = False
            result.append(line)

    if in_list:
        result.append("</ul>")

    html = "\n".join(result)

    # Paragraphs (lines that aren't already wrapped in tags)
    lines = html.split("\n")
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("<"):
            result.append(f"<p>{line}</p>")
        else:
            result.append(line)

    return "\n".join(result)


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>📄</text></svg>">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            background: #f5f5f5;
            padding: 40px 20px;
            color: #333;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 60px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            color: #00356B;
            font-size: 32px;
            margin-bottom: 10px;
            padding-bottom: 15px;
            border-bottom: 3px solid #00356B;
        }}
        
        h2 {{
            color: #286DC0;
            font-size: 24px;
            margin-top: 40px;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #E5E7EB;
        }}
        
        h3 {{
            color: #374151;
            font-size: 18px;
            margin-top: 25px;
            margin-bottom: 10px;
        }}
        
        h4 {{
            color: #6B7280;
            font-size: 16px;
            margin-top: 20px;
            margin-bottom: 8px;
        }}
        
        p {{
            margin-bottom: 12px;
            color: #4B5563;
        }}
        
        ul {{
            margin: 15px 0;
            padding-left: 30px;
        }}
        
        li {{
            margin-bottom: 8px;
            color: #4B5563;
        }}
        
        strong {{
            color: #1F2937;
            font-weight: 600;
        }}
        
        em {{
            font-style: italic;
            color: #6B7280;
        }}
        
        code {{
            background: #F3F4F6;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 14px;
            color: #EF4444;
        }}
        
        a {{
            color: #2563EB;
            text-decoration: none;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}
        
        hr {{
            border: none;
            border-top: 1px solid #E5E7EB;
            margin: 30px 0;
        }}
        
        /* Checkbox styling */
        li {{
            list-style: none;
        }}
        
        li:has(☐), li:has(☑) {{
            position: relative;
            padding-left: 0;
        }}
        
        @media print {{
            body {{
                background: white;
            }}
            
            .container {{
                box-shadow: none;
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        {content}
    </div>
</body>
</html>
"""


def convert_file(md_file):
    """Convert markdown file to HTML"""
    md_path = Path(md_file)

    if not md_path.exists():
        print(f"Error: {md_file} not found")
        return

    # Read markdown
    with open(md_path, "r") as f:
        md_content = f.read()

    # Convert to HTML
    html_content = markdown_to_html(md_content)

    # Extract title from first h1 or use filename
    title_match = re.search(r"^# (.+)$", md_content, re.MULTILINE)
    title = title_match.group(1) if title_match else md_path.stem

    # Generate full HTML
    full_html = HTML_TEMPLATE.format(title=title, content=html_content)

    # Write HTML file
    html_path = md_path.with_suffix(".html")
    with open(html_path, "w") as f:
        f.write(full_html)

    print(f"✅ Converted: {md_path.name} → {html_path.name}")
    print(f"🌐 Open in browser: file://{html_path.absolute()}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 md_to_html.py <markdown_file>")
        sys.exit(1)

    convert_file(sys.argv[1])
