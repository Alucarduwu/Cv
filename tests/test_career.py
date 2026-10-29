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
class TailoringTests(unittest.TestCase):
 def test_reviewed_experience_requires_matching_source_and_count(self):
  profile={'name':'Alex','experience':['Company A | 2024','Company B | 2025']}
  draft={'experience':['Company A | 2024 | Improved','Company B | 2025 | Improved'],'experience_fingerprint':career.experience_fingerprint(profile)}
  self.assertEqual(career.tailored_profile(profile,draft)['experience'],draft['experience'])
  changed=dict(profile,experience=['Company B | 2025','Company A | 2024'])
  self.assertEqual(career.tailored_profile(changed,draft)['experience'],changed['experience'])
  draft['experience']=['Company A only'];self.assertEqual(career.tailored_profile(profile,draft)['experience'],profile['experience'])
 def test_generated_pdf_preserves_reviewed_experiences(self):
  try:from pypdf import PdfReader
  except ImportError:self.skipTest('pypdf is not installed')
  import io
  p={'name':'Alex','experience':['Company A | 2024','Company B | 2025']};d={'experience':['Company A | 2024 | Built APIs','Company B | 2025 | Built UI'],'experience_fingerprint':career.experience_fingerprint(p)}
  data=career.resume_pdf(p,{'title':'Developer'},d);text=' '.join(x.extract_text() for x in PdfReader(io.BytesIO(data)).pages)
  self.assertIn('Company A',text);self.assertIn('Company B',text);self.assertIn('Built APIs',text)
if __name__=='__main__':unittest.main()
