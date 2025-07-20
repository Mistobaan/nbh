import html
import json
import re
from importlib.resources import files
from typing import Any


def parse_ipynb(file_path):
    """
    Parse an IPython notebook (.ipynb) file cell by cell.
    This function loads the JSON structure of the notebook and processes each cell,
    extracting key information like cell type, source code/markdown, and outputs (if any).
    It prefers the standard Jupyter/Colab format (nbformat 4+).

    Args:
        file_path (str): Path to the .ipynb file.

    Returns:
        list: A list of dictionaries, each representing a parsed cell with keys:
              - 'index': int
              - 'type': str (e.g., 'code', 'markdown')
              - 'source': str (joined source lines)
              - 'outputs': list (if code cell, simplified outputs)
              - 'metadata': dict (cell metadata)

    Raises:
        ValueError: If the file is not a valid notebook.
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as err:
        msg = "Invalid JSON in the .ipynb file."
        raise ValueError(msg) from err
    except FileNotFoundError as err:
        msg = f"File not found: {file_path}"
        raise ValueError(msg) from err

    if "nbformat" not in data or data["nbformat"] < 4:
        msg = "Unsupported notebook format (nbformat < 4)."
        raise ValueError(msg)

    if "cells" not in data or not isinstance(data["cells"], list):
        msg = "No 'cells' found or invalid structure in the notebook."
        raise ValueError(msg)

    parsed_cells = []
    for i, cell in enumerate(data["cells"]):
        if not isinstance(cell, dict):
            continue  # Skip invalid cells

        cell_type = cell.get("cell_type", "unknown")
        source_lines = cell.get("source", [])
        source = "".join(source_lines) if isinstance(source_lines, list) else str(source_lines)

        # Handle outputs for code cells (simplified: extract text or data if present)
        outputs = []
        if cell_type == "code":
            raw_outputs = cell.get("outputs", [])
            for out in raw_outputs:
                if "text" in out:
                    outputs.append("".join(out["text"]))
                elif "data" in out and "text/plain" in out["data"]:
                    outputs.append("".join(out["data"]["text/plain"]))

        metadata = cell.get("metadata", {})

        parsed_cells.append(
            {
                "index": i + 1,
                "type": cell_type,
                "source": source.strip(),
                "outputs": outputs,
                "metadata": metadata,
            }
        )

    return parsed_cells


def normalize_html(html_str):
    # Decode HTML entities
    html_str = html.unescape(html_str)
    # Remove comments
    html_str = re.sub(r"<!--[\s\S]*?-->", "", html_str)
    # Remove all whitespace characters (spaces, tabs, newlines)
    html_str = re.sub(r"\s+", "", html_str)
    # Convert to lowercase for case-insensitive comparison
    return html_str.lower()


def compare_html_strings(html1, html2):
    """
    Compare two HTML strings for equality, ignoring spaces and newlines.
    Returns True if they are equivalent, False otherwise.
    """
    normalized1 = normalize_html(html1)
    normalized2 = normalize_html(html2)
    return normalized1 == normalized2


def render_template(template_path: str, context: dict[str, Any]) -> str:
    """
    Renders a template file by substituting variables and handling simple loops.

    - Substitutes `{{ variable }}` with values from the context.
    - Renders sub-templates with `{% render("sub_template.html", item) for item in items %}`.
    """
    content = read_static_file(template_path)

    def get_from_context(key: str, local_context: dict[str, Any]):
        # handles dot notation like "a.b.c"
        keys = key.split(".")
        value = local_context
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                try:
                    value = getattr(value, k)
                except (AttributeError, TypeError):
                    return None
        return value

    # Handle loops
    def handle_loop(match):
        sub_template_path_str, loop_var_name, iterable_name = match.groups()

        iterable = get_from_context(iterable_name, context)
        if not isinstance(iterable, list) or isinstance(iterable, tuple):
            # Silently ignore if not iterable or not found
            return ""

        rendered_parts = []
        for item in iterable:
            sub_context = context.copy()
            sub_context[loop_var_name] = item
            # tpl = render_template(sub_template_path_str, sub_context)
            rendered_parts.append(item)

        return "".join(rendered_parts)

    loop_pattern = re.compile(
        r"{%\s*render\(\"([^\"]+)\"\s*,\s*(\w+)\s*\)\s+for\s+\2\s+in\s+([\w\.]+)\s*%}"
    )
    content = loop_pattern.sub(handle_loop, content)

    # Handle variable substitution
    def handle_variable(match):
        var_name = match.group(1)
        value = get_from_context(var_name, context)
        return str(value) if value is not None else ""

    var_pattern = re.compile(r"{{\s*([\w\.]+)\s*}}")
    return var_pattern.sub(handle_variable, content)


def read_static_file(filename: str) -> str:
    """
    Read a static file from the package.
    Returns the content as a string.
    """
    # 'files' points to the package root; joinpath navigates to the file
    resource_path = files("nbh").joinpath("static", filename)
    if not resource_path.is_file():
        msg = f"Static file '{filename}' not found in package."
        raise FileNotFoundError(msg)

    # For text files: read_text()
    return resource_path.read_text(encoding="utf-8")


def parse_inline(text):
    if re.search(r"\$.*?\$", text):
        parts = re.split(r"(\$.*?\$)", text, flags=re.DOTALL)
        return "".join(
            f"<span>{p}</span>" if p.strip().startswith("$") else parse_inline(p) for p in parts
        )

    # Images
    def image_repl(m):
        alt = m.group(1)
        src = m.group(2).replace('"', '"')
        return f'<img src="{src}" alt="{alt}">'

    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", image_repl, text)

    # Links
    def link_repl(m):
        return f"""<a href="{m.group(2).replace('"', "")}">{m.group(1)}</a>"""

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link_repl, text)

    # Code
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)

    # Bold
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)

    # Italic
    text = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", text)
    text = re.sub(r"_([^_]+)_", r"<em>\1</em>", text)

    # Strikethrough
    return re.sub(r"~~([^~]+)~~", r"<del>\1</del>", text)


def convert_indented_to_pre(markdown_text):
    # Split the input into lines
    lines = markdown_text.splitlines()
    output = []
    i = 0
    in_indented_block = False
    indented_lines = []

    while i < len(lines):
        line = lines[i]
        # Check if the line is indented (4+ spaces or a tab)
        is_indented = bool(re.match(r"^\s{4,}|\t", line))

        if is_indented and not in_indented_block:
            # Start of a new indented block
            in_indented_block = True
            indented_lines = [line.lstrip()]  # Remove leading indentation
        elif is_indented and in_indented_block:
            # Continue collecting indented lines
            indented_lines.append(line.lstrip())
        elif not is_indented and in_indented_block:
            # End of indented block, wrap in <pre>
            output.append("<pre>")
            output.extend(indented_lines)
            output.append("</pre>")
            in_indented_block = False
            indented_lines = []
            output.append(line)  # Add the non-indented line
        else:
            # Non-indented line, not in a block
            output.append(line)

        i += 1


def parse_markdown_cell(md):
    paragraphs = re.split("\n\n", md)
    html = []
    for p in paragraphs:
        out = md_to_html(p)
        html.append(out)
        print(p)
        print("-" * 80)
        print(out)
        print("=" * 80)
    return "".join(html)


def md_to_html(md):
    if re.search(r"\$\$.*?\$\$", md, re.DOTALL):
        parts = re.split(r"(\$\$(.*?)\$\$)", md, flags=re.DOTALL)
        html = []
        for i in range(0, len(parts), 3):
            html.append(md_to_html(parts[i]))
            if i + 2 < len(parts):
                inner = parts[i + 2]
                html.append(f"<p>$${inner}$$</p>")
        return "".join(html)

    if re.search(r"^\\begin\{align\}.*?\\end\{align\}", md, re.DOTALL):
        parts = re.split(r"(^\\begin\{align\}.*?\\end\{align\})", md, flags=re.DOTALL)
        html = []
        for part in parts:
            if part.startswith(r"\begin{align}"):
                latex = part.replace(r"\begin{align}", r"\begin{align*}").replace(
                    r"\end{align}", "\end{align*}"
                )
                html.append(f"<p>$${latex}$$</p>")
            else:
                html.append(md_to_html(part))
        return "".join(html)

    lines = md.splitlines()
    html = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        # Header
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            text = line[level:].strip()
            span = """<span class="heading-link-symbol" aria-hidden="false"/>"""
            html.append(f"<h{level}>{parse_inline(text)}{span}</h{level}>")
            i += 1
            continue
        # HR
        if re.match(r"^-{3,}$", line) or re.match(r"^\*{3,}$", line) or re.match(r"^_{3,}$", line):
            html.append("<hr>")
            i += 1
            continue
        # Code block
        if line.startswith("```"):
            lang = line[3:].strip()
            i += 1
            code = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            code_text = "\n".join(code)
            if lang:
                html.append(f'<pre><code class="language-{lang}">{code_text}</code></pre>')
            else:
                html.append(f"<pre><code>{code_text}</code></pre>")
            continue
        # Blockquote
        if line.startswith(">"):
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip()[1:].strip())
                i += 1
            quote_text = "\n".join(quote)
            quote_html = md_to_html(quote_text)
            html.append(f"<blockquote>{quote_html}</blockquote>")
            continue
        # Table
        if "|" in line and i + 1 < len(lines) and "---" in lines[i + 1]:
            print("parsing table")
            # Headers
            headers = [h.strip() for h in lines[i].strip().strip("|").split("|")]
            i += 1
            align_line = lines[i].strip().strip("|")
            align_parts = [a.strip() for a in align_line.split("|")]
            aligns = []
            for a in align_parts:
                if a.startswith(":") and a.endswith(":"):
                    aligns.append("center")
                elif a.startswith(":"):
                    aligns.append("left")
                elif a.endswith(":"):
                    aligns.append("right")
                else:
                    aligns.append(None)
            i += 1
            html.append("<table>")
            html.append("<thead><tr>")
            for j, h in enumerate(headers):
                al = aligns[j] if j < len(aligns) else None
                style = f' style="text-align:{al};"' if al else ""
                html.append(f"<th{style}>{parse_inline(h)}</th>")
            html.append("</tr></thead>")
            html.append("<tbody>")

            while i < len(lines) and "|" in lines[i]:
                row_line = lines[i].strip().strip("|")
                cells = [c.strip() for c in row_line.split("|")]
                html.append("<tr>")
                for j, cell in enumerate(cells):
                    al = aligns[j] if j < len(aligns) else None
                    style = f' style="text-align:{al};"' if al else ""
                    html.append(f"<td{style}>{parse_inline(cell)}</td>")
                html.append("</tr>")
                i += 1
            html.append("</tbody>")
            html.append("</table>")
            continue
        # List
        curr_line = lines[i]
        line = curr_line.lstrip()
        is_ordered = re.match(r"^\d+\.", line)
        is_unordered = line.startswith(("- ", "* ", "+ "))
        if is_ordered or is_unordered:
            tag = "ol" if is_ordered else "ul"
            html.append(f"<{tag}>")
            while i < len(lines):
                curr_line = lines[i]
                if not curr_line.strip():
                    i += 1
                    continue
                curr = curr_line.lstrip()
                curr_is_ordered = re.match(r"^\d+\.", curr)
                curr_is_unordered = curr.startswith(("- ", "* ", "+ "))
                if not (curr_is_ordered or curr_is_unordered):
                    break
                if (is_ordered and not curr_is_ordered) or (not is_ordered and curr_is_ordered):
                    break
                if is_ordered:
                    m = re.match(r"^\d+\.", curr)
                    item = curr[m.end() :].strip()
                else:
                    item = curr[2:].strip()
                # Task list
                checked = None
                if item.startswith("[ ] "):
                    item = item[4:]
                elif item.startswith(("[x] ", "[X] ")):
                    checked = " checked"
                    item = item[4:]
                if checked is not None:  # wait, always '', or ' checked'
                    li = f'<li><input type="checkbox"{checked} disabled> {parse_inline(item)}</li>'
                else:
                    li = f"<li>{parse_inline(item)}</li>"
                html.append(li)
                i += 1
            html.append(f"</{tag}>")
            continue

        # Indented Block
        # Check if the line is indented (4+ spaces or a tab)
        if bool(re.match(r"^\s{4,}|\t", lines[i])):
            indented_lines = []
            while i < len(lines) and bool(re.match(r"^\s{4,}|\t", lines[i])):
                # Continue collecting indented lines
                indented_lines.append(lines[i].lstrip())
                i += 1
            if html and html[-1].endswith("</pre>"):
                # don't add another <pre> if the last element is already a pre block
                html.append("<code>")
            else:
                html.append("<pre><code>")
            html.extend(indented_lines)
            html.append("</code></pre>")
            continue

        # Paragraph
        para = []
        while i < len(lines) and lines[i].strip():
            para.append(lines[i].strip())
            i += 1
        para_text = " ".join(para)
        html.append(f"<p>{parse_inline(para_text)}</p>")

    return "\n".join(html)


def clean_and_format_nbh(text):
    # Split the text into lines
    lines = text.splitlines()

    # Remove extra empty lines and find the first non-empty line
    cleaned_lines = []
    found_nbh_show = False
    for line in lines:
        stripped_line = line.strip()
        # Skip empty or whitespace-only lines at the start
        if not stripped_line and not cleaned_lines:
            continue
        # Check for # @nbh:show in the first non-empty line with flexible spacing
        if not found_nbh_show and stripped_line:
            # Match # @nbh:show with any spacing (e.g., #.@nbh: show)
            match = re.search(r"#\s*@+\s*nbh\s*:\s*show", line)
            if match:
                # Remove the matched # @nbh:show directive (with any spacing)
                cleaned_line = re.sub(r"#\s*@+\s*nbh\s*:\s*show\s*", "", line)
                if cleaned_line.strip():  # Only add if there's content left
                    cleaned_lines.append(cleaned_line)
                found_nbh_show = True
            else:
                cleaned_lines.append(line)
        else:
            cleaned_lines.append(line)

    # Join the cleaned lines
    cleaned_text = "\n".join(cleaned_lines).rstrip()

    # If the text is empty, return it
    return found_nbh_show, cleaned_text.strip()
