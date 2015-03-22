
from collections import namedtuple
import unicodedata
import re
from . import replies, exceptions

Prefix = namedtuple('prefix', 'nick user host')
prefix_pattern = re.compile(
    r'^(?P<nick>[^!@]+)'
    r'(?:!(?P<user>[^@]+))?'
    r'(?:@(?P<host>[^@]+))?$'
)


# Taken from: http://www.fileformat.info/info/unicode/category/index.htm
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
            [nickname, 'Nickname starts with a channel indicator.'])
    try:
        return check_for_categories(
            nickname, ALLOWED_CATEGORIES_NICKNAME)
    except ValueError as exc:
        raise exceptions.IrcError(
            replies.ERR_ERRONEUSNICKNAME,
            [nickname, str(exc)])


def check_channelname(channelname):
    if not channelname.startswith(CHANNEL_INDICATORS):
        raise exceptions.IrcError(
            replies.ERR_NOSUCHCHANNEL,
            [channelname,
             'Channelname does not start with a channel indicator.'])
    try:
        return check_for_categories(
            channelname[1:], ALLOWED_CATEGORIES_CHANNELNAME)
    except ValueError as exc:
        raise exceptions.IrcError(
            replies.ERR_NOSUCHCHANNEL,
            [channelname, str(exc)])


def normalize_name(nick_or_channel):
    return unicodedata.normalize('NFC', nick_or_channel)


def split_prefix(prefix):
    if prefix is None:
        return Prefix(None, None, None)
    match = prefix_pattern.match(prefix)
    if match is None:
        raise exceptions.IrcError(
            replies.ERR_BADMASK,
            [prefix, 'Invalid prefix'])
    return Prefix(*match.groups())


def parse_line(line):
    """Parse line into a 3-tuple containing:

    (prefix_mask, command, parameters)
    prefix_mask might be None, and parameters the empty list.
    """
    prefix_mask = None
    if line[0:1] == ':':
        if ' ' in line:
            prefix_mask, line = line.split(None, 1)
        else:
            prefix_mask, line = line, ''
        prefix_mask = prefix_mask[1:]
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

    return Message(prefix_mask, command.upper(), params)


class Message:
    def __init__(self, prefix_mask, command, params):
        self.mask = prefix_mask
        self.prefix = split_prefix(prefix_mask)
        self.command = command
        self.params = params

    def __repr__(self):
        if self.command == 'PRIVMSG':
            return '[MSG] <{}@{}> {}'.format(
                self.prefix.nick, *self.params)
        elif self.command == 'NOTICE':
            return '[NOTICE] <{}@{}> {}'.format(
                self.prefix.nick, *self.params)
        else:
            if self.mask is None:
                return '[*] {}: {}'.format(
                    self.command, self.params
                )
            else:
                return '[*] {}: {} {}'.format(
                    self.command, self.prefix, self.params
                )
