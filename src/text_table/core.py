"""Core rendering logic for text tables.

The library's central concern is alignment under terminals that render
East-Asian wide characters in two columns.  \`unicodedata.east_asian_width`
gives us the classification the terminal itself uses: cells are 1 wide for
Narrow/Neutral, 2 for Wide/Fullwidth.  Halfwidth and Ambiguous are treated as
1 because the common Python execution environment is a Latin-1 terminal, and
honouring Ambiguous as 2 would misalign for the majority of users while still
being wrong for the minority who configure a CJK locale.  Picking one rule and
stating it is more honest than a flag nobody can reason about.
"""

import unicodedata
from typing import Any, Iterable, Sequence

__all__ = ["Table", "Column", "render_table"]


def _cell_width(ch: str) -> int:
    """Return the display width of a single character.

    East Asian Wide/Fullwidth characters occupy two columns on a monospaced
    terminal.  Ambiguous-width characters are treated as width 1 because the
    library targets the common Latin-1 terminal; users on a CJK locale who
    need width 2 should pre-process their strings.
    """
    if ch == "\t":
        # We do not attempt to expand tabs to a tab stop; the column width is
        # already computed from content, and a tab inside a cell has no
        # well-defined display width without a cursor position. Treat as 1.
        return 1
    eaw = unicodedata.east_asian_width(ch)
    if eaw in ("W", "F"):
        return 2
    return 1


def display_width(s: str) -> int:
    """Return the number of terminal columns \`s` will occupy."""
    return sum(_cell_width(ch) for ch in s)


def _pad_right(s: str, width: int) -> str:
    """Left-justify \`s` to \`width` display columns, accounting for wide chars."""
    pad = width - display_width(s)
    if pad > 0:
        return s + " " * pad
    return s


def _pad_left(s: str, width: int) -> str:
    """Right-justify \`s` to \`width` display columns."""
    pad = width - display_width(s)
    if pad > 0:
        return " " * pad + s
    return s


def _pad_center(s: str, width: int) -> str:
    """Center \`s` in \`width` display columns, biasing left on odd slack."""
    slack = width - display_width(s)
    if slack <= 0:
        return s
    left = slack // 2
    right = slack - left
    return " " * left + s + " " * right


class Column:
    """A column definition: header, alignment, and optional minimum width.

    \`min_width` lets a caller force a column wider than its content, useful
    for tables whose rows are populated incrementally.
    """

    __slots__ = ("name", "align", "min_width")

    def __init__(self, name: str, align: str = "left", min_width: int = 0) -> None:
        if align not in ("left", "right", "center"):
            raise ValueError(f"align must be 'left', 'right', or 'center', got {align!r}")
        if min_width < 0:
            raise ValueError("min_width must be non-negative")
        self.name = name
        self.align = align
        self.min_width = min_width

    def __repr__(self) -> str:
        return f"Column(name={self.name!r}, align={self.align!r}, min_width={self.min_width})"


def _str_value(v: Any) -> str:
    """Render a cell value to its string form.

    \`None` becomes an empty string so absent data does not print the
    literal text \`None`, which would mislead readers of the rendered table.
    """
    if v is None:
        return ""
    return str(v)


class Table:
    """A text table builder that aligns cells by terminal display width.

    Rows may be added incrementally; \`render()` finalises the layout based
    on the maximum width seen in each column across all rows.
    """

    def __init__(self, columns: Sequence[Column | str]) -> None:
        normalized: list[Column] = []
        for c in columns:
            if isinstance(c, str):
                normalized.append(Column(c))
            else:
                normalized.append(c)
        if not normalized:
            raise ValueError("a table must have at least one column")
        self.columns: list[Column] = normalized
        self.rows: list[list[str]] = []

    def add_row(self, *values: Any) -> "Table":
        """Append a row.  Values are coerced to str; \`None` becomes empty."""
        if len(values) != len(self.columns):
            raise ValueError(
                f"row has {len(values)} values, expected {len(self.columns)}"
            )
        self.rows.append([_str_value(v) for v in values])
        return self

    def _col_widths(self) -> list[int]:
        """Compute the display width of each column, including the header."""
        widths: list[int] = []
        for i, col in enumerate(self.columns):
            w = display_width(col.name)
            if col.min_width > w:
                w = col.min_width
            for row in self.rows:
                if i < len(row):
                    cw = display_width(row[i])
                    if cw > w:
                        w = cw
            widths.append(w)
        return widths

    def render(self) -> str:
        """Return the table as a single string with a border line per row."""
        widths = self._col_widths()
        lines: list[str] = []

        border = " " + " | ".join("-" * w for w in widths) + " "
        lines.append(border)

        def fmt_cell(s: str, width: int, align: str) -> str:
            if align == "right":
                return _pad_left(s, width)
            if align == "center":
                return _pad_center(s, width)
            return _pad_right(s, width)

        header_cells = [
            fmt_cell(col.name, widths[i], col.align)
            for i, col in enumerate(self.columns)
        ]
        lines.append(" " + " | ".join(header_cells) + " ")
        lines.append(border)

        for row in self.rows:
            cells = [
                fmt_cell(row[i], widths[i], self.columns[i].align)
                for i in range(len(self.columns))
            ]
            lines.append(" " + " | ".join(cells) + " ")

        lines.append(border)
        return "\n".join(lines)


def render_table(
    columns: Iterable[Column | str],
    rows: Iterable[Sequence[Any]],
) -> str:
    """Convenience: build and render a Table in one call."""
    table = Table(list(columns))
    for row in rows:
        table.add_row(*row)
    return table.render()
