anki_deck
=========

``anki_deck`` is a simple tool to generate Anki flashcards from the
xdxf dictionaries.

Based on
https://www.reddit.com/r/Anki/comments/34imaw/export_from_goldendict_to_anki_deck_working_method/

To use ``anki_deck`` you need the following data:

* XDXF dictionary file.
* Words file - list of words you want to put in flashcards.
  It's just a plain file with one word per line::

    someword
    another

* Audio samples (optional) in ``.ogg`` format.

``anki_deck`` can create plain text flashcards file or ``.apkg`` deck.
Both of them may be imported by Anki.
To import text file you will need to create a card with fields and deck
``.apkg`` may be imported without extra actions.

You may use it without install like::

    python -m anki_deck.cli ....
    
Or install with ``setyp.py`` and use::

    anki_deck ...

Usage::
    
    # To generate flashcards text file
    anki_deck -d /<path>/<to>/dict.xdxf -a /<path>/<to>/audio -w mywords.txt txt
    
    # To generate a deck
    anki_deck -d /<path>/<to>/dict.xdxf -a /<path>/<to>/audio -w mywords.txt deck MyDeck  # or MyDeck.apkg
    anki_deck -d /<path>/<to>/dict.xdxf -a /<path>/<to>/audio -w mywords.txt deck MyDeck -n "Deck name"
    
If you put dict and audio in a directory with structure::

    dictdata/
      audio/
      dict.xdxf
      
then you may use::

    anki_deck -i /<path>/<to>/dictdata -w mywords.txt ...

Also if words file is named ``words.txt`` you may skip ``-w``::

    anki_deck -i /<path>/<to>/dictdata ...

See help for all options::

    anki_deck -h

Notes
-----

Example of converting DSL to XDXF::

    dictzip -d -k En-Ru-Apresyan.dsl.dz
    makedict -i dsl -o xdxf En-Ru-Apresyan.dsl


Example of extracting sounds from ``.lsa``::

    lingvosound2resdb -l ~/.goldendict/content/Speech.lsa
    rm -rf soundfiles
    resdatabase2dir -i res.rifo -d audio
    rm res.r* ; rm SoundE.ogg ; rm Speech.lsa

