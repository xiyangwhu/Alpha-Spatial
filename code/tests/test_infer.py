import json
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from infer import load_requests,make_prompt,parse_counts


class InferenceTests(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse_counts('{"ERBB2":3}'),{'ERBB2':3})
        self.assertEqual(parse_counts('{}'),{})
        for value in ['{"G":-1}','{"G":true}','{"G":NaN}','{"G":Infinity}',
                      '{"G":1,"G":2}','[]','{"G":','{"G":"3"}']:
            self.assertIsNone(parse_counts(value),value)

    def test_input_and_prompt(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);Image.new('RGB',(512,512)).save(root/'image.png')
            row=dict(request_id='test',image='image.png',bbox_norm=[10,20,30,40],
                     disease='Breast Cancer',panel='Biomarkers and Housekeeping Genes Custom Panel')
            file=root/'requests.jsonl';file.write_text(json.dumps(row)+'\n')
            self.assertEqual(len(load_requests(file)),1)
            self.assertIn('<|box_start|>[10,20,30,40]<|box_end|>',make_prompt(row))
            file.write_text((json.dumps(row)+'\n')*2)
            with self.assertRaises(ValueError):load_requests(file)
            for box in [[10,20,9,40],[0,0,1000,10],[0.,0,10,10],[0,0,1]]:
                file.write_text(json.dumps(dict(row,bbox_norm=box))+'\n')
                with self.assertRaises(ValueError):load_requests(file)
            file.write_text(json.dumps(dict(row,image='../outside.png'))+'\n')
            with self.assertRaises(ValueError):load_requests(file)


if __name__=='__main__':unittest.main()
