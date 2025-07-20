# nbh

⚡️ Create a beautiful notebook HTML file from a Jupyter notebook

## Highlights

very opinionated HTML renderer for Jupyter notebooks, focusing on simplicity and readability.

It supports Markdown, LaTeX, and Python code cells, with a clean and minimal design.

Tufte CSS is used for styling, providing a clean and elegant look, Github Flavored Markdown is used for rendering Markdown cells, and KaTeX is used for rendering LaTeX equations.

![Sample Output](https://raw.githubusercontent.com/Mistobaan/nbh/c6f2446601aa00b54cddc778607d8bea02937e1d/assets/sample.png)

See [intro_to_latex.ipynb](https://github.com/Mistobaan/nbh/blob/main/assets/intro_to_latex.ipynb) and the generated [intro_to_latex.html](https://rawcdn.githack.com/Mistobaan/nbh/refs/heads/main/assets/intro_to_latex.html) for a more complex example.

## Usage

The recommended way is to use [`uvx`](https://docs.astral.sh/uv/):

```bash
# outputs my_notebook.html in the same directory
uvx nbh my_notebook.ipynb
```

```bash
# outputs each ipynb in the /tmp directory
uvx nbh *.ipynb --output /tmp
```

If you want the latest version, you can run it directly from the GitHub repository (unstable):

```bash
# outputs my_notebook.html in the same directory
uvx git+https://github.com/Mistobaan/nbh my_notebook.ipynb
```

```bash
# outputs my_notebook.html in the /tmp directory
uvx git+https://github.com/Mistobaan/nbh my_notebook.ipynb --output /tmp
```

## License

nbh is licensed under the [MIT LICENSE](https://opensource.org/licenses/MIT)
