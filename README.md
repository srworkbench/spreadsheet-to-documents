# Spreadsheet to documents: review what changed

Change a date in a spreadsheet after generating a batch of Word documents. Which files need rebuilding? Did anyone edit one of them in Word?

This local tool compares the next batch with a saved baseline. Its interactive HTML report traces changed source values to highlighted words in each document. Applying the review creates a separate revision, reuses unaffected files byte for byte, and stops if a baseline document was edited or went missing.

## Try the change review

The included demo creates twelve fictional workshop notices. A renewal date changes from **15 June** to **22 June** for DEMO-004. A note changes for DEMO-009, but that column is not used in the template.

| Input change | Visible result | Apply behavior |
|---|---|---|
| DEMO-004 renewal date | One changed document; changed words highlighted | Rebuild that document |
| DEMO-009 unused note | Source change shown; document text unchanged | Reuse the original bytes |
| A manual Word edit in a separate baseline | Conflict selected; rebuild paused | Stop without creating a new revision |

Select a document in the impact map to inspect its before-and-after text. Use **Show affected only** to narrow the review. The report is a static snapshot of the real comparison; changing source files requires a new review. It does not send data anywhere or generate documents when opened.

## What this adds to mail merge

[Word mail merge](https://support.microsoft.com/en-us/word/use-mail-merge-to-personalize-letters) already fills fields, previews recipients, and lets you edit individual results. Use Word when preserving rich document formatting is the priority. [python-docx-template](https://docxtpl.readthedocs.io/en/latest/) also supports much richer DOCX templates than this tool.

The focus here is reviewing **changes between batches**: distinguish a source edit from an output change, inspect its text effect, detect edits to generated files, and apply only the exact reviewed inputs to a new revision. This is a narrow local workflow, not a replacement for Word or a claim that document generation needs AI.

The comparison uses rendered text for rebuild decisions and SHA-256 hashes for file integrity. That means an unused column can change without a rebuild, while even a formatting-only edit to a generated DOCX pauses the batch. This conservative rule protects manual edits but can produce conflicts after harmless Word saves. It does not attempt to merge those edits automatically.

## Quickstart

Requires Python 3.10 or later. No account, server or API key is needed.

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python demo.py output/revision-demo
```

On Windows, activate the environment with `.venv\Scripts\activate`.

Open these files in a browser:

- `output/revision-demo/review/index.html`: one document needs rebuilding, eleven can be reused.
- `output/revision-demo/conflict-review/index.html`: a manual edit prevents rebuilding.

The demo also applies the first review. Open `output/revision-demo/next-revision/DEMO-004.docx` to see the revised date in the editable document. The baseline remains at `output/revision-demo/baseline/`. Run the demo again with a different output path; it will not overwrite the first run.

## Use your own data

Create a CSV or values-only XLSX with a unique `record_id` column. IDs can contain letters, numbers, hyphens and underscores, up to 80 characters. Preserve ID spelling across revisions. Match plain-text template placeholders to column names, such as `{{organization}}`. Separate paragraphs with blank lines; the first paragraph becomes the title.

```sh
# First version: documents plus a snapshot of the data and template.
python revisions.py build records.csv template.txt output/v1

# After editing the spreadsheet or template, inspect the proposed changes.
python revisions.py review output/v1 records.csv template.txt output/review-v2

# Open output/review-v2/index.html before applying.
python revisions.py apply output/review-v2/plan.json output/v2
```

For XLSX, add `--sheet Records` to `build` or `review` to choose a worksheet. Formulas are rejected because this tool does not calculate Excel formulas. Dates and numbers are inserted as text, so format them for readers before generating.

The report shows added, removed, changed and unchanged records. Removed records are left out of the new revision; their old files remain in the baseline. Reordering rows does not trigger document rebuilds. Required values, malformed placeholders and duplicate IDs are checked before generation.

If inputs, baseline files or the review plan change after review, `apply` stops. Run `review` again into a fresh directory. If a generated file was edited in Word, preserve that edited copy, reconcile the intended changes into the source or template, and create a new baseline in another directory. Do not erase edits just to clear a conflict.

For a one-off batch without revision tracking, the original command still works:

```sh
python generate.py examples/records.csv examples/template.txt output/one-off
```

## Limits and data handling

- Templates support plain paragraphs and simple placeholders. Existing Word layouts, tables, images, conditional logic and rich template formatting are not supported.
- The preview compares generated text, not Word pagination or the content of manual edits. Inspect the actual DOCX files before using them.
- Baseline snapshots contain the source records and template. The HTML report contains document text and changed values. The adjacent plan also contains local input paths. Keep those generated artifacts private when using private inputs; there is no upload or publishing function.
- A review plan references local files by absolute path. Moving the files requires a new review. Treat manifests and plans as local application state, not authenticated records from an untrusted sender.
- Do not edit source files or run concurrent builds against the same destination while applying a review. Inputs are checked again before publication, but this is not a transactional database or a distributed lock.
- A caught generation error leaves no new revision. A forced process termination during the final file moves can leave an incomplete destination; retain the baseline and retry into a fresh directory.
- This tool does not send documents, validate their business meaning, or claim production use. All included demo records are invented.

## Verification

```sh
python -m unittest discover -s tests -v
```

Tests exercise selective rebuilding and byte-preserving reuse, template changes, added and removed records, manual-edit conflicts, stale plans, a mid-build input change, generation failure and retry, HTML escaping, CSV/XLSX validation, and document metadata.

## License

MIT. See [LICENSE](LICENSE).
