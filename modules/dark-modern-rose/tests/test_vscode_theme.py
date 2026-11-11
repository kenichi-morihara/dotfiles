"""Token colours of the Dark Modern Rose VS Code theme (TextMate pass).

Fixtures are tokenized with the vscode-textmate engine bundled in the installed
VS Code app plus the grammars that are active in the editor (ruby-lsp, Rails
Syntax, this extension's injections), so a failure here means the editor shows
the wrong colour. Semantic tokens from ruby-lsp are covered by
tests/vscode_theme/e2e.mjs instead.
"""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
EXT = Path(os.environ.get(
    'DARK_MODERN_ROSE_EXT',
    ROOT / 'home/dot_vscode/extensions/kenichi-morihara.dark-modern-rose-1.0.0'))
VSCODE_APP = Path(os.environ.get('VSCODE_APP', '/Applications/Visual Studio Code.app/Contents/Resources/app'))
EXTENSIONS = Path(os.environ.get('VSCODE_EXTENSIONS', Path.home() / '.vscode/extensions'))
TOKENIZE = ROOT / 'tests/vscode_theme/tokenize.mjs'
FIXTURES = ROOT / 'tests/fixtures/vscode_theme'
SAMPLES = ROOT / 'home/dot_vscode/extensions/kenichi-morihara.dark-modern-rose-1.0.0/samples'

# Colour roles of the theme design. Tests name roles; each theme maps them to colours.
KEYWORD = 'keyword'      # structure and other keywords: def/class/module/do/end, const/function, self/this, ->/=>, and/or/not, typeof/new
DECL = 'decl'            # Rails/visibility declarations, decorators, HTML/JSX tags
CLASS = 'class'          # classes, modules, types, interfaces, React components
CONSTANT = 'constant'    # UPPER constants, enum members (same colour as variables; the case tells them apart)
VARIABLE = 'variable'    # confirmed variables, parameters, properties
SYMBOL = 'symbol'        # symbols, hash/object keys, HTML/JSX attributes
FUNCTION = 'function'    # method/function definitions and calls
PLAIN = 'plain'          # operators, punctuation, unresolved identifiers
STRING = 'string'
COMMENT = 'comment'
LITERAL = 'literal'      # true/false/nil/null, numbers
CONTROL = 'control'      # keyword.control (as in VS Code Dark Modern) minus Ruby block structure: if/else/case/rescue, return/raise, import/export

BASE_PALETTE = {
    KEYWORD: '#BD93F9', DECL: '#DC92B7', CLASS: '#62E1C7', CONSTANT: '#74C4FF',
    VARIABLE: '#74C4FF', SYMBOL: '#A6B4EE', FUNCTION: '#F1E4A6', PLAIN: '#E3E1ED',
    STRING: '#FFAE92', COMMENT: '#8DBB7A', LITERAL: '#F0A04B', CONTROL: '#F78FD9',
}

def _tokenize(path, root_scope, theme):
    out = subprocess.run(['node', str(TOKENIZE), str(EXT), root_scope, str(path), theme],
                         check=True, capture_output=True, text=True)
    return json.loads(out.stdout)


def _line(lines, needle, nth=0):
    hits = [toks for toks in lines if needle in ''.join(t['text'] for t in toks)]
    if len(hits) <= nth:
        raise AssertionError(f'fixture line not found: {needle!r}')
    return hits[nth]


def _color_of(tokens, word):
    pattern = re.compile(r'(?<![\w@$:?!])' + re.escape(word) + r'(?![\w?!])')
    for t in tokens:
        if pattern.search(t['text']):
            return t['color'], t['scopes'][1:]
    raise AssertionError(f'token {word!r} not found in {"".join(t["text"] for t in tokens)!r}')


@unittest.skipUnless(shutil.which('node') and (VSCODE_APP / 'node_modules.asar').exists()
                     and any(EXTENSIONS.glob('shopify.ruby-lsp-*')),
                     'VS Code app, node and the ruby-lsp extension are required')
class ThemeTestCase(unittest.TestCase):
    fixture = None
    root_scope = 'source.ruby'
    theme = 'dark-modern-rose.json'
    palette = BASE_PALETTE

    @classmethod
    def setUpClass(cls):
        cls.lines = _tokenize(cls.fixture, cls.root_scope, cls.theme) if cls.fixture else []

    def assertColors(self, expectations):
        for needle, word, role, *nth in expectations:
            with self.subTest(line=needle, token=word):
                color, scopes = _color_of(_line(self.lines, needle, *nth), word)
                self.assertEqual(color, self.palette[role],
                                 f'{word!r} in {needle!r} should be {role}; scopes {scopes}')

    def test_comments_only_use_comment_color(self):
        if not self.lines:
            self.skipTest('no fixture')
        leaks = [(''.join(x['text'] for x in toks), t['text'], t['color'])
                 for toks in self.lines for t in toks if t['text'].strip()
                 and any('comment' in s or 'meta.type.signature.rbs' in s for s in t['scopes'])
                 and t['color'] != self.palette[COMMENT]]
        self.assertEqual(leaks, [])


class RegressionTests(ThemeTestCase):
    fixture = FIXTURES / 'regressions.rb'

    def test_inline_rbs_comments(self):
        self.assertColors([
            ('DAYS = "days"', '"days" -- 日', COMMENT),
            ('KEYS = [DAYS]', 'Array', COMMENT),
            ('KEYS = [DAYS]', 'hours', COMMENT),
        ])

    def test_if_else_are_control_end_is_structure_and_booleans_are_literals(self):
        self.assertColors([
            ('if true', 'if', CONTROL), ('if true', 'true', LITERAL),
            ('else if false', 'else if', CONTROL), ('else if false', 'false', LITERAL),
            ('    end', 'end', KEYWORD),
        ])

    def test_endless_def_body_is_an_expression_not_parameters(self):
        self.assertColors([
            ('def load! = nil', 'load!', FUNCTION), ('def load! = nil', 'nil', LITERAL),
            ('def ready? = true', 'true', LITERAL),
            ('def dist = Math.sqrt(2)', 'Math', CLASS), ('def dist = Math.sqrt(2)', 'sqrt', FUNCTION),
            ('def name=(value)', 'value', VARIABLE),
            ('private def helper = nil', 'private', DECL), ('private def helper = nil', 'nil', LITERAL),
        ])

    def test_rescue_binding_is_a_variable(self):
        self.assertColors([
            ('rescue Datamart::Error::LoadError => e', 'e', VARIABLE),
            ('rescue Datamart::Error::LoadError => e', 'LoadError', CLASS),
            ('rescue Foo, Bar::Baz => err', 'Foo', CLASS),
            ('rescue Foo, Bar::Baz => err', 'err', VARIABLE),
        ])

    def test_variables_are_colored_only_when_certain(self):
        self.assertColors([
            ('d_tables = []', 'd_tables', VARIABLE),
            ('@name = value', 'name', VARIABLE),
            ('items.each', 'proc', VARIABLE),
            # Lambda parameters are declared like block/def parameters.
            ('->(status)', 'status', VARIABLE), ('->(status)', 'by_status', SYMBOL),
            ('->(status)', '->', KEYWORD), ('->(status)', 'where', FUNCTION),
            ('filter = ->(order', 'order', VARIABLE), ('filter = ->(order', 'rest', VARIABLE),
            ('filter = ->(order', 'key', VARIABLE), ('filter = ->(order', '1', LITERAL),
            ('nested = ->(a', '->', KEYWORD),
            # Hash value at end of line could be a method call: leave it unresolved.
            (':c => d', 'd', PLAIN),
            # Bare identifiers need ruby-lsp to know whether they are locals or calls.
            ('BigquerySqlParser.extract', 'custom_variable_expanded_query', PLAIN),
        ])

    def test_declarations(self):
        self.assertColors([
            ('attr_reader :transfer_record', 'attr_reader', DECL),
            ('private # trailing comment', 'private', DECL),
            ('items.each', 'each', FUNCTION),
        ])
        # A bare `scope` line is a local variable, not the Rails `scope` declaration.
        bare_scope = [toks for toks in self.lines if ''.join(t['text'] for t in toks).strip() == 'scope']
        self.assertEqual(_color_of(bare_scope[0], 'scope')[0], self.palette[PLAIN])

    def test_statements_that_leave_the_scope_are_control_keywords(self):
        self.assertColors([
            ('raise e', 'raise', CONTROL),
            ('items.each { |x| next', 'next', CONTROL), ('items.each { |x| next', 'break', CONTROL),
            ('items.each { |x| next', 'if', CONTROL),
            ('retry if attempts', 'retry', CONTROL), ('exit! 1', 'exit!', CONTROL), ('abort "bye"', 'abort', CONTROL),
            ('throw :done', 'throw', CONTROL),
            # Rails responses stay helper calls (ruby-lsp repaints bare calls as methods anyway).
            ('redirect_to root_path and return', 'redirect_to', FUNCTION),
            ('redirect_to root_path and return', 'return', CONTROL),
            ('redirect_to root_path and return', 'root_path', FUNCTION),
            ('render json: {}, status: :ok', 'render', FUNCTION),
            # Names that merely contain the words, or calls on a receiver, are not exits.
            ('return_value = obj.raise', 'return_value', VARIABLE),
            ('return_value = obj.raise', 'raise', FUNCTION),
            ('render_later = 1', 'render_later', VARIABLE),
        ])

    def test_embedded_sql_and_data_sections_are_not_ruby(self):
        self.assertColors([
            ('SELECT * FROM Users', 'Users', PLAIN),
            ('=end trailing Foo end', 'Foo', COMMENT),
            ('__END__', '__END__', KEYWORD),
            ('Foo end validates :x', 'validates', COMMENT),
        ])


class ShowcaseRubyTests(ThemeTestCase):
    fixture = SAMPLES / 'showcase.rb'

    def test_rails_model(self):
        self.assertColors([
            ('class Order <', 'class', KEYWORD), ('class Order <', 'ApplicationRecord', CLASS),
            ('include Searchable', 'include', DECL), ('include Searchable', 'Auditable', CLASS),
            ('STATUSES =', 'STATUSES', CONSTANT), ('TAX_RATE = 0.1', '0.1', LITERAL),
            ('belongs_to :user', 'belongs_to', DECL), ('belongs_to :user', 'user', SYMBOL),
            ('belongs_to :user', 'true', LITERAL),
            ('has_many :line_items', '->', KEYWORD), ('has_many :line_items', 'order', FUNCTION),
            ('enum :status', 'enum', DECL), ('normalizes :email', 'normalizes', DECL),
            ('validates :email', 'URI', CLASS), ('validates :email', 'EMAIL_REGEXP', CONSTANT),
            ('with_options if:', 'with_options', DECL), ('with_options if:', 'do', KEYWORD),
            ('scope :recent', 'scope', DECL), ('scope :recent', 'where', FUNCTION),
        ])

    def test_ruby_syntax(self):
        self.assertColors([
            ('subtotal = line_items.sum', 'subtotal', VARIABLE), ('subtotal = line_items.sum', '_1', VARIABLE),
            ('Order ##{id}', 'Order #', STRING), ('Order ##{id}', 'name', FUNCTION),
            ('def process!', 'process!', FUNCTION), ('def process!', 'opts', VARIABLE),
            ('raise ArgumentError', 'ArgumentError', CLASS), ('raise ArgumentError', 'raise', CONTROL),
            ('in { mode: :fast', 'in', CONTROL), ('n.times', 'yield', CONTROL),
            ('lock!', 'lock!', FUNCTION),
            ('rescue ActiveRecord::RecordInvalid', 'e', VARIABLE),
            ('errors.add(:base', 'and', KEYWORD),
            ('def to_param', '"', STRING),
            ('self.total = total', 'self', KEYWORD),
        ])

    def test_controller_and_job(self):
        self.assertColors([
            ('before_action :authenticate_user!', 'before_action', DECL),
            ('rescue_from ActiveRecord::RecordNotFound', 'RecordNotFound', CLASS),
            ('format.json', 'render', FUNCTION),
            ('head :not_found and return', 'head', FUNCTION),
            ('head :not_found and return', 'return', CONTROL),
            ('queue_as :default', 'queue_as', DECL), ('retry_on Timeout::Error', '3', LITERAL),
        ])


class ShowcaseErbTests(ThemeTestCase):
    fixture = SAMPLES / 'showcase.html.erb'
    root_scope = 'text.html.erb'

    def test_erb(self):
        self.assertColors([
            ('<%# 注文一覧', 'validates', COMMENT),
            ('<div class="orders', 'div', DECL), ('<div class="orders', 'class', SYMBOL),
            ('<div class="orders', 'empty?', FUNCTION),
            ('link_to order.code', 'link_to', FUNCTION), ('link_to order.code', 'order_path', FUNCTION),
            ('render "line_items"', 'true', LITERAL),
            ('render "line_items"', 'render', FUNCTION),
            ('<% end %>', 'end', KEYWORD),
            ('form_with model:', 'orders_path', FUNCTION),
        ])



class ShowcaseTsxTests(ThemeTestCase):
    fixture = SAMPLES / 'showcase.tsx'
    root_scope = 'source.tsx'

    def test_declarations_and_types(self):
        self.assertColors([
            ('import React,', 'import', CONTROL), ('import React,', 'from', CONTROL),
            ('export const API_URL', 'export', CONTROL), ('export const API_URL', 'const', KEYWORD),
            ('enum Status', 'Status', CLASS), ('Open = "open"', 'Open', CONSTANT),
            ('interface OrderProps', 'OrderProps', CLASS), ('interface OrderProps', 'T', CLASS),
            ('title?: string', 'string', CLASS), ('title?: string', 'title', SYMBOL),
            ('private readonly cache', 'cache', SYMBOL),
            ('class OrderStore', 'OrderStore', CLASS),
            ('private readonly cache', 'private', KEYWORD), ('private readonly cache', 'new', KEYWORD),
            ('static instance', 'null', CLASS),
        ])

    def test_declared_keys_look_like_hash_keys(self):
        # Object keys, type members and class fields where they are declared; `obj.key` stays a variable.
        self.assertColors([
            ('defaultFilter = {', 'status', SYMBOL), ('defaultFilter = {', 'limit', SYMBOL),
            ('defaultFilter = {', '10', LITERAL),
            ('type Order = {', 'total', SYMBOL), ('o.total > 0', 'total', VARIABLE),
        ])

    def test_functions_and_expressions(self):
        self.assertColors([
            ('async load(', 'async', KEYWORD), ('async load(', 'load', FUNCTION),
            ('async load(', 'id', VARIABLE),
            ('this.cache.get', 'this', KEYWORD), ('this.cache.get', 'get', FUNCTION),
            ('this.cache.get', 'cache', VARIABLE),
            ('useState<string>', 'useState', FUNCTION), ('useState<string>', 'string', CLASS),
            ('let count = 0', 'count', VARIABLE), ('let count = 0', '0', LITERAL),
            ('count += visible.length', 'length', VARIABLE),
            ('typeof window', 'typeof', KEYWORD), ('setQuery(null', 'null', LITERAL),
            ('const handleClick', 'handleClick', FUNCTION), ('const handleClick', '=>', KEYWORD),
        ])

    def test_template_interpolation_matches_ruby(self):
        self.assertColors([
            ('await fetch(`', '${', KEYWORD), ('await fetch(`', '/orders/', STRING),
            ('await fetch(`', 'id', VARIABLE),
        ])

    def test_jsx(self):
        self.assertColors([
            ('<section className', 'section', DECL), ('<section className', 'className', SYMBOL),
            ('<section className', '"', STRING),
            ('<OrderRow key', 'OrderRow', CLASS), ('<OrderRow key', 'onClick', SYMBOL),
            ('<OrderRow key', 'false', LITERAL), ('<OrderRow key', 'handleClick', FUNCTION),
            ('<h1>{title}', 'h1', DECL),
        ])


class ShowcaseTsTests(ThemeTestCase):
    fixture = SAMPLES / 'showcase.ts'
    root_scope = 'source.ts'

    def test_typescript(self):
        self.assertColors([
            ('export type Result', 'Result', CLASS), ('export type Result', 'true', CLASS),
            ('implements Repository', 'Repository', CLASS),
            ('@decorate', '@', DECL),
            ('error instanceof SyntaxError', 'instanceof', KEYWORD),
            ('error instanceof SyntaxError', 'SyntaxError', CLASS),
            ('value is T', 'is', KEYWORD),
            ('Object.keys', 'a', SYMBOL), ('Object.keys', 'satisfies', CONTROL),
        ])


if __name__ == '__main__':
    unittest.main()
