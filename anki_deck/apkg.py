"""
This module implements Anki deck generator.

Based on:

    https://github.com/ankidroid/Anki-Android/wiki/Database-Structure
    https://gist.github.com/sartak/3921255

:copyright: (c) 2015 by Sergey Kozlov
:license: MIT, see LICENSE for more details.
"""
import sys
import os
import os.path as op
import shutil
import codecs
import json
import tempfile
import sqlite3
import string
import random
import time
from hashlib import sha1
from .parser import CardsHandler


if sys.version_info[0] > 2:
    xrange = range

# -- SQL commands --------------------------------------------------------------

TABLES = [
    """
    CREATE TABLE cards (
        id              integer primary key,
        nid             integer not null,
        did             integer not null,
        ord             integer not null,
        mod             integer not null,
        usn             integer not null,
        type            integer not null,
        queue           integer not null,
        due             integer not null,
        ivl             integer not null,
        factor          integer not null,
        reps            integer not null,
        lapses          integer not null,
        left            integer not null,
        odue            integer not null,
        odid            integer not null,
        flags           integer not null,
        data            text not null
    )""",
    """
    CREATE TABLE col (
        id              integer primary key,
        crt             integer not null,
        mod             integer not null,
        scm             integer not null,
        ver             integer not null,
        dty             integer not null,
        usn             integer not null,
        ls              integer not null,
        conf            text not null,
        models          text not null,
        decks           text not null,
        dconf           text not null,
        tags            text not null
    )""",
    """
    CREATE TABLE graves (
        usn             integer not null,
        oid             integer not null,
        type            integer not null
    )""",
    """
    CREATE TABLE notes (
        id              integer primary key,
        guid            text not null,
        mid             integer not null,
        mod             integer not null,
        usn             integer not null,
        tags            text not null,
        flds            text not null,
        sfld            integer not null,
        csum            integer not null,
        flags           integer not null,
        data            text not null
    )""",
    """
    CREATE TABLE revlog (
        id              integer primary key,
        cid             integer not null,
        usn             integer not null,
        ease            integer not null,
        ivl             integer not null,
        lastIvl         integer not null,
        factor          integer not null,
        time            integer not null,
        type            integer not null
    )"""
]

INDEXES = [
    "CREATE INDEX ix_cards_nid on cards (nid)",
    "CREATE INDEX ix_cards_sched on cards (did, queue, due)",
    "CREATE INDEX ix_cards_usn on cards (usn)",
    "CREATE INDEX ix_notes_csum on notes (csum)",
    "CREATE INDEX ix_notes_usn on notes (usn)",
    "CREATE INDEX ix_revlog_cid on revlog (cid)",
    "CREATE INDEX ix_revlog_usn on revlog (usn)",
    "ANALYZE"
]


# -- Deck configs --------------------------------------------------------------

def make_card_field(name, order):
    """Create common card field struct with given name and order number."""
    return {
        'name': name,
        'media': [],
        'sticky': False,
        'rtl': False,
        'ord': order,
        'font': 'Arial',
        'size': 20
    }


LATEXPRE = r"""\documentclass[12pt]{article}
\special{papersize=3in,5in}
\usepackage[utf8]{inputenc}
\usepackage{amssymb,amsmath}
\pagestyle{empty}
\setlength{\parindent}{0in}
\begin{document}
"""

LATEXPOST = r"""\end{document}"""

CSS = r""".card {
  font-family: arial;
  font-size: 20px;
  text-align: center;
  color: black;
  background-color: white;
}
"""

FRONT_FMT = r"""{{Front}}
<br>
{{Transcription}}
<br>
{{Sound}}
"""

BACK_FMT = r"""{{FrontSide}}
<hr id=answer>
{{Back}}
"""

# conf is not very clear, took from existing db.
CONF = {
   'nextPos': 1,
   'estTimes': True,
   'activeDecks': [1],
   'sortType': 'noteFld',
   'timeLim': 0,
   'sortBackwards': False,
   'addToCur': True,
   'curDeck': 1,
   'newBury': True,
   'newSpread': 0,
   'dueCounts': True,
   'collapseTime': 1200,
   'curModel': None     # What is it?
}

MODEL = {
    'id': None,     # Filled by Deck
    'name': None,   # Filled by Deck
    'did': None,    # Filled by Deck
    'mod': None,    # Filled by Deck
    'vers': [],
    'tags': [],
    'usn': -1,
    'req': [[0, 'any', [0, 2, 3]]],
    'type': 0,
    'css': CSS,
    'sortf': 0,
    'latexPre': LATEXPRE,
    'latexPost': LATEXPOST,
    'tmpls': [
        {
            'name': 'Card 1',
            'qfmt': FRONT_FMT,
            'did': None,
            'bafmt': '',
            'afmt': BACK_FMT,
            'ord': 0,
            'bqfmt': ''
        }
    ],
    'flds': [
        make_card_field('Front', 0),
        make_card_field('Back', 1),
        make_card_field('Transcription', 2),
        make_card_field('Sound', 3)
    ]
}

DECK = {
    'id': None,     # Filled by Deck
    'name': None,   # Filled by Deck
    'mod': None,    # Filled by Deck
    'desc': '',
    'extendRev': 50,
    'usn': -1,
    'collapsed': False,
    'browserCollapsed': True,
    'newToday': [0, 0],
    'timeToday': [0, 0],
    'dyn': 0,
    'extendNew': 10,
    'conf': 1,
    'revToday': [0, 0],
    'lrnToday': [0, 0],
}

# -- Deck configs done ---------------------------------------------------------


def _guid(lenght):
    """Generate random GUID with the given `length`."""
    return ''.join(random.choice(string.printable) for x in xrange(lenght))


def card_to_flds(card):
    """Create fields string fro the given card."""
    parts = [card.word, card.info, card.transcription,
             '[sound:%s]' % card.sound if card.sound else '']
    return '\x1f'.join(parts)


def checksum(text):
    """Create checksum.

    Checksum is an integer representation of first 8 digits
    of sha1 hash of the given `text`.
    """
    return int(sha1(text.encode('utf-8')).hexdigest()[:8], 16)


class Deck(CardsHandler):
    """This class creates Anki `apkg` file."""
    def __init__(self, filename, sound_path, name):
        self.sound_path = sound_path
        self.outpath = tempfile.mkdtemp(prefix='anki_deck_', )
        self.filename = filename

        self.cursor = None
        self.media = {}  # to map input sound file names to result file names.

        # Initial deck data.
        self.deck_name = name
        self.epoch = int(time.time())
        self.epoch_ms = self.epoch * 1000
        self.model_id = int(time.time() * 1000)
        self.model_id_str = str(self.model_id)
        self.deck_id = self.model_id + 1
        self.deck_id_str = str(self.deck_id)
        self.note_id_start = self.deck_id + 1
        self.note_id = self.note_id_start

    def _run_sql(self, sql_list):
        for sql in sql_list:
            self.cursor.execute(sql)

    # Setup DB, create tables and set initial metadata.
    def _prepare_db(self):
        self.conn = sqlite3.connect(op.join(self.outpath, 'collection.anki2'))
        self.cursor = self.conn.cursor()
        self._run_sql(TABLES)
        self._set_metadata()
        self.conn.commit()

    # Build deck connection info and stores it in DB.
    def _set_metadata(self):
        CONF['curModel'] = self.model_id_str

        MODEL['id'] = self.model_id_str
        MODEL['name'] = 'AnkiDeck-%s-%d' % (self.deck_name, self.epoch)
        MODEL['did'] = self.deck_id
        MODEL['mod'] = self.epoch
        models = {self.model_id_str: MODEL}

        DECK['id'] = self.deck_id
        DECK['name'] = self.deck_name
        DECK['mod'] = self.epoch
        decks = {self.deck_id_str: DECK}

        # id,crt,mod,scm,ver,dty,usn,ls,conf,models,decks,dconf,tags
        vals = (1, self.epoch, self.epoch_ms, self.epoch_ms, 11, 0, 0, 0,
                json.dumps(CONF),
                json.dumps(models),
                json.dumps(decks),
                '{}',
                '{}')

        c = self.conn.cursor()
        c.execute("INSERT INTO col VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", vals)

    def start(self):
        if op.exists(self.filename):
            os.unlink(self.filename)

        self._prepare_db()

    def finish(self):
        # Save media info (about sound files which we copied in the handle().
        with codecs.open(op.join(self.outpath, 'media'), 'w', 'utf-8') as out:
            out.write(json.dumps(self.media))

        # Add cards for each word.
        gen = []
        for i in xrange(self.note_id - self.note_id_start):
            gen.append([self.note_id + i, self.note_id_start + i, self.deck_id,
                        0, self.epoch, -1, 0, 0, i + 1, 0, 0, 0, 0, 0, 0,
                        0, 0, ''])

        self.cursor.executemany(
            "INSERT INTO cards VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            gen)

        # Create required indexes.
        self._run_sql(INDEXES)
        self.conn.commit()
        self.conn.close()

        # Create result apkg file.
        import zipfile
        with zipfile.ZipFile(self.filename, 'w') as deck:
            for name in os.listdir(self.outpath):
                deck.write(op.join(self.outpath, name), name)

        # Try to cleanup - remove out temp dir where all stuff is generated.
        # It's ok if it fails so we skip all exceptions.
        try:
            shutil.rmtree(self.outpath)
        except Exception:
            pass

    def handle(self, card):
        if card.sound:
            # Map sound file to a number and copy it to the temp dir.
            index = len(self.media)
            self.media[index] = card.sound

            shutil.copy(op.join(self.sound_path, card.sound),
                        op.join(self.outpath, str(index)))

            # Put word with all required into to the DB record.
            vals = (
                self.note_id,
                _guid(10),
                self.model_id,
                self.epoch,
                -1,
                '',
                card_to_flds(card),
                card.word,
                checksum(card.word),
                0,
                ''
            )

            # id,guid,mid,mod,usn,tags,flds,sfld,csum,flags,data
            self.cursor.execute(
                "INSERT INTO notes VALUES (?,?,?,?,?,?,?,?,?,?,?)", vals)

            # This id is used as unique id for all records in the notes table
            # and later for IDs for records in cards table, see finish().
            self.note_id += 1

