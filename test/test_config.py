# -*- coding: utf-8 -*-

import os
import sys
import unittest
import slackbot


class OptionTest(unittest.TestCase):
    def test_plain(self):
        option = slackbot.Option('foo')
        data = {'foo': 'bar'}
        self.assertEqual(option.evaluate(data), 'bar')

    def test_default(self):
        option = slackbot.Option('foo', default='0')
        data = {}
        self.assertEqual(option.evaluate(data), '0')

    def test_type(self):
        option = slackbot.Option('foo', type=int)
        data = {'foo': '1'}
        self.assertEqual(option.evaluate(data), 1)

    def test_type_with_default(self):
        option = slackbot.Option('foo', default='0', type=int)
        data = {}
        self.assertEqual(option.evaluate(data), 0)

    def test_type_without_default(self):
        option = slackbot.Option('foo', type=int)
        data = {}
        self.assertEqual(option.evaluate(data), None)

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

    def test_action_with_type(self):
        option = slackbot.Option('foo', action=hex, type=int)
        data = {'foo': '0'}
        self.assertEqual(option.evaluate(data), '0x0')

    def test_action_with_default(self):
        option = slackbot.Option('foo', action=str.upper, default='bar')
        data = {}
        self.assertEqual(option.evaluate(data), 'BAR')

    def test_action_without_default(self):
        option = slackbot.Option('foo', action=str.upper)
        data = {}
        self.assertEqual(option.evaluate(data), None)

    def test_action_and_type_with_default(self):
        option = slackbot.Option('foo', action=hex, default='255', type=int)
        data = {}
        self.assertEqual(option.evaluate(data), '0xff')


class OptionHelpTest(unittest.TestCase):
    def test_plain(self):
        option = slackbot.Option('foo')
        self.assertEqual(
                    option.help_message(),
                    '(optional)')

    def test_required(self):
        option = slackbot.Option('foo', help='Foo', required=True)
        self.assertEqual(
                    option.help_message(),
                    'Foo (required)')

    def test_default(self):
        option = slackbot.Option('foo', help='Foo', default='bar')
        self.assertEqual(
                    option.help_message(),
                    'Foo (default: bar)(optional)')

    def test_default_hidden(self):
        option = slackbot.Option('foo', help='Foo', default=b'')
        self.assertEqual(
                    option.help_message(),
                    'Foo (optional)')

    def test_choices(self):
        option = slackbot.Option('foo', help='Foo', choices=(0, 1))
        self.assertEqual(
                    option.help_message(),
                    'Foo {0, 1}(optional)')

    def test_all(self):
        option = slackbot.Option(
                    'foo',
                    default='foo',
                    choices=('foo', 'bar', 'baz'),
                    required=True,
                    help='Foo')
        self.assertEqual(
                    option.help_message(),
                    'Foo {foo, bar, baz}(default: foo)(required)')


class ConfigParserTest(unittest.TestCase):
    def test_plain(self):
        parser = slackbot._config.ConfigParser(
                'Test',
                (slackbot.Option('foo'), slackbot.Option('bar')))
        data = {'foo': '0', 'bar': '1'}
        result = parser.parse(data)
        self.assertEqual(result.foo, '0')
        self.assertEqual(result.bar, '1')

    def test_dict(self):
        parser = slackbot._config.ConfigParser(
                'Test',
                (slackbot.Option('foo'), ))
        data = {'foo': {'bar': '0', 'baz': '1'}}
        result = parser.parse(data)
        self.assertEqual(result.foo.bar, '0')
        self.assertEqual(result.foo.baz, '1')

    def test_list(self):
        parser = slackbot._config.ConfigParser(
                'Test',
                (slackbot.Option('foo'), ))
        data = {'foo': ['bar', 'baz']}
        result = parser.parse(data)
        self.assertEqual(result.foo[0], 'bar')
        self.assertEqual(result.foo[1], 'baz')

    def test_dict_in_list(self):
        parser = slackbot._config.ConfigParser(
                'Test',
                (slackbot.Option('foo'), ))
        data = {'foo': [{'bar': '0'}, {'baz': '1'}]}
        result = parser.parse(data)
        self.assertEqual(result.foo[0].bar, '0')
        self.assertEqual(result.foo[1].baz, '1')

    def test_list_in_dict(self):
        parser = slackbot._config.ConfigParser(
                'Test',
                (slackbot.Option('foo'), ))
        data = {'foo': {'bar': ['0', '1']}}
        result = parser.parse(data)
        self.assertEqual(result.foo.bar[0], '0')
        self.assertEqual(result.foo.bar[1], '1')


class ConfigParserExitTest(unittest.TestCase):
    def setUp(self):
        self._stderr = sys.stderr
        sys.stderr = open(os.devnull, mode='w')

    def tearDown(self):
        sys.stderr.close()
        sys.stderr = self._stderr
        self._stderr = None

    def test_unrecognized_argumets(self):
        parser = slackbot._config.ConfigParser(
                'Test',
                (slackbot.Option('foo'), ))
        data = {'foo': '0', 'bar': '1'}
        with self.assertRaises(SystemExit) as cm:
            retult = parser.parse(data)
        self.assertEqual(cm.exception.code, 2)

    def test_required_failed(self):
        parser = slackbot._config.ConfigParser(
                'Test',
                (slackbot.Option('foo', required=True), ))
        data = {}
        with self.assertRaises(SystemExit) as cm:
            retult = parser.parse(data)
        self.assertEqual(cm.exception.code, 2)

    def test_choices_failed(self):
        parser = slackbot._config.ConfigParser(
                'Test',
                (slackbot.Option('foo', choices=('bar', 'baz')), ))
        data = {'foo': 'foo'}
        with self.assertRaises(SystemExit) as cm:
            retult = parser.parse(data)
        self.assertEqual(cm.exception.code, 2)


class ConfigParserHelpTest(unittest.TestCase):
    def test_plane(self):
        parser = slackbot._config.ConfigParser(
                'Test',
                (slackbot.Option('foo'),
                 slackbot.Option('bar')))
        self.assertEqual(
                parser.help_message(),
                "Test:\n"
                "  foo: # (optional)\n"
                "  bar: # (optional)")


if __name__ == '__main__':
    unittest.main()
