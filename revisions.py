"""Review document changes before creating a new, separate batch revision."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from collections import Counter
from pathlib import Path

from generate import read_records, render_text, write_document

MANIFEST = "revision.json"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encode(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def read_inputs(source: Path, template: Path, sheet=None):
    source_bytes, template_bytes = source.read_bytes(), template.read_bytes()
    records = read_records(source, sheet)
    text = template_bytes.decode("utf-8")
    rendered = dict(render_text(text, records))
    # Reject edits during parsing, including formula/workbook changes.
    if source.read_bytes() != source_bytes or template.read_bytes() != template_bytes:
        raise ValueError("Inputs changed while reading; retry with stable files")
    return {"records": records, "template": text, "rendered": rendered,
            "source_sha256": digest(source_bytes), "template_sha256": digest(template_bytes)}


def publish_directory(output: Path, populate):
    """Stage all work, reserve a fresh destination, roll back caught failures."""
    if output.exists() or output.is_symlink():
        raise ValueError("Output already exists; choose a new revision directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".revision-build-", dir=output.parent) as temporary:
        staging = Path(temporary)
        populate(staging)
        output.mkdir()  # Exclusive reservation: never replace a concurrent writer.
        try:
            for item in staging.iterdir():
                item.rename(output / item.name)
        except BaseException:
            shutil.rmtree(output)
            raise


def write_revision(staging, inputs, reused=None):
    reused = reused or {}
    documents = {}
    for identifier, text in inputs["rendered"].items():
        destination = staging / f"{identifier}.docx"
        if identifier in reused:
            destination.write_bytes(reused[identifier])
        else:
            write_document(text, destination)
        documents[identifier] = digest(destination.read_bytes())
    manifest = {"version": 1, "records": inputs["records"], "template": inputs["template"],
                "documents": documents}
    (staging / MANIFEST).write_bytes(encode(manifest))


def build(source: Path, template: Path, output: Path, sheet=None):
    inputs = read_inputs(source, template, sheet)
    publish_directory(output, lambda stage: write_revision(stage, inputs))
    return len(inputs["records"])


def load_baseline(baseline: Path):
    manifest_bytes = (baseline / MANIFEST).read_bytes()
    manifest = json.loads(manifest_bytes)
    if manifest.get("version") != 1:
        raise ValueError("Unsupported revision manifest; use a version 1 baseline")
    rendered = dict(render_text(manifest["template"], manifest["records"]))
    if set(rendered) != set(manifest["documents"]):
        raise ValueError("Baseline manifest has inconsistent document IDs")
    actual, conflicts = {}, {}
    for identifier in rendered:
        path = baseline / f"{identifier}.docx"
        if path.is_symlink():
            conflicts[identifier] = "Generated file is a symbolic link"
        elif not path.is_file():
            conflicts[identifier] = "Generated file is missing"
        else:
            actual[identifier] = path.read_bytes()
            if digest(actual[identifier]) != manifest["documents"][identifier]:
                conflicts[identifier] = "Generated file changed after the baseline was built"
    return manifest, rendered, actual, conflicts, digest(manifest_bytes)


def make_plan(baseline: Path, source: Path, template: Path, sheet=None):
    old, previous, actual, conflicts, manifest_hash = load_baseline(baseline)
    inputs = read_inputs(source, template, sheet)
    before = {row["record_id"]: row for row in old["records"]}
    after = {row["record_id"]: row for row in inputs["records"]}
    # A case-only rename is ambiguous on case-insensitive file systems.
    old_case = {key.casefold(): key for key in before}
    for key in after:
        if key.casefold() in old_case and key != old_case[key.casefold()]:
            raise ValueError("A record_id changed only letter case; keep its original spelling")
    entries = []
    for identifier in sorted(set(before) | set(after)):
        old_text, new_text = previous.get(identifier), inputs["rendered"].get(identifier)
        if identifier not in before:
            action = "added"
        elif identifier not in after:
            action = "removed"
        elif old_text != new_text:
            action = "changed"
        else:
            action = "unchanged"
        fields = []
        for name in sorted(set(before.get(identifier, {})) | set(after.get(identifier, {}))):
            old_value = before.get(identifier, {}).get(name)
            new_value = after.get(identifier, {}).get(name)
            if old_value != new_value:
                fields.append({"field": name, "before": old_value, "after": new_value})
        entries.append({"id": identifier, "action": action,
                        "conflict": conflicts.get(identifier), "fields": fields,
                        "before": old_text, "after": new_text})
    plan = {"version": 1, "baseline": str(baseline.resolve()), "source": str(source.resolve()),
            "template": str(template.resolve()), "sheet": sheet,
            "baseline_sha256": manifest_hash,
            "baseline_files": {key: digest(value) for key, value in actual.items()},
            "source_sha256": inputs["source_sha256"], "template_sha256": inputs["template_sha256"],
            "template_changed": old["template"] != inputs["template"],
            "counts": dict(Counter(entry["action"] for entry in entries)),
            "blocked": bool(conflicts), "entries": entries}
    return plan, inputs, actual


def review(baseline: Path, source: Path, template: Path, output: Path, sheet=None):
    from review_page import render_page
    plan, _, _ = make_plan(baseline, source, template, sheet)
    def populate(stage):
        (stage / "plan.json").write_bytes(encode(plan))
        (stage / "index.html").write_text(render_page(plan), encoding="utf-8")
    publish_directory(output, populate)
    return plan


def apply(plan_path: Path, output: Path):
    saved = json.loads(plan_path.read_bytes())
    plan, inputs, actual = make_plan(Path(saved["baseline"]), Path(saved["source"]),
                                     Path(saved["template"]), saved.get("sheet"))
    if plan != saved:
        raise ValueError("Review is stale or edited. Run review again before applying")
    if plan["blocked"]:
        raise ValueError("A baseline document changed or is missing. Preserve those edits and reconcile before rebuilding")
    reused = {entry["id"]: actual[entry["id"]] for entry in plan["entries"]
              if entry["action"] == "unchanged"}
    def populate(stage):
        write_revision(stage, inputs, reused)
        # Detect an edit during generation before exposing the new revision.
        current, _, _ = make_plan(Path(saved["baseline"]), Path(saved["source"]),
                                  Path(saved["template"]), saved.get("sheet"))
        if current != saved:
            raise ValueError("Files changed during generation; no new revision was published")
    publish_directory(output, populate)
    return plan["counts"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    first = commands.add_parser("build", help="Create a baseline with its source snapshot")
    inspect = commands.add_parser("review", help="Create an interactive change report; write no documents")
    inspect.add_argument("baseline", type=Path)
    for command in (first, inspect):
        command.add_argument("source", type=Path)
        command.add_argument("template", type=Path)
        command.add_argument("output", type=Path)
        command.add_argument("--sheet")
    commit = commands.add_parser("apply", help="Apply an unchanged review into a fresh revision")
    commit.add_argument("plan", type=Path)
    commit.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "build":
            print(f"Built {build(args.source, args.template, args.output, args.sheet)} documents and a baseline snapshot")
        elif args.command == "review":
            plan = review(args.baseline, args.source, args.template, args.output, args.sheet)
            print(json.dumps({"counts": plan["counts"], "blocked": plan["blocked"]}))
            print(f"Open {args.output / 'index.html'} to inspect changes")
        else:
            print(json.dumps(apply(args.plan, args.output)))
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(2, f"Cannot {args.command}: {exc}\n")


if __name__ == "__main__":
    main()
