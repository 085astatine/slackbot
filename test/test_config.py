# -*- coding: utf-8 -*-


import unittest
import slackbot


class OptionTest(unittest.TestCase):
    def test_default(self):
        option = slackbot.Option('foo')
        data = {'foo': 'bar'}
        self.assertEqual(option.evaluate(data), 'bar')

    def test_type(self):
        option = slackbot.Option('foo', type=int)
        data = {'foo': '1'}
        self.assertEqual(option.evaluate(data), 1)

    def test_required(self):
        option = slackbot.Option('foo', required=True)
        data = {}
        with self.assertRaises(slackbot.OptionError):
            option.evaluate(data)

    def test_choices(self):
        option = slackbot.Option('foo', choices=('foo', 'bar',))
        data = {'foo': 'bar'}
        self.assertEqual(option.evaluate(data), 'bar')

    def test_choices_failed(self):
        option = slackbot.Option('foo', choices=('foo', 'bar',))
        data = {'foo': 'baz'}
        with self.assertRaises(slackbot.OptionError):
            option.evaluate(data)

    def test_choices_with_type(self):
        option = slackbot.Option('foo', type=int, choices=(1, 2))
        data = {'foo': '1'}
        self.assertEqual(option.evaluate(data), 1)

    def test_choices_with_type_failed(self):
        option = slackbot.Option('foo', type=int, choices=(1, 2))
        data = {'foo': '0'}
        with self.assertRaises(slackbot.OptionError):
            option.evaluate(data)

    def test_action(self):
        option = slackbot.Option('foo', action=str.upper)
        data = {'foo': 'bar'}
        self.assertEqual(option.evaluate(data), 'BAR')

if __name__ == '__main__':
    unittest.main()
