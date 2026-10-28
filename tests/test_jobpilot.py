import os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import jobpilot as j
class JobPilotTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();j.DB=Path(self.tmp.name)/'test.db';self.profile={'name':'Test','skills':['React','Node.js','SQL']};self.job={'id':'a','company':'Example','title':'Junior React Developer','location':'Remote Mexico','description':'React Node.js REST APIs','url':'https://example.com/a','source':'test'};j.save_jobs([self.job],self.profile)
 def tearDown(self):self.tmp.cleanup()
 def test_import_idempotent_preserves_history(self):
  con=j.db();con.execute("INSERT INTO applications(job_id,state,created_at) VALUES('a','sent','today')");con.commit();con.close();j.save_jobs([self.job,self.job],self.profile);self.assertEqual(len(j.rows('SELECT * FROM jobs')),1);self.assertEqual(j.rows('SELECT state FROM applications')[0]['state'],'sent')
 def test_scoring_word_boundaries(self):
  score,why=j.score_job({'title':'Junior','location':'Remote Mexico','description':'reactive and nosql'},self.profile);self.assertNotIn('React',why[0]);self.assertNotIn('SQL',why[0]);self.assertEqual(score,36)
 def test_send_consent_and_duplicate(self):
  d=Path(self.tmp.name);(d/'a.pdf').write_bytes(b'%PDF-1.4');(d/'body.txt').write_text('Hello');opts=('a','hr@example.com','Hello',d/'body.txt',d/'a.pdf','smtp.example.com',587,'u@example.com','secret')
  with self.assertRaisesRegex(ValueError,'confirm-send'):j.send(*opts,False)
  with patch('jobpilot.smtplib.SMTP') as smtp:
   j.send(*opts,True);smtp.return_value.__enter__.return_value.send_message.assert_called_once()
  with self.assertRaisesRegex(ValueError,'ya tiene'):j.send(*opts,True)
  self.assertEqual(j.rows('SELECT state FROM applications')[0]['state'],'sent')
 def test_uncertain_failure_prevents_retry(self):
  d=Path(self.tmp.name);(d/'a.pdf').write_bytes(b'%PDF-1.4');(d/'body.txt').write_text('Hello');opts=('a','hr@example.com','Hello',d/'body.txt',d/'a.pdf','smtp.example.com',587,'u@example.com','secret',True)
  with patch('jobpilot.smtplib.SMTP',side_effect=OSError('network')):
   with self.assertRaises(OSError):j.send(*opts)
  self.assertEqual(j.rows('SELECT state FROM applications')[0]['state'],'uncertain')
  with self.assertRaisesRegex(ValueError,'ya tiene'):j.send(*opts)
 def test_ai_requires_configuration(self):
  with patch.dict(os.environ,{},clear=True):
   with self.assertRaisesRegex(ValueError,'Configura'):j.ai_draft(self.job,self.profile)
if __name__=='__main__':unittest.main()
