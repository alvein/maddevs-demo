from collections.abc import Generator
from enum import Enum
from html.parser import HTMLParser
import logging
from typing import List, Set


# Default maximum value for each fragment
MAX_LEN = 4096

# Logger configuration, i.e. for Sentry
logger = logging.Logger(__name__)


class PositionNodeEnum(Enum):
    BREAKABLE = 'breakable'
    UNBREAKABLE = 'unbreakable'


class SplitMessageHTMLParser(HTMLParser):
    """Wrapper with required logic"""
    max_len: int = MAX_LEN
    debug: bool = False
    breakable_tags: Set[str] = {'p', 'b', 'strong', 'i', 'ul', 'ol', 'div', 'span'}
    fragments: List[str] = []

    _fragment: str = ''
    _fragment_len: int = 0
    _fragment_status = None

    _temporary_fragment: str = ''
    _temporary_fragment_len: int = 0

    _xpath: List[str] = []
    _xpath_with_attrs: List[str] = []

    def __init__(self, *, max_len: int = MAX_LEN, debug: bool = False, convert_charrefs: bool = True):
        self.max_len = max_len
        self.debug = debug
        self.fragments = []
        super().__init__(convert_charrefs=convert_charrefs)

    def handle_starttag(self, tag, attrs):
        """Handle start tag"""
        self._xpath.append(tag)
        self._xpath_with_attrs.append(self.get_starttag_text())

        # Found unbreakable block, just collecting the data
        if not self._is_wrapping_allowed:
            self._temporary_fragment += self.get_starttag_text()
            self._temporary_fragment_len += len(self.get_starttag_text()) + len(tag) + 3
            self._fragment_status = PositionNodeEnum.UNBREAKABLE
            return super().handle_starttag(tag, attrs)

        self._fragment_status = PositionNodeEnum.BREAKABLE
        self._fragment += self.get_starttag_text()

        # Get length for the current fragment, at same time count the ending tag
        _tag_length = len(self.get_starttag_text()) + len(tag) + 3
        if self._fragment_len + _tag_length > self.max_len:
            self._finalize_fragment()

        self._fragment_len += _tag_length
        return super().handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        """Handle close tag"""
        if self._fragment_status == PositionNodeEnum.UNBREAKABLE:
            self._temporary_fragment += f'</{tag}>'

        else:
            self._fragment += f'</{tag}>'

        # Cut full and short xpath
        self._xpath.pop(-1)
        self._xpath_with_attrs.pop(-1)

        # If we may add temporary fragment to the existed one - try it
        if self._is_wrapping_allowed:
            self._fragment_status = PositionNodeEnum.BREAKABLE
            self._dump_fragment()

        return super().handle_endtag(tag)

    def handle_data(self, data) -> None:
        """Handling the text node"""
        # Extend the temporary fragment
        if self._fragment_status == PositionNodeEnum.UNBREAKABLE:
            self._temporary_fragment += data
            self._temporary_fragment_len += len(data)
            return super().handle_data(data)

        # Checking if we should split the text node or not
        if self._fragment_len + len(data) > self.max_len:
            # Split the text node
            self._fragment += data[:self.max_len - self._fragment_len]
            data = data[self.max_len - self._fragment_len:]

            self._fragment_len = len(self._fragment)
            self._finalize_fragment()

        self._fragment += data
        self._fragment_len += len(data)

        return super().handle_data(data)

    def _dump_fragment(self) -> None:
        """Dump the fragment if need and it is possible"""
        if self._fragment_len + self._temporary_fragment_len < self.max_len:
            # Extend the existed fragment
            self._fragment += self._temporary_fragment
            self._fragment_len += self._temporary_fragment_len

            # Reset the temporary fragment
            self._temporary_fragment_len = 0
            self._temporary_fragment = ''

        elif self._fragment_len + self._temporary_fragment_len >= self.max_len:
            self._finalize_fragment()

    @property
    def _is_wrapping_allowed(self) -> bool:
        """Checking if we may split current fragment or not"""
        return not bool(set(self._xpath) - self.breakable_tags)

    def _finalize_fragment(self) -> None:
        """Finalize the fragment"""
        for tag in self._xpath.copy()[::-1]:
            self._fragment += f'</{tag}>'

        # Saving the fragment
        if self._fragment:
            self.fragments.append(self._fragment)

        # Show the verbose to stdout if needed
        if self.debug:
            print(f'-- fragment #{len(self.fragments)}: {self._fragment_len} chars --\n{self._fragment}')

        # Closing the fragment using xpath
        self._fragment = ''
        self._fragment_len = 0
        for position, tag in enumerate(self._xpath_with_attrs):
            self._fragment += tag
            self._fragment_len += len(tag) + len(self._xpath[position]) + 3

        # Restoring the structure
        self._fragment += self._temporary_fragment
        self._fragment_len += self._temporary_fragment_len

        # Reset temporary part
        self._temporary_fragment = ''
        self._temporary_fragment_len = 0

        if self._fragment_len > self.max_len:
            logger.exception(f'Unsplittable fragment {len(self.fragments) + 1}')
            raise Exception

    def feed(self, data) -> None:
        """Feed the HTML"""
        super().feed(data)

        # Dump the rest data as a new fragment
        if self._fragment_len or self._temporary_fragment_len:
            self._finalize_fragment()

    def get_fragments(self) -> Generator[str]:
        """Get fragments"""
        for fragment in self.fragments:
            yield fragment


def split_message(source: str, max_len: int) -> Generator[str]:
    """Splits the original message (`source`) into fragments of the specified length (`max_len`)."""
    parser = SplitMessageHTMLParser(max_len=max_len)
    parser.feed(source)

    return parser.get_fragments()