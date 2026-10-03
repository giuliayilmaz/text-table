import unittest

from text_table import Table, Column, render_table
from text_table.core import display_width


class TestDisplayWidth(unittest.TestCase):
    def test_ascii(self):
        self.assertEqual(display_width("hello"), 5)

    def test_empty(self):
        self.assertEqual(display_width(""), 0)

    def test_cjk_is_wide(self):
        self.assertEqual(display_width("日本語"), 6)

    def test_mixed(self):
        self.assertEqual(display_width("ab日本"), 6)


class TestColumn(unittest.TestCase):
    def test_defaults(self):
        c = Column("Name")
        self.assertEqual(c.name, "Name")
        self.assertEqual(c.align, "left")
        self.assertEqual(c.min_width, 0)

    def test_bad_align(self):
        with self.assertRaises(ValueError):
            Column("X", align="sideways")

    def test_negative_min_width(self):
        with self.assertRaises(ValueError):
            Column("X", min_width=-1)


class TestTableBasic(unittest.TestCase):
    def test_simple_ascii(self):
        t = Table(["Name", "Age"])
        t.add_row("Alice", 30)
        t.add_row("Bob", 7)
        out = t.render()
        lines = out.split("\n")
        self.assertEqual(len(lines), 6)
        self.assertIn("Name", lines[1])
        self.assertIn("Alice", lines[3])
        self.assertIn("Bob", lines[4])

    def test_header_alignment_left(self):
        t = Table([Column("N", align="left"), Column("V", align="left")])
        t.add_row("x", "yz")
        out = t.render()
        # Header "N" in a 1-wide column should be "N".
        # Header "V" in a 2-wide column should be "V ".
        header_line = out.split("\n")[1]
        self.assertEqual(header_line, " N | V  ")

    def test_right_align(self):
        t = Table([Column("Num", align="right")])
        t.add_row("1")
        t.add_row("100")
        out = t.render()
        data_lines = out.split("\n")[3:]
        self.assertEqual(data_lines[0], "   1 ")
        self.assertEqual(data_lines[1], " 100 ")

    def test_center_align_odd_slack(self):
        t = Table([Column("N", align="center")])
        t.add_row("ab")  # width 2; header "N" width 1; col width 2 -> no pad
        t.add_row("a")    # col width becomes 2 -> cell "a" has slack 1, left=0
        out = t.render()
        lines = out.split("\n")
        # row "a" in width 2, slack 1, left=0 right=1 -> "a "
        self.assertEqual(lines[4], " a  ")


class TestWideCharacters(unittest.TestCase):
    def test_cjk_aligns_with_ascii(self):
        t = Table(["名前", "点"]
        ) if False else Table(["名前", "点"])
        t.add_row("Alice", 90)
        t.add_row("太郎", 85)
        out = t.render()
        lines = out.split("\n")
        # Column widths: 名前=4, Alice=5 -> 5; 点=2, 90=2 -> 2
        # Header line: " 名前  | 点 " (名前 is 4 wide, padded to 5 -> one trailing space)
        self.assertEqual(lines[1], " 名前  | 点 ")
        # Alice row: " Alice | 90 "
        self.assertEqual(lines[3], " Alice | 90 ")
        # 太郎 row: " 太郎  | 85 " (4 cells content, 1 pad)
        self.assertEqual(lines[4], " 太郎  | 85 ")

    def test_emoji_not_double(self):
        # 😀 (U+1F600) is East Asian Wide -> width 2 under our rule.
        w = display_width("hi\U0001F600")
        self.assertEqual(w, 4)


class TestEdgeCases(unittest.TestCase):
    def test_none_becomes_empty(self):
        t = Table(["A", "B"])
        t.add_row(None, "x")
        out = t.render()
        lines = out.split("\n")
        # Row: "   | x " with A-width 1, B-width 1
        self.assertEqual(lines[3], "   | x ")

    def test_empty_table_just_header(self):
        t = Table(["A", "B"])
        out = t.render()
        lines = out.split("\n")
        # border, header, border, border (no data rows)
        self.assertEqual(len(lines), 4)
        self.assertEqual(lines[1], " A | B ")

    def test_min_width(self):
        t = Table([Column("A", min_width=5)])
        t.add_row("x")
        out = t.render()
        lines = out.split("\n")
        self.assertEqual(lines[1], " A     ")
        self.assertEqual(lines[3], " x     ")

    def test_wrong_row_length_raises(self):
        t = Table(["A", "B"])
        with self.assertRaises(ValueError):
            t.add_row("only one")

    def test_empty_columns_raises(self):
        with self.assertRaises(ValueError):
            Table([])

    def test_integer_values(self):
        t = Table(["N"])
        t.add_row(42)
        out = t.render()
        self.assertIn("42", out)

    def test_mixed_types(self):
        t = Table(["S", "N", "F"])
        t.add_row("x", 1, 1.5)
        out = t.render()
        self.assertIn("1.5", out)


class TestRenderTableFunction(unittest.TestCase):
    def test_convenience(self):
        out = render_table(["A", "B"], [("x", "y")])
        lines = out.split("\n")
        self.assertEqual(len(lines), 5)
        self.assertEqual(lines[3], " x | y ")

    def test_with_columns(self):
        out = render_table(
            [Column("N", align="right")],
            [("1",), ("22",)],
        )
        lines = out.split("\n")
        self.assertEqual(lines[3], "  1 ")
        self.assertEqual(lines[4], " 22 ")

    def test_no_rows(self):
        out = render_table(["A"], [])
        lines = out.split("\n")
        self.assertEqual(len(lines), 4)


if __name__ == "__main__":
    unittest.main()
