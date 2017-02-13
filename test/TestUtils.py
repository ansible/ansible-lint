# -*- coding: utf-8 -*-

# Copyright (c) 2013-2014 Will Thames <will@thames.id.au>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import unittest

import ansiblelint.utils as utils


class TestUtils(unittest.TestCase):

    def test_tokenize_blank(self):
        (cmd, args, kwargs) = utils.tokenize("")
        self.assertEqual(cmd, '')
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {})

    def test_tokenize_single_word(self):
        (cmd, args, kwargs) = utils.tokenize("vars:")
        self.assertEqual(cmd, "vars")

    def test_tokenize_string_module_and_arg(self):
        (cmd, args, kwargs) = utils.tokenize("hello: a=1")
        self.assertEqual(cmd, "hello")
        self.assertEqual(kwargs, {"a": "1"})

    def test_tokenize_strips_action(self):
        (cmd, args, kwargs) = utils.tokenize("action: hello a=1")
        self.assertEqual(cmd, "hello")
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {"a": "1"})

    def test_tokenize_more_than_one_arg(self):
        (cmd, args, kwargs) = utils.tokenize("action: whatever bobbins x=y z=x c=3")
        self.assertEqual(cmd, "whatever")
        self.assertEqual(args[0], "bobbins")
        self.assertEqual(args[1], "x=y")
        self.assertEqual(args[2], "z=x")
        self.assertEqual(args[3], "c=3")

    def test_tokenize_command_with_args(self):
        cmd, args, kwargs = utils.tokenize("action: command chdir=wxy creates=zyx tar xzf zyx.tgz")
        self.assertEqual(cmd, "command")
        self.assertEqual(args[0], "tar")
        self.assertEqual(args[1], "xzf")
        self.assertEqual(args[2], "zyx.tgz")
        self.assertEqual(kwargs, {'chdir': 'wxy', 'creates': 'zyx'})

    def test_normalize_simple_command(self):
        task1 = dict(name="hello", action="command chdir=abc echo hello world")
        task2 = dict(name="hello", command="chdir=abc echo hello world")
        self.assertEqual(utils.normalize_task(task1, 'tasks.yml'), utils.normalize_task(task2, 'tasks.yml'))

    def test_normalize_complex_command(self):
        task1 = dict(name="hello", action={'module': 'ec2',
                                           'region': 'us-east1',
                                           'etc': 'whatever'})
        task2 = dict(name="hello", ec2={'region': 'us-east1',
                                        'etc': 'whatever'})
        task3 = dict(name="hello", ec2="region=us-east1 etc=whatever")
        task4 = dict(name="hello", action="ec2 region=us-east1 etc=whatever")
        self.assertEqual(utils.normalize_task(task1, 'tasks.yml'), utils.normalize_task(task2, 'tasks.yml'))
        self.assertEqual(utils.normalize_task(task2, 'tasks.yml'), utils.normalize_task(task3, 'tasks.yml'))
        self.assertEqual(utils.normalize_task(task3, 'tasks.yml'), utils.normalize_task(task4, 'tasks.yml'))

    def test_normalize_args(self):
        task1 = dict(git={'version': 'abc'}, args={'repo': 'blah', 'dest': 'xyz'})
        task2 = dict(git={'version': 'abc', 'repo': 'blah', 'dest': 'xyz'})

        task3 = dict(git='version=abc repo=blah dest=xyz')
        task4 = dict(git=None, args={'repo': 'blah', 'dest': 'xyz', 'version': 'abc'})
        self.assertEqual(utils.normalize_task(task1, 'tasks.yml'), utils.normalize_task(task2, 'tasks.yml'))
        self.assertEqual(utils.normalize_task(task1, 'tasks.yml'), utils.normalize_task(task3, 'tasks.yml'))
        self.assertEqual(utils.normalize_task(task1, 'tasks.yml'), utils.normalize_task(task4, 'tasks.yml'))

    def test_extract_from_list(self):
        block = dict(
                block = [dict(tasks=[dict(name="hello",command="whoami")])],
                test_none = None,
                test_string = 'foo'
        )
        blocks = [block]

        test_list = utils.extract_from_list(blocks, ['block'])
        test_none = utils.extract_from_list(blocks, ['test_none'])

        self.assertEqual(list(block['block']), test_list)
        self.assertEqual(list(), test_none)
        with self.assertRaises(RuntimeError):
            utils.extract_from_list(blocks, ['test_string'])

    def test_simple_template(self):
        v = "{{ playbook_dir }}"
        result = utils.template('/a/b/c', v, dict(playbook_dir='/a/b/c'))
        self.assertEqual(result, "/a/b/c")

    def test_missing_filter(self):
        v = "{{ 'hello' | doesnotexist }}"
        result = utils.template('/a/b/c', v, dict(playbook_dir='/a/b/c'))
        self.assertEqual(result, "{{ 'hello' | doesnotexist }}")

    def test_existing_filter_on_unknown_var(self):
        v = "{{ hello | to_json }}"
        result = utils.template('/a/b/c', v, dict(playbook_dir='/a/b/c'))
        self.assertEqual(result, "{{ hello | to_json }}")

    def test_task_to_str_unicode(self):
        task = dict(fail=dict(msg=u"unicode é ô à"))
        result = utils.task_to_str(utils.normalize_task(task, 'filename.yml'))
        self.assertEqual(result, u"fail msg=unicode é ô à")
