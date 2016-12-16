import os
import unittest
from gb_compiler.grammar_parser import transform_to_dict
from gb_compiler.grammar_parser.lr1_parser import read_bnf_file


class GrammarLineParser(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_simple_rule(self):
        sample_text = "<a> ::= <b>"
        expected = {"a": [[{"non_terminal": "b"}]]}
        result = transform_to_dict(sample_text)
        self.assertEqual(result, expected)

    def test_big_right_side(self):
        sample_text = '<a> ::= <b> "-" <c> <d> "+"'
        expected = {
            "a": [
                [
                    {"non_terminal": "b"},
                    {"terminal": "-"},
                    {"non_terminal": "c"},
                    {"non_terminal": "d"},
                    {"terminal": "+"}
                ]
            ]
        }
        result = transform_to_dict(sample_text)
        self.assertEqual(result, expected)

    def test_two_rules(self):
        sample_text = '<a> ::= <b> "c"\n' \
                      '<b> ::= "d"'
        expected = {
            "a": [
                [
                    {"non_terminal": "b"},
                    {"terminal": "c"}
                ]
            ],
            "b": [
                [
                    {"terminal": "d"}
                ]
            ]
        }
        result = transform_to_dict(sample_text)
        self.assertEqual(result, expected)

    def test_two_rules_same_right_side(self):
        sample_text = '<a> ::= <b> "c"\n' \
                      '<a> ::= "d"'
        expected = {
            "a": [
                [
                    {"non_terminal": "b"},
                    {"terminal": "c"}
                ],
                [
                    {"terminal": "d"}
                ]
            ]
        }
        result = transform_to_dict(sample_text)
        self.assertEqual(result, expected)


class BNFGrammarLoading(unittest.TestCase):
    def test_loading(self):
        print(os.getcwd())
        read_bnf_file("../samples/grammar_parser/Gramaticas/ejemplo2.bnf")


if __name__ == "__main__":
    unittest.main()
