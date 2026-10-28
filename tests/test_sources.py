import json,sys,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import jobpilot as j
class SourceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.old=(j.DB,j.DATA);j.DATA=Path(self.tmp.name);j.DB=j.DATA/'db.sqlite';self.profile={'name':'Demo','skills':['Python']}
 def tearDown(self):j.DB,j.DATA=self.old;self.tmp.cleanup()
 def test_ashby_normalizes_public_api(self):
  raw={'jobs':[{'title':'Junior','jobUrl':'https://jobs.example/j','location':'Mexico','isRemote':True,'descriptionPlainText':'Python'}]}
  with patch.object(j,'get_json',return_value=raw):
   jobs=j.fetch_ashby('example')
  self.assertEqual(jobs[0]['source'],'ashby');self.assertIn('Remote',jobs[0]['location']);self.assertEqual(jobs[0]['description'],'Python')
 def test_remotive_cache_and_attribution(self):
  raw={'jobs':[{'id':3,'title':'Engineer','url':'https://remotive.com/jobs/3','company_name':'Co','candidate_required_location':'Mexico','description':'<p>Python</p>'}]}
  with patch.object(j,'get_json',return_value=raw) as request:
   a=j.fetch_remotive();b=j.fetch_remotive()
  self.assertEqual(request.call_count,1);self.assertEqual(a,b);self.assertEqual(a[0]['source'],'Remotive');self.assertEqual(a[0]['description'],'Python')
 def test_duplicate_exact_url(self):
  first={'id':'a','company':'X','title':'Role','url':'https://example.org/1'};second=dict(first,id='b');j.save_jobs([first,second],self.profile);self.assertEqual(len(j.rows('SELECT * FROM jobs')),1)
 def test_batch_continues_after_failure(self):
  f=j.DATA/'sources.json';f.write_text(json.dumps([{'source':'bad','board':'x'},{'source':'ashby','board':'ok'}]))
  with patch.object(j,'fetch_source',side_effect=[ValueError('oops'),[{'id':'x','company':'Y','title':'role','url':'https://example.org'}]]):
   results=j.fetch_batch(f,self.profile)
  self.assertEqual([x['status'] for x in results],['error','ok']);self.assertEqual(len(j.rows('SELECT * FROM jobs')),1)
if __name__=='__main__':unittest.main()
