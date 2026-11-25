from pathlib import Path
from src.load import get_connection

ANALYTICS_SQL_PATH = Path(__file__).resolve().parent.parent / "sql" / "analytics.sql"


def format_table(rows: list) -> str:
    """Render SQLite rows as an aligned plain-text table."""
    if not rows:
        return "(No rows returned)"

    headers = list(rows[0].keys())
    str_rows = [
        ["NULL" if row[h] is None else str(row[h]) for h in headers] for row in rows
    ]
    widths = [
        max([len(h), *(len(r[i]) for r in str_rows)]) for i, h in enumerate(headers)
    ]

    header_line = " | ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    divider = "-+-".join("-" * w for w in widths)
    body_lines = [
        " | ".join(r[i].ljust(widths[i]) for i, _ in enumerate(headers))
        for r in str_rows
    ]
    return "\n".join([header_line, divider, *body_lines])


def run_analytics() -> None:
    """Run every query in sql/analytics.sql and display formatted output."""
    raw_sql = ANALYTICS_SQL_PATH.read_text(encoding="utf-8")
    statements = [s.strip() for s in raw_sql.split(";") if s.strip()]

    conn = get_connection()
    try:
        for idx, stmt in enumerate(statements, start=1):
            code_lines = [
                line
                for line in stmt.splitlines()
                if line.strip() and not line.strip().startswith("--")
            ]
            if not code_lines:
                continue

            first_line = stmt.splitlines()[0]
            title = (
                first_line.lstrip("- ").strip()
                if first_line.startswith("--")
                else f"Query {idx}"
            )
            rows = conn.execute(stmt).fetchall()
            print(f"\n=== {title} ===")
            print(format_table(rows))
    finally:
        conn.close()


if __name__ == "__main__":
    run_analytics()
