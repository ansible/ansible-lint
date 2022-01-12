import os
from typing import Optional, Union

from ansible.template import Templar
from jinja2 import nodes
from jinja2.environment import Environment
from jinja2.visitor import NodeTransformer
from ruamel.yaml.comments import CommentedMap, CommentedSeq

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules.JinjaTestsAsFilters import JinjaTestsAsFilters
from ansiblelint.transforms import Transform
from ansiblelint.transform_utils import dump
from ansiblelint.utils import ansible_templar, nested_items_path


class FilterNodeTransformer(NodeTransformer):

    # from https://github.com/ansible/ansible/blob/devel/hacking/fix_test_syntax.py
    ansible_test_map = {
        'version_compare': 'version',
        'is_dir': 'directory',
        'is_file': 'file',
        'is_link': 'link',
        'is_abs': 'abs',
        'is_same_file': 'same_file',
        'is_mount': 'mount',
        'issubset': 'subset',
        'issuperset': 'superset',
        'isnan': 'nan',
        'succeeded': 'successful',
        'success': 'successful',
        'change': 'changed',
        'skip': 'skipped',
    }
    ansible_tests = staticmethod(JinjaTestsAsFilters.ansible_tests)

    def visit_Filter(self, node: nodes.Filter) -> Optional[nodes.Node]:
        if node.name not in self.ansible_tests():
            return self.generic_visit(node)

        test_name = self.ansible_test_map.get(node.name, node.name)
        # fields = ("node", "name", "args", "kwargs", "dyn_args", "dyn_kwargs")
        test_node = nodes.Test(
            node.node,
            test_name,
            node.args,
            node.kwargs,
            node.dyn_args,
            node.dyn_kwargs,
        )
        return self.generic_visit(test_node)


class JinjaTestsAreTestsTransform(Transform):
    id = "jinja-tests-are-tests"
    shortdesc = "Replace deprecated Jinja2 filter-style tests with actual tests."
    description = (
        "This updates expressions to use ``result is failed`` instead of "
        "``result|failed``. Using tests as filters was deprecated in "
        "Ansible 2.5 and removed in Ansible 2.9."
    )
    version_added = "5.3"

    wants = JinjaTestsAsFilters
    tags = JinjaTestsAsFilters.tags

    # for raw jinja templates (not yaml) we only need to reformat for one match.
    # keep a list of files so we can skip them.
    _files_fixed = []

    def __call__(
        self,
        match: MatchError,
        lintable: Lintable,
        data: Union[CommentedMap, CommentedSeq, str],
    ) -> None:
        """Transform data to fix the MatchError."""
        if lintable.path in self._files_fixed:
            # text/jinja2 template file was already reformatted. Nothing left to do.
            self._fixed(match)
            return

        basedir: str = os.path.abspath(os.path.dirname(str(lintable.path)))
        templar: Templar = ansible_templar(basedir, templatevars={})
        jinja_env: Environment = templar.environment

        target_key: Optional[Union[int, str]]
        target_parent: Optional[Union[CommentedMap, CommentedSeq]]
        target_template: str

        if str(lintable.base_kind) == 'text/yaml':
            # the full yaml_path is to the string template.
            # we need the parent so we can modify it.
            target_key = match.yaml_path[-1]
            target_parent = self._seek(match.yaml_path[:-1], data)
            target_template = target_parent[target_key]
            if "when" in match.yaml_path:
                target_template = "{{" + target_template + "}}"
        elif str(lintable.base_kind) == 'text/jinja2':
            target_parent = target_key = None
            target_template = data  # the whole file
            # TODO: mark subsequent matches for the same file as fixed
            #       as we will be fixing the entire file.
        else:  # unknown file type
            return

        ast = jinja_env.parse(target_template)
        ast = FilterNodeTransformer().visit(ast)
        new_template = dump(node=ast, environment=jinja_env)

        if target_parent is not None:
            if "when" in match.yaml_path:
                # remove "{{ " and " }}" (dump always adds space w/ braces)
                new_template = new_template[3:-3]
            target_parent[target_key] = new_template
        else:
            with open(lintable.path.resolve(), mode='w', encoding='utf-8') as f:
                f.write(new_template)
            self._files_fixed.append(lintable.path)

        self._fixed(match)
