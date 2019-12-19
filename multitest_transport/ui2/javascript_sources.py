# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Development web sources gatherer-- providing JavaScript on the fly.

"""

import os
import re
import string
import six


_RE_NONASCII = re.compile(r'[^\000-\177]')
_GOOG_MODULE_PATTERN = re.compile(br'^\s*goog\.module\s*\(\s*[\'\"]',
                                  re.MULTILINE)

# Escape sequences for char and string literals
_JAVA_ESCAPE_MAP = {
    '\b': '\\b',
    '\t': '\\t',
    '\n': '\\n',
    '\f': '\\f',
    '\r': '\\r',
    '"': '\\"',
    "'": "\\'",
    '\\': '\\\\',
}

# Fill the escape map with ASCII characters from 0-128
for i in range(128):
  c = chr(i)
  if c not in _JAVA_ESCAPE_MAP and c not in string.printable:
    _JAVA_ESCAPE_MAP[c] = '\\%03o' % i
# Compile characters-to-be-escaped into regex for matching
_JAVA_ESCAPE_RE = re.compile('|'.join(
    [re.escape(c) for c in _JAVA_ESCAPE_MAP.keys()]))


def compile_js_from_manifest(manifest_path):
  """Compiles JavaScript from web_sources manifest file.

  This function takes every JavaScript file from the manifest, concatenates
  them, and compile them to a string using js_eval_compiler.
  Args:
    manifest_path: path to MF file to read.

  Returns:
    A string containing concatenated javascript.
  """
  inputs = []

  for js_rel_path in _read_manifest(manifest_path):
    js_rel_path = os.path.join('google3', js_rel_path)
    with open(js_rel_path, 'r') as jsf:
      inputs.append((js_rel_path, jsf.read()))
  return _compile(inputs)


def _read_manifest(manifest_path):
  """Reads a web_sources manifest file.

  Args:
    manifest_path: Absolute path to manifest file.

  Yields:
    paths strings, each corresponding to one line in the manifest.
  """
  with open(manifest_path, 'r') as mf:
    for line in mf:
      yield line.strip()


def _compile(inputs, source_url_root='http://jseval/'):
  """Compiler that wraps all file contents in eval() or goog.loadModule.


  Args:
    inputs: A list of tuples where the first item is the .js file path
        relative to the root of the server (this will be used - with a fake
        URL prefix, required to make the feature work - as the sourceURL=
        parameter of the corresponding eval() statement) and the second item
        is the .js file content. A dict cannot be used here as ordering of
        files must be preserved.
    source_url_root: The domain root under which .js files will appear as
        resources of the site.

  Returns:
    The compiled source as a JS string.
  """
  result = ['var CLOSURE_NO_DEPS = true;\n\n']
  for (path, content) in inputs:
    result.append('// ')
    result.append(path)
    if _GOOG_MODULE_PATTERN.search(content):
      result.append('\ngoog.loadModule(\"')
    else:
      result.append('\neval(\"')
    if isinstance(content, six.text_type):
      result.append(_escape(content))
    else:
      result.append(_escape(content.decode('utf-8')))
    result.append('\\n//# sourceURL=')
    result.append(source_url_root)
    result.append(_escape(path))
    result.append('\");\n\n')
  return ''.join(result)


def _escape(text):
  """Escapes a string so it can be inserted in a Java string or char literal.


  Escapes unprintable and non-ASCII characters.  The resulting string consists
  entirely of ASCII characters.

  Args:
    text: string to be escaped

  Returns:
    escaped string
  """
  # Escape all unprintable characters in default locale
  result = _JAVA_ESCAPE_RE.sub(lambda m: _JAVA_ESCAPE_MAP[m.group(0)], text)
  # Replace remaining non-ASCII characters with their unicode escape sequence
  return _RE_NONASCII.sub(lambda m: '\\u%04x' % ord(m.group(0)), result)
