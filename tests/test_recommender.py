#!/usr/bin/env python3
"""Unit tests for keyword recommendation logic."""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_models.robot_keyword_recommender import KeywordPatternAnalyzer, RobotKeywordRecommender


class TestContextRecommendations(unittest.TestCase):
    def setUp(self):
        self.analyzer = KeywordPatternAnalyzer()
        self.analyzer.keyword_sequences = [
            ['Log To Console', 'Sleep', 'Click Element', 'Should Be Equal'],
            ['Log To Console', 'Wait', 'Click Element', 'Close Browser'],
            ['Open Browser', 'Log To Console', 'Sleep', 'Close Browser'],
        ]
        self.analyzer.keyword_libraries = {
            'Log To Console': 'BuiltIn',
            'Sleep': 'BuiltIn',
            'Click Element': 'SeleniumLibrary',
            'Should Be Equal': 'BuiltIn',
            'Wait': 'BuiltIn',
            'Close Browser': 'SeleniumLibrary',
            'Open Browser': 'SeleniumLibrary',
        }
        self.analyzer.keyword_transitions = {
            'Log To Console': {'Sleep': 2, 'Wait': 1},
            'Sleep': {'Click Element': 2, 'Close Browser': 1},
        }

    def test_exact_context_match(self):
        recs = self.analyzer.get_context_recommendations(['Log To Console', 'Sleep'], 3)
        self.assertTrue(recs)
        keywords = [r.keyword for r in recs]
        self.assertIn('Click Element', keywords)

    def test_fuzzy_context_match(self):
        recs = self.analyzer.get_context_recommendations(
            ['Log To Console', 'Wait', 'Click Element'], 3
        )
        self.assertTrue(recs)

    def test_ngram_fallback(self):
        recs = self.analyzer.get_context_recommendations(['Unknown Keyword'], 3)
        self.assertEqual(recs, [])

        recs = self.analyzer.get_context_recommendations(['Log To Console'], 3)
        self.assertTrue(recs)
        self.assertIn(recs[0].keyword, ['Sleep', 'Wait'])

    def test_context_truncation(self):
        long_context = [f'kw{i}' for i in range(15)]
        long_context[-2] = 'Log To Console'
        long_context[-1] = 'Sleep'
        seq = long_context + ['Click Element']
        self.analyzer.keyword_sequences.append(seq)
        self.analyzer.keyword_libraries.update({
            'Log To Console': 'BuiltIn',
            'Sleep': 'BuiltIn',
            'Click Element': 'SeleniumLibrary',
        })
        for i in range(15):
            self.analyzer.keyword_libraries[f'kw{i}'] = 'BuiltIn'

        recs = self.analyzer.get_context_recommendations(long_context, 3, max_context_window=10)
        self.assertTrue(recs)

    def test_keywords_in_order(self):
        seq = ['A', 'B', 'C', 'D']
        self.assertEqual(self.analyzer._keywords_in_order(seq, ['A', 'C']), 2)
        self.assertEqual(self.analyzer._keywords_in_order(seq, ['A', 'D']), 3)
        self.assertEqual(self.analyzer._keywords_in_order(seq, ['D', 'A']), -1)


class TestRobotKeywordRecommender(unittest.TestCase):
    def test_returns_dicts(self):
        recommender = RobotKeywordRecommender()
        recommender.analyzer.keyword_sequences = [['Log To Console', 'Sleep', 'Click Element']]
        recommender.analyzer.keyword_libraries = {
            'Log To Console': 'BuiltIn',
            'Sleep': 'BuiltIn',
            'Click Element': 'SeleniumLibrary',
        }
        recommender.analyzer.keyword_transitions = {
            'Log To Console': {'Sleep': 1},
            'Sleep': {'Click Element': 1},
        }

        recs = recommender.get_context_recommendations(['Log To Console'], 3)
        self.assertTrue(recs)
        self.assertIsInstance(recs[0], dict)
        self.assertIn('library', recs[0])
        self.assertIn('keyword', recs[0])


class TestXmlDiscovery(unittest.TestCase):
    def test_finds_xml_in_subdirectories(self):
        xml_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'xml_files')
        if not os.path.exists(xml_dir):
            self.skipTest('data/xml_files not present')

        output_files = []
        for f in os.listdir(xml_dir):
            file_path = os.path.join(xml_dir, f)
            if os.path.isfile(file_path) and f.endswith('.xml'):
                output_files.append(file_path)
            elif os.path.isdir(file_path):
                for sub_file in os.listdir(file_path):
                    sub_file_path = os.path.join(file_path, sub_file)
                    if os.path.isfile(sub_file_path) and sub_file.endswith('.xml'):
                        output_files.append(sub_file_path)

        self.assertGreater(len(output_files), 0)


if __name__ == '__main__':
    unittest.main()
