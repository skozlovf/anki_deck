"""
This module implements plain text flashcards generator for Anki.

:copyright: (c) 2015 by Sergey Kozlov
:license: MIT, see LICENSE for more details.
"""
import codecs
from .parser import CardsHandler


class FlashcardsWriter(CardsHandler):
    """This class writes cards to a flashcards file which may be imported to
    Anki desk.

    File format (tab separated)::

        <word> <translations> <transcription> <sound>

    To import flashcards file create card with fields:

    * Front
    * Back
    * Transcription
    * Sound

    Front Template::

        {{Front}}
        <br>
        {{Transcription}}
        <br>
        {{Sound}}

    Back Template::

        {{FrontSide}}
        <hr id=answer>
        {{Back}}

    Then go File->Import, select flashcards and properly map fields.
    """
    def __init__(self, filename, separator='\t'):
        self.separator = separator
        self.filename = filename
        self.out = None

    def start(self):
        self.out = codecs.open(self.filename, 'w', 'utf-8')

    def finish(self):
        if self.out:
            self.out.close()

    def handle(self, card):
        parts = [card.word, card.info, card.transcription,
                 '[sound:%s]' % card.sound if card.sound else '']
        self.out.write(self.separator.join(parts))
        self.out.write('\n')

