import argparse
from pathlib import Path

from nbh import lib


def app():
    parser = argparse.ArgumentParser(
        prog="nbh",
        description="Convert one or more Jupyter notebooks to HTML.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="NOTEBOOK",
        help="Path to one or more notebook files (*.ipynb).",
    )
    parser.add_argument(
        "--output",
        metavar="DIR",
        default=".",
        help="Output directory for processed files (default: current directory).",
    )

    args = parser.parse_args()

    for file in args.files:
        # print(f"Processing notebook: {file}")
        # Here you would call the function to parse the notebook
        # For example: parsed_cells = lib.parse_ipynb(file)
        # And then format or save the output as needed
        # lib.format_notebook(parsed_cells)
        parsed_cells = lib.parse_ipynb(file)
        formatted_cells = []
        for cell in parsed_cells:
            if cell["type"] == "code":
                # don't output code unless has an explicitly @nbh:show
                should_show, clean_content = lib.clean_and_format_nbh(cell["source"])
                if should_show and clean_content:
                    ctx = {"content": clean_content}
                    cell_html = lib.render_template("cell.code.html", ctx)
                    formatted_cells.append(cell_html)
            elif cell["type"] == "markdown":
                ctx = {"content": lib.md_to_html(cell["source"])}

                cell_html = lib.render_template("cell.markdown.html", ctx)
                formatted_cells.append(cell_html)

        ctx = {"title": "Notebook HTML Renderer", "cells": formatted_cells}
        html_output = lib.render_template("index.html", ctx)

        Path(args.output).mkdir(parents=True, exist_ok=True)
        output_file_path = Path(args.output) / f"{Path(file).stem}.html"
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(html_output)
            # print(f"Output written to: {output_file_path}")


if __name__ == "__main__":
    app()
