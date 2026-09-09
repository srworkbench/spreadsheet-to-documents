import tempfile
import unittest
from pathlib import Path
from PIL import Image
from review_image import render_images


class ReviewImageTest(unittest.TestCase):
    def test_long_untrusted_record_remains_valid_image_without_path_use(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'images'
            plan = {'counts': {'changed': 1}, 'blocked': True, 'entries': [
                {'id': '../../outside<script>', 'action': 'changed', 'conflict': 'Manual edit',
                 'fields': [{'field': '<tag>', 'before': 'old', 'after': 'new'}],
                 'before': 'A long notice. ' * 200, 'after': 'Updated notice. ' * 200}]}
            render_images(plan, output)
            self.assertEqual([p.name for p in output.iterdir()], ['record-001.png'])
            with Image.open(output / 'record-001.png') as im:
                self.assertEqual(im.width, 1200)
                self.assertGreater(im.height, 2000)
                self.assertFalse(im.info)
    def test_unused_field_changes_and_no_change_batch_get_reports(self):
        for fields in [[], [{'field':'note','before':'a','after':'b'}]]:
            with tempfile.TemporaryDirectory() as tmp:
                out=Path(tmp)/'images'
                render_images({'counts':{'unchanged':1},'blocked':False,'entries':[
                    {'id':'ONE','action':'unchanged','fields':fields,'before':'same','after':'same'}]},out)
                self.assertTrue((out/'record-001.png').is_file())
