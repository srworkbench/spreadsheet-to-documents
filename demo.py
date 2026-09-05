"""Build a reproducible demo from wholly invented workshop notices."""
import argparse
import csv
from pathlib import Path

from docx import Document

from revisions import apply, build, publish_directory, review


def create_demo(output: Path):
    # Reserve a fresh directory. All subsequent artifacts remain local here.
    publish_directory(output, lambda _: None)
    template = output / "template.txt"
    source = output / "records.csv"
    revised = output / "revised.csv"
    template.write_text("Workshop renewal\n\n{{organization}}\n\nYour equipment workshop is booked for {{renewal_date}}.\n\nBooking reference: {{record_id}}", encoding="utf-8")
    records = [{"record_id":f"DEMO-{number:03}", "organization":f"Example Workshop {number:02}",
                "renewal_date":"15 June 2030", "note":"Draft"} for number in range(1,13)]
    def save(path):
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(records[0]))
            writer.writeheader(); writer.writerows(records)
    save(source)
    build(source, template, output / "baseline")
    records[3]["renewal_date"] = "22 June 2030"
    records[8]["note"] = "Checked"  # Unused field: no document needs changing.
    save(revised)
    review(output / "baseline", revised, template, output / "review")
    apply(output / "review" / "plan.json", output / "next-revision")
    # A separate baseline demonstrates the difficult case without damaging the first.
    build(source, template, output / "edited-baseline")
    edited = output / "edited-baseline" / "DEMO-004.docx"
    doc = Document(edited); doc.add_paragraph("Fictional manual note: confirm the equipment list."); doc.save(edited)
    review(output / "edited-baseline", revised, template, output / "conflict-review")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        create_demo(args.output)
    except (ValueError, OSError) as exc:
        parser.exit(2, f"Cannot build demo: {exc}\n")
    print(f"Open {args.output / 'review' / 'index.html'} for the change map")
    print(f"Open {args.output / 'conflict-review' / 'index.html'} for the hand-edit conflict")
