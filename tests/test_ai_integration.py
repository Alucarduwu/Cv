import json,os,sys,tempfile,threading,unittest,urllib.parse,urllib.request
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app,jobpilot
from http.server import ThreadingHTTPServer
class AITests(unittest.TestCase):
 def test_reviewed_proposal_not_saved_until_confirmed(self):
  with tempfile.TemporaryDirectory() as d:
   old=(jobpilot.DATA,jobpilot.DB,app.PROFILE);jobpilot.DATA=Path(d);jobpilot.DB=Path(d)/'db';app.PROFILE=Path(d)/'profile.json'
   jobpilot.save_jobs([{'id':'a','title':'Role','company':'Test','url':'https://example.org','description':'React'}],{'name':'Demo','skills':['React']})
   server=ThreadingHTTPServer(('127.0.0.1',0),app.Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();base='http://127.0.0.1:'+str(server.server_port)
   def post(path,body):return urllib.request.urlopen(urllib.request.Request(base+path,data=urllib.parse.urlencode(body).encode())).read().decode()
   try:
    with patch('intelligence.ai_workflow',return_value={'output':{'tailored_resume_summary':'Propuesta verificable'},'warning':'review'}):
     page=post('/ai',{'token':app.TOKEN,'id':'a','task':'resume'})
    self.assertIn('Propuesta verificable',page);self.assertFalse(app.draft_path('a').exists())
    post('/draft',{'token':app.TOKEN,'id':'a','headline':'Dev','summary':'Propuesta revisada'})
    self.assertEqual(json.loads(app.draft_path('a').read_text())['summary'],'Propuesta revisada')
   finally:server.shutdown();server.server_close();thread.join();jobpilot.DATA,jobpilot.DB,app.PROFILE=old
if __name__=='__main__':unittest.main()
