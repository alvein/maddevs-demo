"""Unittests for fragment splitter"""

import unittest
import unittest.mock

from maddevs_demo.msg_split import SplitMessageHTMLParser

class SplitMessageHTMLParserTestCase(unittest.TestCase):
    """Common test for the SplitMessageHTMLParser"""
    def test_exception(self):
        """Testing unbreakable blocks"""
        with self.assertRaises(Exception):
            parser = SplitMessageHTMLParser(max_len=10)
            parser.feed('<marquee>Test case</marquee>')

    def test_common_case(self):
        """Testing common case with unbrakable block"""
        max_len = 40
        parser = SplitMessageHTMLParser(max_len=max_len)
        parser.feed(
            '<div>Possible case<marquee>Test case</marquee> another break of the wall</div>'
        )
        self.assertEqual(len(parser.fragments), 3)
        for fragment in parser.fragments:
            self.assertLessEqual(len(fragment), max_len)
        self.assertListEqual(
            parser.fragments,
            [
                '<div>Possible case</div>',
                '<div><marquee>Test case</marquee> </div>',
                '<div>another break of the wall</div>'
            ]
        )

    @unittest.mock.patch('maddevs_demo.msg_split.print')
    def test_debugging(self, print_mock: "unittest.mock.MagicMock"):
        """Testing if debugging works"""
        parser = SplitMessageHTMLParser(max_len=30, debug=False)
        parser.feed('<marquee>Test case</marquee>')
        print_mock.assert_not_called()
        print_mock.reset_mock()

        parser = SplitMessageHTMLParser(max_len=30, debug=True)
        parser.feed('<marquee>Test case</marquee>')
        print_mock.assert_called_once_with('-- fragment #1: 28 chars --\n<marquee>Test case</marquee>')


if __name__ == '__main__':
    unittest.main()