import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import io
import json
import urllib.request
import urllib.error

# Add current directory to path so we can import get_error_rate
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    import get_error_rate
except ImportError:
    # If running from root, maybe need monitoring.get_error_rate?
    # Or just add monitoring to path
    sys.path.append(os.path.join(os.getcwd(), 'monitoring'))
    import get_error_rate

class TestGetErrorRate(unittest.TestCase):

    @patch('urllib.request.urlopen')
    def test_get_system_info_success(self, mock_urlopen):
        # Create a mock response object
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({'key': 'value'}).encode('utf-8')
        # Allow context manager usage (with urllib.request.urlopen(...) as response:)
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None

        mock_urlopen.return_value = mock_response

        result = get_error_rate.get_system_info('192.168.1.100')
        self.assertEqual(result, {'key': 'value'})

    @patch('urllib.request.urlopen')
    def test_get_system_info_failure(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 404
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None

        mock_urlopen.return_value = mock_response

        # Suppress print output
        captured_output = io.StringIO()
        sys.stdout = captured_output

        result = get_error_rate.get_system_info('192.168.1.100')

        sys.stdout = sys.__stdout__
        self.assertIsNone(result)

    def test_calculate_error_rate(self):
        # Mock sys.stdout to capture print output
        captured_output = io.StringIO()
        sys.stdout = captured_output

        info = {
            'stratum': {
                'activePoolMode': 0,
                'pools': [
                    {'accepted': 90, 'rejected': 10},
                    {'accepted': 0, 'rejected': 0}
                ]
            }
        }

        get_error_rate.calculate_error_rate(info)

        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()

        # Check for Primary Pool output
        # Depending on implementation, pool 0 is primary
        self.assertIn("Accepted Shares: 90", output)
        self.assertIn("Rejected Shares: 10", output)
        # 10 / 100 * 100 = 10.00%
        self.assertIn("Error Rate (Reject Rate): 10.00%", output)

    def test_calculate_error_rate_dual_pool(self):
        # Mock sys.stdout to capture print output
        captured_output = io.StringIO()
        sys.stdout = captured_output

        info = {
            'stratum': {
                'activePoolMode': 1,
                'pools': [
                    {'accepted': 90, 'rejected': 10},
                    {'accepted': 45, 'rejected': 5}
                ]
            }
        }

        get_error_rate.calculate_error_rate(info)

        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()

        self.assertIn("Pool 1:", output)
        # Pool 1: 10/100 = 10%
        self.assertIn("Error Rate (Reject Rate): 10.00%", output)

        self.assertIn("Pool 2:", output)
        # Pool 2: 5/50 = 10%
        # It appears twice, so we might need to check count or just presence is enough for now.

    def test_calculate_error_rate_zero_shares(self):
        captured_output = io.StringIO()
        sys.stdout = captured_output

        info = {
            'stratum': {
                'activePoolMode': 0,
                'pools': [
                    {'accepted': 0, 'rejected': 0}
                ]
            }
        }

        get_error_rate.calculate_error_rate(info)

        sys.stdout = sys.__stdout__
        output = captured_output.getvalue()

        self.assertIn("Error Rate (Reject Rate): 0.00%", output)


if __name__ == '__main__':
    unittest.main()
