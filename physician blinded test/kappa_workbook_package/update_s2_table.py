"""Update unanimous acceptance in the supplied S2 template without restyling.

Only G11:G44 and the S3-to-S2 title number change. Existing layout, styles,
other results, notes, and workbook parts remain intact.
"""
import argparse
import json
import re
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

NS = {'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def update(results, template, output):
    if template.resolve() == output.resolve():
        raise ValueError('Use a separate output path to preserve the original template')
    metrics = json.loads(results.read_text())['question_metrics']
    lookup = {(r['Model'], r['Question']): r['Unanimous acceptance'] for r in metrics}
    with ZipFile(template) as source:
        xml = source.read('xl/worksheets/sheet1.xml').decode('utf-8')
        root = ET.fromstring(xml)
        strings = []
        if 'xl/sharedStrings.xml' in source.namelist():
            strings = [''.join(si.itertext()) for si in ET.fromstring(source.read('xl/sharedStrings.xml'))]
        cells = {c.attrib['r']:c for c in root.findall('.//x:sheetData/x:row/x:c', NS)}

        def value(ref):
            cell = cells[ref]
            if cell.attrib.get('t') == 'inlineStr':
                return ''.join(cell.find('x:is', NS).itertext())
            text = cell.find('x:v', NS).text
            return strings[int(text)] if cell.attrib.get('t') == 's' else text

        if value('G10') != 'Unanimous acceptance':
            raise ValueError('Unexpected template: G10 must be Unanimous acceptance')
        replacements = {}
        for row in range(11,45):
            key = value(f'A{row}'), value(f'B{row}')
            replacements[f'G{row}'] = f'{lookup[key]:.3f}'
        replacements['A1'] = value('A1').replace('S3 Table.', 'S2 Table.')
        # Preserve all style attributes and XML outside changed cell contents.
        from xml.sax.saxutils import escape
        for ref, text in replacements.items():
            pattern = rf'<(?P<prefix>[\w]+:)?c\b(?P<attrs>[^>]*\br="{ref}"[^>]*)>.*?</(?:[\w]+:)?c>'
            def replace(match):
                prefix = match.group('prefix') or ''
                attrs = re.sub(r'\s+t="[^"]*"', '', match.group('attrs'))
                return f'<{prefix}c{attrs} t="inlineStr"><{prefix}is><{prefix}t>{escape(text)}</{prefix}t></{prefix}is></{prefix}c>'
            xml, n = re.subn(pattern, replace, xml, flags=re.S)
            if n != 1:
                raise ValueError(f'Expected one cell {ref}, got {n}')
        output.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(output, 'w') as target:
            for entry in source.infolist():
                data = xml.encode('utf-8') if entry.filename == 'xl/worksheets/sheet1.xml' else source.read(entry.filename)
                target.writestr(entry, data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', required=True, type=Path)
    parser.add_argument('--template', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    update(args.results, args.template, args.output)
