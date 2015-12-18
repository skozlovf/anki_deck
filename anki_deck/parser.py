"""
This module XDXF parser and tools.

:copyright: (c) 2015 by Sergey Kozlov
:license: MIT, see LICENSE for more details.
"""
import sys
import os.path as op
import codecs
import logging
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class Card(object):
    """This class represents a card."""
    def __init__(self):
        self.word = None
        self.info = []
        self.transcription = None
        self.sound = None


class CardsHandler(object):
    """Base class for the cards handlers.

    See:
        :func:`get_cards`.
    """
    def start(self):
        """This method gets called by the :func:`get_cards` before
        reading dict file.
        """
        pass

    def finish(self):
        """
        This method gets called by the :func:`get_cards` after parsing
        is finished.
        """
        pass

    def handle(self, card):
        """Main card handler logic. Must be reimplemented in subclass."""
        raise NotImplemented


class ParseError(Exception):
    pass


def _set_transcription(card):
    """Find transcription and set it to the `transcription`.

    If transcription is placed at very beginning then remove it.
    """
    for i, x in enumerate(card.info):
        first = x.find('[')
        if first != -1:
            last = x.index(']')
            card.transcription = x[first:last + 1]
            if not i:
                card.info[i] = x[last + 1:]
            break


def _xml_cleanup(card):
    """Cleanup card translation XML.

    It removes all examples (`<ex>` tags) and unwraps nested `<blockquote>`.

    Returns:
        One-line XML unicode string.
    """
    text = '<ar>' + ' '.join(card.info)
    soup = BeautifulSoup(text.replace('&apos;', "'"), 'html.parser')
    for tag in soup.find_all('ex'):
        tag.decompose()

    # Remove empty tags. There may be some because we removed <ex> nodes.
    for tag in soup.find_all('blockquote'):
        if not tag.text:
            tag.decompose()

    # Convert this:
    #
    # <blockquote>
    #   <blockquote>
    #       <blockquote>
    #           ...
    #       </blockquote>
    #   </blockquote>
    # </blockquote>
    #
    # to:
    #
    # <blockquote>
    #   ...
    # </blockquote>

    # Build list of 'deepest' <blockquote> nodes.
    lst = [x for x in soup.find_all('blockquote') if
           x.contents[0].name != 'blockquote']

    # Unwrap <blockquote> if its parent is also <blockquote>.
    for tag in lst:
        while tag.parent.name == 'blockquote':
            tag.parent.unwrap()

    return unicode(soup).replace('\n', ' ')


def parse_cards(word_list, dict_file, sound_path):
    """Yields a Card for each word in the `word_list`.

    Args:
        word_list: List of words for which return cards.
        dict_file: Filename of the dict in the xdxf format.
        sound_path: Path to dir with ogg audio files with names `<word>.ogg`.

    Returns:
        Card object.
    """
    # Read dict file liny by line and search lines:
    #  * '<ar><k>...' - starts a word translation info
    #  * '...</ar>' - ends translation info
    with codecs.open(dict_file, 'r', 'utf-8') as d:
        card = None

        for line in d:
            # Translation info started.
            # We extract word from the line '<ar><k>[word]</k>'
            # TODO: is line format always '<ar><k>[word]</k>'?
            if not card and line.startswith('<ar><k>'):
                text = line[7:-5].lower().replace('&apos;', "'")
                if text in word_list:
                    card = Card()
                    card.word = text
                    card.sound = card.word + '.ogg'
                    word_list.remove(text)

            # If word is started then we add lines to the info list.
            elif card:
                card.info.append(line)

                # If this line ends word translation then save all data
                # to the flashcard.
                if line.endswith('</ar>\n'):
                    _set_transcription(card)
                    card.info = _xml_cleanup(card)

                    yield card
                    card = None

                    # Stop parsing if all words are extracted.
                    if not word_list:
                        break


def get_cards(words_file, dict_file, sound_path, card_handler):
    """Run `card_handler` on cards for `words_file` extracted from `dict_file`.

    Args:
        words_file: Words filename.
        dict_file: Filename of the dict in the xdxf format.
        sound_path: Path to dir with ogg audio files with names `<word>.ogg`.
        card_handler: :class:`CardsHandler` instance.
    """
    try:
        with open(words_file, 'r') as words:
            word_list = set(x.strip().lower() for x in words if x)

        if not word_list:
            raise ParseError('Empty words file')

        need_audio = op.exists(sound_path)
        card_handler.start()

        for card in parse_cards(word_list, dict_file, sound_path):
            if need_audio:
                path = op.join(sound_path, card.sound)
                if not op.exists(path):
                    card.sound = None
                    logger.warning("Missing sound %s" % path)
            card_handler.handle(card)
        card_handler.finish()

        if word_list:
            logger.warning('Missing translations: %s', ', '.join(word_list))
    except IOError as e:
        logger.error(e)
        sys.exit(1)
