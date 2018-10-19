r"""JUnit XML formatter

The XML Schema of JUnit XML format:

- https://github.com/windyroad/JUnit-Schema/blob/master/JUnit.xsd
  [http://windyroad.com.au/2011/02/07/apache-ant-junit-xml-schema/]
"""
from __future__ import absolute_import
import datetime

from .base import BaseFormatter
from ..version import __version__ as VERSION


_JUNIT_XML_TESTCASE = """\
      <testcase id="{id}" name="{shortdesc}" classname="{filename}">
        <failure type="ERROR" message="{message}">
            rule_id={id}
            linenumber={linenumber}
            line={line}
        </failure>
      </testcase>
"""
_JUNIT_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<testsuites>
    <testsuite name="ansible-lint {version}" timestamp="{timestamp}" id="0"
               tests="{nrules}" time="{time}" errors="{nmatches}"
               skipped="{nskipped}">
      <properties>
        <property name="tool" value="ansible-lint"/>
        <property name="version" value="{version}"/>
      </properties>
      {testcases}
    </testsuite>
<testsuites>
"""
_TIMESTAMP = datetime.datetime.now().isoformat()


class JUnitXmlFormatter(BaseFormatter):

    def format(self, match, colored=False):
        """
        :param match: :class:`~ansiblelint.Match` object
        :param colored: It's completely ignored in this formatter
        """
        return _JUNIT_XML_TESTCASE.format(**match.as_dict())

    def formats(self, matches, colored=False, **kwargs):
        cases = super(JUnitXmlFormatter, self).formats(matches)
        info = dict(version=VERSION, timestamp=_TIMESTAMP,
                    nmatches=len(matches),
                    nrules=kwargs.get("nrules", 16),
                    time=kwargs.get("time", 0),
                    nskipped=kwargs.get("nskipped", 0),
                    testcases=cases)

        return _JUNIT_XML.format(**info)
