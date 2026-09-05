# Spreadsheet to Word documents

Generate one editable Word document per spreadsheet row. Use it for routine notices, service reminders, or summaries that share the same structure.

The tool reads CSV or XLSX, fills placeholders in a plain-text template, and writes DOCX files. It validates the whole batch before writing documents and refuses to overwrite an existing output directory. Everything runs locally; no account or AI API is required.

## Quickstart

Requires Python 3.10 or later.

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python generate.py examples/records.csv examples/template.txt output/demo
```

On Windows, activate the environment with `.venv\Scripts\activate`.

Open `output/demo/DEMO-001.docx` in Word or a compatible editor. The two fictional rows produce two separate service reminders. The first document includes:

> The Equipment maintenance service for Example Workshop A is scheduled for renewal on 2030-06-15.

## Use your own template

- Include a unique `record_id` column. IDs may contain letters, numbers, hyphens, and underscores, up to 80 characters.
- Match template fields to column names: `{{organization}}`, `{{service}}`, and so on.
- Separate paragraphs with blank lines. The first paragraph becomes the document title.
- Every referenced value must be present. Blank rows are skipped. Other invalid rows reject the batch.

For Excel input:

```sh
python generate.py records.xlsx template.txt output/batch --sheet Records
```

Use a values-only worksheet; formulas are rejected because this tool does not calculate Excel formulas. Dates and numbers are inserted as text, so format them for readers before generating the documents.

## Checks and limits

```sh
python -m unittest discover -s tests -v
```

Tests cover text escaping, missing values, duplicate IDs, unsafe filenames, existing output, XLSX input, formula rejection, and author metadata. A failed validation leaves no output documents. Do not run concurrent builds against the same destination. A process interruption during the final file moves may leave an incomplete destination; choose a fresh output directory for a retry.

This first version supports paragraphs and simple placeholders. It does not preserve an existing Word template, insert tables, send documents, or verify the business meaning of your data. Review generated documents before using them. The included examples are entirely fictional.

## License

MIT. See LICENSE.
