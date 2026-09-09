"""Native PNG review cards from the exact apply plan; no browser or network."""
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BG = '#edf2f5'
INK = '#173044'
MUTED = '#526778'
BLUE = '#245cca'
RED = '#a73532'
GREEN = '#21714c'


def font(size):
    # Pillow's bundled font avoids machine-specific fonts and private paths.
    return ImageFont.load_default(size=size)


def render_card(plan, entry, destination):
    """Write a complete, wrapped report for one record. Never execute report code."""
    width = 1200
    rows = []
    def add(text, size=27, color=INK, gap=12):
        for paragraph in str(text).split('\n'):
            lines = textwrap.wrap(paragraph, width=max(20, int(1060 / (size * .62))),
                                  replace_whitespace=False) or ['']
            for line in lines:
                rows.append((line, size, color, 8))
        rows.append(('', 0, color, gap))
    counts = plan['counts']
    add('SPREADSHEET TO DOCUMENTS / CHANGE REVIEW', 22, MUTED, 20)
    if plan['blocked']:
        add('Manual edit detected. Batch paused.', 46, RED)
    else:
        add(f"Rebuild {counts.get('changed', 0) + counts.get('added', 0)}. Reuse {counts.get('unchanged', 0)}.", 52, BLUE)
    add(f"{counts.get('changed',0)} changed / {counts.get('added',0)} new / {counts.get('unchanged',0)} reusable / {counts.get('removed',0)} removed", 24, MUTED, 20)
    add(entry['id'] + '.docx', 34)
    if entry.get('conflict'):
        add(entry['conflict'], 27, RED)
        add('Saved text is shown below. The manual edit is preserved; this tool does not merge it.', 24, MUTED)
    if plan.get('template_changed'):
        add('Template changed. Compare the complete text below.', 25, BLUE)
    for field in entry['fields']:
        add(field['field'], 23, MUTED, 2)
        add(f"Before: {field['before'] if field['before'] is not None else '(absent)'}", 29, RED, 2)
        add(f"After:   {field['after'] if field['after'] is not None else '(absent)'}", 29, GREEN)
    if entry['action'] == 'unchanged':
        add('Output text is identical. Reuse the original document bytes.', 27, GREEN)
    elif entry['action'] == 'removed':
        add('Omit from the new batch. Keep the baseline file.', 27)
    add('SAVED BASELINE TEXT', 22, MUTED)
    add(entry['before'] if entry['before'] is not None else '(No baseline document)', 27)
    add('PROPOSED TEXT', 22, MUTED)
    add(entry['after'] if entry['after'] is not None else '(Removed from the new batch)', 27)
    add('REVIEW SNAPSHOT / Documents have not been changed by this report.', 21, MUTED)
    height = max(850, 110 + sum(size + 8 + gap for _, size, _, gap in rows))
    image = Image.new('RGB', (width, height), BG)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((28, 28, width-28, height-28), radius=20, fill='white')
    y = 56
    for text, size, color, gap in rows:
        if size:
            draw.text((65, y), text, font=font(size), fill=color)
        y += size + 8 + gap
    image.save(destination, format='PNG')


def render_images(plan, directory):
    """All affected records, or the first reusable record for a no-change batch."""
    directory = Path(directory)
    directory.mkdir()
    selected = [e for e in plan['entries'] if e['action'] != 'unchanged' or e['fields'] or e.get('conflict')]
    if not selected:
        selected = plan['entries'][:1]
    for number, entry in enumerate(selected, 1):
        # Numeric filenames never use untrusted IDs as paths.
        render_card(plan, entry, directory / f'record-{number:03}.png')
