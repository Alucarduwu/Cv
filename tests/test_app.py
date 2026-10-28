import os,re,subprocess,sys,tempfile,unittest,urllib.parse,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class AppTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();env=dict(os.environ,JOBPILOT_DATA=cls.tmp.name,JOBPILOT_PORT='18766');cls.p=subprocess.Popen([sys.executable,'app.py'],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);line=cls.p.stdout.readline();assert '18766' in line
 @classmethod
 def tearDownClass(cls):cls.p.terminate();cls.p.wait(timeout=5);cls.p.stdout.close();cls.p.stderr.close();cls.tmp.cleanup()
 def get(self,path):return urllib.request.urlopen('http://127.0.0.1:18766'+path).read().decode()
 def post(self,path,body):return urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:18766'+path,data=urllib.parse.urlencode(body).encode())).read().decode()
 def test_full_flow_and_csrf(self):
  page=self.get('/profile');token=re.search('name="token" value="([^"]+)',page).group(1)
  with self.assertRaises(urllib.error.HTTPError):self.post('/demo',{'token':'invalid'})
  self.post('/profile',{'token':token,'name':'Alex Example','skills':'React, Python','experience':'Engineer | Company A | 2025\nEngineer | Company B | 2026','contact_email':'alex@example.com'})
  self.post('/demo',{'token':token});self.assertIn('Junior Full Stack Developer',self.get('/jobs'))
  cv=self.get('/resume?id=demo%3A001');self.assertIn('Company A',cv);self.assertIn('Company B',cv)
  output=self.post('/answers',{'token':token,'id':'demo:001','questions':'Correo electrónico\n¿Tienes visa?'});self.assertIn('alex@example.com',output);self.assertIn('needs_review',output)
  self.post('/draft',{'token':token,'id':'demo:001','headline':'Software Engineer','summary':'Experiencia verificable'});self.assertIn('Software Engineer',self.get('/resume?id=demo%3A001'))
  self.post('/track',{'token':token,'id':'demo:001','state':'preparacion','notes':'revisar'});self.assertIn('preparacion',self.get('/tracking'))
  try:import reportlab
  except ImportError:pass
  else:
   pdf=urllib.request.urlopen('http://127.0.0.1:18766/pdf?id=demo%3A001');self.assertTrue(pdf.read().startswith(b'%PDF-'));self.assertEqual(pdf.headers.get_content_type(),'application/pdf')
if __name__=='__main__':unittest.main()
