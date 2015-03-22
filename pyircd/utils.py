
import unicodedata
from . import replies, exceptions

p = """
Taken from: http://www.fileformat.info/info/unicode/category/index.htm
[Cc]	Other, Control
[Cf]	Other, Format
[Cn]	Other, Not Assigned (no characters in the file have this property)
[Co]	Other, Private Use
[Cs]	Other, Surrogate
[LC]	Letter, Cased
[Ll]	Letter, Lowercase
[Lm]	Letter, Modifier
[Lo]	Letter, Other
[Lt]	Letter, Titlecase
[Lu]	Letter, Uppercase
[Mc]	Mark, Spacing Combining
[Me]	Mark, Enclosing
[Mn]	Mark, Nonspacing
[Nd]	Number, Decimal Digit
[Nl]	Number, Letter
[No]	Number, Other
[Pc]	Punctuation, Connector
[Pd]	Punctuation, Dash
[Pe]	Punctuation, Close
[Pf]	Punctuation, Final quote (may behave like Ps or Pe depending on usage)
[Pi]	Punctuation, Initial quote (may behave like Ps or Pe depending on usage)
[Po]	Punctuation, Other
[Ps]	Punctuation, Open
[Sc]	Symbol, Currency
[Sk]	Symbol, Modifier
[Sm]	Symbol, Math
[So]	Symbol, Other
[Zl]	Separator, Line
[Zp]	Separator, Paragraph
[Zs]	Separator, Space
"""

CATEGORY_NAMES = {
    'Lu': 'Letter, Uppercase',
    'Mc': 'Mark, Spacing Combining',
    'Sm': 'Symbol, Math',
    'Mn': 'Mark, Nonspacing',
    'Cs': 'Other, Surrogate',
    'Sc': 'Symbol, Currency',
    'Cf': 'Other, Format',
    'Zp': 'Separator, Paragraph',
    'Pd': 'Punctuation, Dash',
    'Lt': 'Letter, Titlecase',
    'LC': 'Letter, Cased',
    'Cn': 'Other, Not Assigned (no characters in '
          'the file have this property)',
    'Sk': 'Symbol, Modifier',
    'Nd': 'Number, Decimal Digit',
    'Co': 'Other, Private Use',
    'Zs': 'Separator, Space',
    'Pc': 'Punctuation, Connector',
    'Po': 'Punctuation, Other',
    'Pi': 'Punctuation, Initial quote (may behave '
          'like Ps or Pe depending on usage)',
    'Lo': 'Letter, Other',
    'Nl': 'Number, Letter',
    'Ll': 'Letter, Lowercase',
    'Zl': 'Separator, Line',
    'Lm': 'Letter, Modifier',
    'Pe': 'Punctuation, Close',
    'Me': 'Mark, Enclosing',
    'Pf': 'Punctuation, Final quote (may behave '
          'like Ps or Pe depending on usage)',
    'Cc': 'Other, Control',
    'So': 'Symbol, Other',
    'No': 'Number, Other',
    'Ps': 'Punctuation, Open'
}

ALLOWED_CATEGORIES_CHANNELNAME = {
    'LC', 'Ll', 'Lm', 'Lo', 'Lt', 'Lu',
    'Nd', 'Nl', 'No',
    'Pc', 'Pd', 'Pe', 'Po',
}
ALLOWED_CATEGORIES_NICKNAME = {
    'LC', 'Ll', 'Lm', 'Lo', 'Lt', 'Lu',
    'Nd', 'Nl', 'No',
    'Pc', 'Pd', 'Pe',
}

CHANNEL_INDICATORS = '#'


def check_for_categories(text, categories):
    if not text:
        raise ValueError('String is empty.')
    for char in text:
        category = unicodedata.category(char)
        if category not in categories:
            raise ValueError(
                'Character {!r} of category {} ({}) is not allowed'
                .format(char, category, CATEGORY_NAMES[category]))
    return True


def check_nickname(nickname):
    if nickname.startswith(CHANNEL_INDICATORS):
        raise exceptions.IrcError(
            replies.ERR_ERRONEUSNICKNAME,
            'Nickname starts with a channel indicator.')
    try:
        return check_for_categories(
            nickname, ALLOWED_CATEGORIES_NICKNAME)
    except ValueError as exc:
        raise exceptions.IrcError(
            replies.ERR_ERRONEUSNICKNAME,
            str(exc))


def check_channelname(channelname):
    if not channelname.startswith(CHANNEL_INDICATORS):
        raise exceptions.IrcError(
            replies.ERR_NOSUCHCHANNEL,
            'Channelname does not start with a channel indicator.')
    try:
        return check_for_categories(
            channelname[1:], ALLOWED_CATEGORIES_CHANNELNAME)
    except ValueError as exc:
        raise exceptions.IrcError(
            replies.ERR_NOSUCHCHANNEL,
            str(exc))


def parse_line(line):
    """Parse line into a 3-tuple containing:

    (prefix, command, parameters)
    prefix might be None, and parameters the empty list.
    """
    prefix = None
    if line[0:1] == ':':
        if ' ' in line:
            prefix, line = line.split(None, 1)
        else:
            prefix, line = line, ''
        prefix = prefix[1:]
    if ' ' in line:
        command, line = line.split(None, 1)
    else:
        command, line = line, ''
    if ' :' in line:
        param_line, trailing = line.split(' :', 1)
        param_line = param_line.strip()
        params = param_line.split()
        params.append(trailing)
    else:
        params = line.split()

    return prefix, command.upper(), params