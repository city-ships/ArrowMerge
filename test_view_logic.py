import sys
from unittest.mock import MagicMock

# Mock PyQt6 to allow importing view without GUI libs
mock_qt = MagicMock()
sys.modules['PyQt6'] = mock_qt
sys.modules['PyQt6.QtWidgets'] = mock_qt
sys.modules['PyQt6.QtGui'] = mock_qt
sys.modules['PyQt6.QtCore'] = mock_qt

import unittest
from arrowmerge.view import MenuLabelBuilder

class TestMenuLabels(unittest.TestCase):
    def test_push_word(self):
        label = MenuLabelBuilder.get_label('push', 'word')
        self.assertIn("Copy to Changed Text", label)
        self.assertIn("Word", label)
        self.assertIn("⮕", label)
        self.assertNotIn("Push", label) # Ensure old term is gone

    def test_push_line(self):
        label = MenuLabelBuilder.get_label('push', 'line')
        self.assertIn("Copy to Changed Text", label)
        self.assertIn("Line", label)
        self.assertIn("⮕", label)
        self.assertNotIn("Push", label)

    def test_pull_word(self):
        label = MenuLabelBuilder.get_label('pull', 'word')
        self.assertIn("Revert to Previous Text", label)
        self.assertIn("Word", label)
        self.assertIn("⬅", label)
        self.assertNotIn("Pull", label)

    def test_pull_line(self):
        label = MenuLabelBuilder.get_label('pull', 'line')
        self.assertIn("Revert to Previous Text", label)
        self.assertIn("Line", label)
        self.assertIn("⬅", label)
        self.assertNotIn("Pull", label)

if __name__ == '__main__':
    unittest.main()
