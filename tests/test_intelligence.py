import json, os, sys, unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import intelligence as i
class IntelligenceTests(unittest.TestCase):
 def test_gaps_distinguishes_profile_and_job(self):
  r=i.gap_report({'description':'React, Python and PostgreSQL'}, {'skills':['React','SQL']})
  self.assertIn('React',[x['skill'] for x in r['matches']]);self.assertIn('Python',[x['skill'] for x in r['potential_gaps']]);self.assertIn('SQL',[x['skill'] for x in r['matches']])
 def test_analytics_counts_per_job(self):
  r=i.analytics([{'title':'Python','description':'Python Python'}],[{'state':'sent'}]);self.assertEqual(r['skill_mentions']['Python'],1);self.assertEqual(r['application_states']['sent'],1)
 def test_provider_required(self):
  with patch.dict(os.environ,{},clear=True):
   with self.assertRaisesRegex(ValueError,'Configure'):i.ai_workflow('review',{}, {})
 def test_rejects_invalid_task(self):
  with self.assertRaises(ValueError):i.ai_workflow('bad',{}, {})
if __name__=='__main__':unittest.main()
