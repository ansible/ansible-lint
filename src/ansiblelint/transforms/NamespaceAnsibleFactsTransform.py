import os
from typing import Optional, Union

from ansible.template import Templar
from jinja2 import nodes
from jinja2.environment import Environment
from jinja2.visitor import NodeTransformer
from ruamel.yaml.comments import CommentedMap, CommentedSeq

from ansiblelint.errors import MatchError
from ansiblelint.file_utils import Lintable
from ansiblelint.rules.AnsibleFactsNamespacingRule import (
    AnsibleFactsNamespacingRule,
    is_fact_name,
)
from ansiblelint.transforms import Transform
from ansiblelint.transform_utils import dump
from ansiblelint.utils import ansible_templar, nested_items_path


class GetVarNodeTransformer(NodeTransformer):
    def visit_Name(self, node: nodes.Name) -> Optional[nodes.Node]:
        # {{ ansible_distribution }}
        # Name(name='ansible_distribution', ctx='load')
        # --> ansible_facts.distribution
        # Getattr(node=Name(name='ansible_facts', ctx='load'), attr='distribution', ctx='load')
        # or --> ansible_facts['distribution']
        # Getitem(node=Name(name='ansible_facts', ctx='load'), arg=Const(value='distribution'), ctx='load')

        prefix_len = len("ansible_")
        name = node.name[prefix_len:]
        if not name or not node.name.startswith("ansible_"):
            return self.generic_visit(node)

        is_a_fact = is_fact_name(name)
        might_be_a_fact = is_a_fact is None
        if is_a_fact or might_be_a_fact:
            new_node = nodes.Getattr(nodes.Name("ansible_facts", "load"), name, "load")
            return self.generic_visit(new_node)

        return self.generic_visit(node)

    # def visit_Const(self, node: nodes.Const) -> Optional[nodes.Node]:
    #     return self.generic_visit(node)

    # def visit_Getitem(self, node: nodes.Getitem) -> Optional[nodes.Node]:
    #     return self.generic_visit(node)

    # def visit_Getattr(self, node: nodes.Getattr) -> Optional[nodes.Node]:
    #     return self.generic_visit(node)

    # {{ lookup('vars', 'ansible_' + ansible_interfaces[0]) }}
    # Call(node=Name(name='lookup', ctx='load'), args=[
    #   Const(value='vars'),
    #   Add(
    #     left=Const(value='ansible_'),
    #     right=Getitem(
    #       node=Name(name='ansible_interfaces', ctx='load'),
    #       arg=Const(value=0),
    #       ctx='load'
    #     )
    #   )
    # ], kwargs=[], dyn_args=None, dyn_kwargs=None)

    # {{lookup('vars', 'ansible_play_hosts', 'ansible_play_batch', 'ansible_play_hosts_all')}}
    # Call(node=Name(name='lookup', ctx='load'), args=[
    #   Const(value='vars'),
    #   Const(value='ansible_play_hosts'),
    #   Const(value='ansible_play_batch'),
    #   Const(value='ansible_play_hosts_all')
    # ], kwargs=[], dyn_args=None, dyn_kwargs=None)


class NamespaceAnsibleFactsTransform(Transform):
    id = "namespace-facts"
    shortdesc = "Adjust facts so they are accessed via ansible_facts namespace."
    description = (
        "Makes expressions access facts via ``ansible_facts.<fact>`` "
        "instead of ``ansible_<fact>`` which was deprecated in Ansible 2.5. "
        "Setting ``inject_facts_as_vars=False`` in ansible.cfg disables "
        "the legacy behavior of adding facts to the vars namespace. See: "
        "https://docs.ansible.com/ansible/latest/porting_guides/porting_guide_2.5.html#ansible-fact-namespacing"
    )
    version_added = "5.3"

    wants = AnsibleFactsNamespacingRule
    tags = AnsibleFactsNamespacingRule.tags

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
            do_wrap_template = "when" in match.yaml_path or match.yaml_path[-2:] == [
                "debug",
                "var",
            ]
            if do_wrap_template:
                target_template = "{{" + target_template + "}}"
        elif str(lintable.base_kind) == 'text/jinja2':
            target_parent = target_key = None
            target_template = data  # the whole file
            do_wrap_template = False
        else:  # unknown file type
            return

        ast = jinja_env.parse(target_template)
        ast = GetVarNodeTransformer().visit(ast)
        new_template = dump(node=ast, environment=jinja_env)

        if target_parent is not None:
            if do_wrap_template:
                # remove "{{ " and " }}" (dump always adds space w/ braces)
                new_template = new_template[3:-3]
            target_parent[target_key] = new_template
        else:
            with open(lintable.path.resolve(), mode='w', encoding='utf-8') as f:
                f.write(new_template)
            self._files_fixed.append(lintable.path)

        self._fixed(match)
