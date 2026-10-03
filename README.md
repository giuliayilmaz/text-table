# Text Table

Render aligned text tables in Python, correctly accounting for East-Asian wide characters that occupy two terminal columns.

```python
from text_table import Table, Column, render_table

table = Table([Column("名前", align="left"), Column("点", align="right")])
table.add_row("Alice", 90)
table.add_row("太郎", 85)
print(table.render())

# Or in one call:
print(render_table(["A", "B"], [("x", "y")]))
```

## Why this exists

Plain \`str.ljust` and \`f"{s:<10}"` count characters, not terminal columns. A string like \`"太郎"` is two characters but renders in four columns, which silently breaks any table aligned with the built-in formatters. This library uses \`unicodedata.east_asian_width` to count display width the way a monospaced terminal does, so mixed CJK and ASCII tables line up.

The trade-off: width is computed per Unicode property, not measured against a specific terminal emulator. If your terminal disagrees with Unicode's classification (rare, but possible for custom fonts), alignment will be off.

## The awkward edge

Characters of **Ambiguous** width (many emoji, some punctuation) are treated as width 1. This matches the common Latin-1 terminal. If you are running a CJK-locale terminal that renders these as width 2, the table will misalign for those specific characters. Wide (\`W`) and Fullwidth (\`F`) characters such as CJK ideographs and full-width Latin are always counted as 2. Tabs inside cell content are treated as width 1 rather than expanded to a tab stop.

## Exports

- \`Table(columns)` — builder. \`columns` is a sequence of \`Column` or bare \`str` (treated as left-aligned).
- \`Table.add_row(*values)` — append a row; \`None` renders as empty.
- \`Table.render()` — return the table as a string.
- \`Column(name, align=\"left\", min_width=0)` — column definition; \`align` is \`\"left\"`, \`\"right\"`, or \`\"center\"`.
- \`render_table(columns, rows)` — convenience function building and rendering in one call.

Standard library only. No dependencies.
