import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import career
class CareerTests(unittest.TestCase):
 def test_resume_retains_all_experience_and_escapes(self):
  p={'name':'A <script>','skills':['Python','React'],'experience':[{'role':'Dev','company':'One','highlights':['Built stuff']},{'role':'Dev','company':'Two'}]}
  out=career.resume_html(p,{'title':'Python role','description':'Python'})
  self.assertIn('One',out);self.assertIn('Two',out);self.assertIn('Built stuff',out);self.assertNotIn('<script>',out);self.assertLess(out.index('Python'),out.index('React'))
 def test_unknown_answers_not_invented(self):
  p={'name':'Alex','contact':{'email':'a@example.com'}};out=career.form_answers(p,['Correo electrónico','¿Requieres visa?']);self.assertEqual(out[0]['answer'],'a@example.com');self.assertIsNone(out[1]['answer']);self.assertEqual(out[1]['status'],'needs_review')
 def test_profile_validation(self):
  with self.assertRaises(ValueError):career.normalize({'name':'X','skills':'Python'})
 def test_highlights_survive_editor(self):
  self.assertIn('Built feature',career.text_item({'role':'Dev','highlights':['Built feature']}))
if __name__=='__main__':unittest.main()
