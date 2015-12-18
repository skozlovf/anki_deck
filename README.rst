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

See help::

    anki_card -h
    anki_card txt -h


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

