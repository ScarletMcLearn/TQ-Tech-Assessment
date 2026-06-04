#!/usr/bin/env python
"""Run a test command and save its console output as a timestamped PDF."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import textwrap
from datetime import datetime
from pathlib import Path


PAGE_WIDTH = 612
PAGE_HEIGHT = 792
MARGIN = 42
FONT_SIZE = 9
LINE_HEIGHT = 12
MAX_CHARS = 96


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a test suite and save the output as a PDF report."
    )
    parser.add_argument("suite", help="Report prefix, such as backend-test.")
    parser.add_argument("cwd", help="Directory where the test command should run.")
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Command to run after --.",
    )
    args = parser.parse_args()

    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        parser.error("a test command is required after --")

    return args


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run_command(command: list[str], cwd: Path) -> tuple[int, str]:
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    output_lines: list[str] = []
    assert process.stdout is not None
    for line in process.stdout:
        print(line, end="")
        output_lines.append(line)

    return process.wait(), "".join(output_lines)


def pdf_escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("(", "\\(")
        .replace(")", "\\)")
        .replace("\r", "")
    )


def report_lines(
    suite: str, command: list[str], cwd: Path, exit_code: int, output: str
) -> list[str]:
    finished_at = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    lines = [
        f"Test report: {suite}",
        f"Finished: {finished_at}",
        f"Working directory: {cwd}",
        f"Command: {' '.join(command)}",
        f"Exit code: {exit_code}",
        "",
        "Output:",
        "",
    ]
    lines.extend(output.splitlines() or ["<no output>"])
    return lines


def paginate(lines: list[str]) -> list[list[str]]:
    wrapped_lines: list[str] = []
    for line in lines:
        expanded = line.expandtabs(4)
        wrapped = textwrap.wrap(
            expanded,
            width=MAX_CHARS,
            replace_whitespace=False,
            drop_whitespace=False,
        )
        wrapped_lines.extend(wrapped or [""])

    lines_per_page = (PAGE_HEIGHT - (MARGIN * 2)) // LINE_HEIGHT
    return [
        wrapped_lines[index : index + lines_per_page]
        for index in range(0, len(wrapped_lines), lines_per_page)
    ] or [[""]]


def build_pdf(pages: list[list[str]]) -> bytes:
    objects: list[bytes] = []

    def add_object(body: bytes) -> int:
        objects.append(body)
        return len(objects)

    catalog_id = add_object(b"<< /Type /Catalog /Pages 2 0 R >>")
    pages_id = add_object(b"")
    font_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")

    page_ids: list[int] = []
    content_ids: list[int] = []
    for page in pages:
        content = ["BT", f"/F1 {FONT_SIZE} Tf", f"{MARGIN} {PAGE_HEIGHT - MARGIN} Td"]
        for index, line in enumerate(page):
            if index:
                content.append(f"0 -{LINE_HEIGHT} Td")
            content.append(f"({pdf_escape(line)}) Tj")
        content.append("ET")
        content_bytes = "\n".join(content).encode("latin-1", errors="replace")
        content_id = add_object(
            b"<< /Length "
            + str(len(content_bytes)).encode("ascii")
            + b" >>\nstream\n"
            + content_bytes
            + b"\nendstream"
        )
        page_id = add_object(
            (
                f"<< /Type /Page /Parent {pages_id} 0 R "
                f"/MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
                f"/Resources << /Font << /F1 {font_id} 0 R >> >> "
                f"/Contents {content_id} 0 R >>"
            ).encode("ascii")
        )
        content_ids.append(content_id)
        page_ids.append(page_id)

    kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
    objects[pages_id - 1] = (
        f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>"
    ).encode("ascii")

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for object_id, body in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{object_id} 0 obj\n".encode("ascii"))
        pdf.extend(body)
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
            "startxref\n"
            f"{xref_offset}\n"
            "%%EOF\n"
        ).encode("ascii")
    )
    return bytes(pdf)


def write_pdf(suite: str, lines: list[str]) -> Path:
    timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
    output_dir = repo_root() / "reports" / "pdf"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{suite}-report-{timestamp}.pdf"
    counter = 2
    while output_path.exists():
        output_path = output_dir / f"{suite}-report-{timestamp}-{counter}.pdf"
        counter += 1
    output_path.write_bytes(build_pdf(paginate(lines)))
    return output_path


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    args = parse_args()
    root = repo_root()
    cwd = (root / args.cwd).resolve()
    exit_code, output = run_command(args.command, cwd)
    report = write_pdf(
        args.suite, report_lines(args.suite, args.command, cwd, exit_code, output)
    )
    print(f"\nPDF test report saved to {os.path.relpath(report, root)}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
