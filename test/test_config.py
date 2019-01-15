# -*- coding: utf-8 -*-

import os
import sys
import unittest
import slackbot


class OptionTest(unittest.TestCase):
    def test_plain(self):
        option = slackbot.Option('foo')
        input = make_input('bar')
        self.assertEqual(option.evaluate(input), 'bar')

    def test_default(self):
        option = slackbot.Option('foo', default='0')
        input = make_none_input()
        self.assertEqual(option.evaluate(input), '0')

    def test_type(self):
        option = slackbot.Option('foo', type=int)
        input = make_input('1')
        self.assertEqual(option.evaluate(input), 1)

    def test_type_with_default(self):
        option = slackbot.Option('foo', default='0', type=int)
        input = make_none_input()
        self.assertEqual(option.evaluate(input), 0)

    def test_type_without_default(self):
        option = slackbot.Option('foo', type=int)
        input = make_none_input()
        with self.assertRaises(Exception):
            self.assertEqual(option.evaluate(input), None)

    def test_required(self):
        option = slackbot.Option('foo', required=True)
        input = make_none_input()
        with self.assertRaises(slackbot.OptionError):
            option.evaluate(input)

    def test_choices(self):
        option = slackbot.Option('foo', choices=('foo', 'bar',))
        input = make_input('bar')
        self.assertEqual(option.evaluate(input), 'bar')

    def test_choices_failed(self):
        option = slackbot.Option('foo', choices=('foo', 'bar',))
        input = make_input('baz')
        with self.assertRaises(slackbot.OptionError):
            option.evaluate(input)

    def test_choices_with_type(self):
        option = slackbot.Option('foo', type=int, choices=(1, 2))
        input = make_input('1')
        with self.assertRaises(slackbot.OptionError):
            option.evaluate(input)

    def test_action(self):
        option = slackbot.Option('foo', action=str.upper)
        input = make_input('bar')
        self.assertEqual(option.evaluate(input), 'BAR')

    def test_action_with_type(self):
        option = slackbot.Option('foo', action=hex, type=int)
        input = make_input('0')
        self.assertEqual(option.evaluate(input), '0x0')

    def test_action_with_default(self):
        option = slackbot.Option('foo', action=str.upper, default='bar')
        input = make_none_input()
        self.assertEqual(option.evaluate(input), 'BAR')

    def test_action_without_default(self):
        option = slackbot.Option('foo', action=str.upper)
        input = make_none_input()
        with self.assertRaises(Exception):
            self.assertEqual(option.evaluate(input), None)

    def test_action_and_type_with_default(self):
        option = slackbot.Option('foo', action=hex, default='255', type=int)
        input = make_none_input()
        self.assertEqual(option.evaluate(input), '0xff')

    def test_sample(self):
        option = slackbot.Option('foo', sample='bar')
        input = make_none_input()
        self.assertEqual(option.evaluate(input), None)


class OptionSampleTest(unittest.TestCase):
    def test_plain(self):
        option = slackbot.Option('foo')
        self.assertEqual(
                option.sample_message(),
                ['# (optional)',
                 'foo:'])

    def test_indent(self):
        option = slackbot.Option('foo')
        self.assertEqual(
                option.sample_message(indent=2),
                ['  # (optional)',
                 '  foo:'])

    def test_required(self):
        option = slackbot.Option('foo', help='Foo', required=True)
        self.assertEqual(
                option.sample_message(),
                ['# Foo (required)',
                 'foo:'])

    def test_default(self):
        option = slackbot.Option('foo', help='Foo', default='bar')
        self.assertEqual(
                option.sample_message(),
                ['# Foo (default: bar)(optional)',
                 'foo: bar'])

    def test_default_hidden(self):
        option = slackbot.Option('foo', help='Foo', default=b'')
        self.assertEqual(
                option.sample_message(),
                ['# Foo (optional)',
                 'foo: !!binary ""'])

    def test_choices(self):
        option = slackbot.Option('foo', help='Foo', choices=(0, 1))
        self.assertEqual(
                option.sample_message(),
                ['# Foo {0, 1}(optional)',
                 'foo:'])

    def test_sample(self):
        option = slackbot.Option('foo', sample='FOO')
        self.assertEqual(
                option.sample_message(),
                ['# (optional)',
                 'foo: FOO'])

    def test_sample_and_default(self):
        option = slackbot.Option('foo', default='foo', sample='FOO')
        self.assertEqual(
                option.sample_message(),
                ['# (default: foo)(optional)',
                 'foo: FOO'])


class ConfigParserTest(unittest.TestCase):
    def test_plain(self):
        parser = slackbot._config.ConfigParser(slackbot.OptionList(
                'Test',
                [slackbot.Option('foo'),
                 slackbot.Option('bar')]))
        data = {'foo': '0', 'bar': '1'}
        result = parser.parse(data)
        self.assertEqual(result.foo, '0')
        self.assertEqual(result.bar, '1')

    def test_dict(self):
        parser = slackbot._config.ConfigParser(slackbot.OptionList(
                'Test',
                [slackbot.Option('foo')]))
        data = {'foo': {'bar': '0', 'baz': '1'}}
        result = parser.parse(data)
        self.assertEqual(result.foo.bar, '0')
        self.assertEqual(result.foo.baz, '1')

    def test_list(self):
        parser = slackbot._config.ConfigParser(slackbot.OptionList(
                'Test',
                [slackbot.Option('foo')]))
        data = {'foo': ['bar', 'baz']}
        result = parser.parse(data)
        self.assertEqual(result.foo[0], 'bar')
        self.assertEqual(result.foo[1], 'baz')

    def test_dict_in_list(self):
        parser = slackbot._config.ConfigParser(slackbot.OptionList(
                'Test',
                [slackbot.Option('foo')]))
        data = {'foo': [{'bar': '0'}, {'baz': '1'}]}
        result = parser.parse(data)
        self.assertEqual(result.foo[0].bar, '0')
        self.assertEqual(result.foo[1].baz, '1')

    def test_list_in_dict(self):
        parser = slackbot._config.ConfigParser(slackbot.OptionList(
                'Test',
                [slackbot.Option('foo')]))
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
        parser = slackbot._config.ConfigParser(slackbot.OptionList(
                'Test',
                [slackbot.Option('foo')]))
        data = {'foo': '0', 'bar': '1'}
        with self.assertRaises(SystemExit) as cm:
            retult = parser.parse(data)
        self.assertEqual(cm.exception.code, 2)

    def test_required_failed(self):
        parser = slackbot._config.ConfigParser(slackbot.OptionList(
                'Test',
                [slackbot.Option('foo', required=True)]))
        data = {}
        with self.assertRaises(SystemExit) as cm:
            retult = parser.parse(data)
        self.assertEqual(cm.exception.code, 2)

    def test_choices_failed(self):
        parser = slackbot._config.ConfigParser(slackbot.OptionList(
                'Test',
                [slackbot.Option('foo', choices=('bar', 'baz'))]))
        data = {'foo': 'foo'}
        with self.assertRaises(SystemExit) as cm:
            retult = parser.parse(data)
        self.assertEqual(cm.exception.code, 2)


class ConfigParserHelpTest(unittest.TestCase):
    def test_plane(self):
        parser = slackbot._config.ConfigParser(slackbot.OptionList(
                'Test',
                [slackbot.Option('foo'),
                 slackbot.Option('bar')],
                help='test'))
        self.assertEqual(
                parser.sample_message(),
                '# test\n'
                'Test:\n'
                '  # (optional)\n'
                '  foo:\n'
                '  # (optional)\n'
                '  bar:\n')


def make_input(value):
    return slackbot._config.InputValue(is_none=False, value=value)


def make_none_input():
    return slackbot._config.InputValue(is_none=True, value=None)


if __name__ == '__main__':
    unittest.main()
