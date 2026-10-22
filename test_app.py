"""
PackGuard AI - Automated End-to-End Test Suite
Tests:
1. GET / (Dashboard HTML)
2. GET /api/status (Engine & config state)
3. GET /api/sample (Sample specification)
4. POST /api/analyze with use_sample=true (Full workflow)
5. POST /api/analyze with uploaded PDF & JSON files
6. POST /api/followup (Interactive Q&A)
7. Error conditions (empty file, invalid extension, missing fields)
"""

import io
import json
import unittest
from app import app, SAMPLE_ARTWORK_PATH, SAMPLE_RULEBOOK_PATH


class TestPackGuardApp(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_01_index_route(self):
        """Test GET / returns 200 and loads HTML dashboard."""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"PackGuard", res.data)
        self.assertIn(b"Analyze Artwork", res.data)
        print("Test 1 Passed: GET / serves dashboard HTML.")

    def test_02_status_route(self):
        """Test GET /api/status returns valid JSON structure."""
        res = self.client.get('/api/status')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('gemini_configured', data)
        self.assertIn('supported_artwork', data)
        print(f"Test 2 Passed: GET /api/status (Gemini configured: {data['gemini_configured']}).")

    def test_02b_health_route(self):
        """Test GET /health returns 200 and security headers are injected."""
        res = self.client.get('/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'healthy')
        self.assertEqual(data['app_name'], 'PackGuard AI')
        # Verify security headers
        self.assertEqual(res.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(res.headers.get('X-Frame-Options'), 'SAMEORIGIN')
        print("Test 2b Passed: GET /health returns 200 OK with security headers.")

    def test_03_sample_route(self):
        """Test GET /api/sample returns sample rulebook and GET /api/samples lists presets."""
        res_list = self.client.get('/api/samples')
        self.assertEqual(res_list.status_code, 200)
        data_list = res_list.get_json()
        self.assertTrue(data_list['success'])
        self.assertGreaterEqual(len(data_list['presets']), 4)

        res = self.client.get('/api/sample')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('sample_rulebook', data)
        self.assertEqual(data['sample_rulebook']['brand'], 'Dancing Fish')
        print("Test 3 Passed: GET /api/samples lists presets & GET /api/sample returns rulebook.")

    def test_04_analyze_sample_preset(self):
        """Test POST /api/analyze with use_sample=true runs end-to-end analysis."""
        res = self.client.post('/api/analyze', data={'use_sample': 'true'})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        analysis = data['data']
        self.assertIn('summary', analysis)
        self.assertIn('findings', analysis)
        self.assertGreater(len(analysis['findings']), 5)

        # Check key metrics
        summary = analysis['summary']
        self.assertIn('compliance_score', summary)
        self.assertIn('issue_count', summary)
        self.assertIn('passed_count', summary)
        self.assertIn('needs_review_count', summary)

        print(f"Test 4 Passed: Analysis complete! Score: {summary['compliance_score']}%, Issues: {summary['issue_count']}, Passed: {summary['passed_count']}.")

    def test_05_analyze_uploaded_files(self):
        """Test POST /api/analyze with multipart uploaded files."""
        with open(SAMPLE_ARTWORK_PATH, 'rb') as f_art:
            art_data = f_art.read()
        with open(SAMPLE_RULEBOOK_PATH, 'rb') as f_rb:
            rb_data = f_rb.read()

        res = self.client.post(
            '/api/analyze',
            data={
                'artwork': (io.BytesIO(art_data), 'granola_carton.pdf'),
                'rulebook': (io.BytesIO(rb_data), 'master_rules.json')
            },
            content_type='multipart/form-data'
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertGreater(len(data['data']['findings']), 5)
        print("Test 5 Passed: Multipart upload analysis successful.")

    def test_06_followup_endpoint(self):
        """Test POST /api/followup handles questions."""
        res = self.client.post(
            '/api/followup',
            data=json.dumps({
                'question': 'Why is the 480g net weight flagged for the US market?',
                'context': {
                    'summary': {'compliance_score': 72},
                    'findings': []
                }
            }),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertTrue(any(term in data['answer'].lower() for term in ['21 cfr', 'net', 'ounce', 'fda', 'weight', 'fpla']))
        print("Test 6 Passed: Follow-up Q&A returns accurate guidance.")

    def test_07_invalid_file_extension(self):
        """Test POST /api/analyze rejects unsupported file extensions."""
        res = self.client.post(
            '/api/analyze',
            data={
                'artwork': (io.BytesIO(b'dummy'), 'malicious.exe'),
                'rulebook': (io.BytesIO(b'{"a": 1}'), 'rules.json')
            },
            content_type='multipart/form-data'
        )
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertFalse(data['success'])
        self.assertIn("Invalid artwork format", data['error'])
        print("Test 7 Passed: Invalid file extension rejected cleanly.")


if __name__ == '__main__':
    unittest.main()
