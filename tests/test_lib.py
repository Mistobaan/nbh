import unittest
from pathlib import Path

from src.nbh.lib import compare_html_strings, render_template


class TestRenderTemplate(unittest.TestCase):
    def test_render_template(self):
        fixtures = Path(__file__).parent / "fixtures"
        template_path = fixtures / "template.html"
        context = {"name": "World", "items": [{"name": "Item 1"}, {"name": "Item 2"}]}
        result = render_template(template_path, context)
        expected_result = """Hello World
    <p>Item 1</p>
    <p>Item 2</p>
    """
        assert compare_html_strings(result, expected_result)


if __name__ == "__main__":
    unittest.main()
