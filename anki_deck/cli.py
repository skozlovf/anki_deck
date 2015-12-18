"""
This module implements command line interface for the anki_deck.

:copyright: (c) 2015 by Sergey Kozlov
:license: MIT, see LICENSE for more details.
"""
import sys
import os.path as op
import logging
import click
from anki_deck.parser import get_cards

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
pass_ctx = click.make_pass_decorator(dict, ensure=True)


@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True)
@click.option('--input-dir', '-i',
              help="Input data dir with 'dict.xdxf' and 'audio/'.")
@click.option('--dict', '-d',  help='Dictionary file in xdxf format.')
@click.option('--audio', '-a', help='Directory with audio files in ogg format.')
@click.option('--words', '-w', help='Input words file.', default='words.txt',
              show_default=True)
@pass_ctx
def run(ctx, input_dir, dict, audio, words):
    """Tool to generate cards file which may be imported to Anki."""

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    c = click.get_current_context()
    ctx['input_dir'] = input_dir
    ctx['dict'] = dict
    ctx['audio'] = audio
    ctx['words'] = words

    if input_dir:
        if not dict:
            ctx['dict'] = op.join(input_dir, 'dict.xdxf')
        if not audio:
            ctx['audio'] = op.join(input_dir, 'audio')

    if c.invoked_subcommand is None:
        c.invoke(txt, None)


@run.command()
@click.option('--out', '-o', default='flashcards.txt', show_default=True,
              help="Output filename.")
@pass_ctx
def txt(ctx, out):
    """Generate text flashcards file."""
    from anki_deck.flashcards import FlashcardsWriter
    handler = FlashcardsWriter(out)
    get_cards(ctx['words'], ctx['dict'], ctx['audio'], handler)


@run.command()
@click.option('--deck-name', '-n', help="Deck name.")
@click.argument('out')
@pass_ctx
def deck(ctx, deck_name, out):
    """Generate apkg deck."""
    name, ext = op.splitext(out)

    if not ext:
        out = name + '.apkg'
    elif ext != '.apkg':
        logging.error('Invalid deck filename extension, must be .apkg')
        sys.exit(1)

    if deck_name is None:
        deck_name = name

    from anki_deck.apkg import Deck
    handler = Deck(out, ctx['audio'], deck_name)
    get_cards(ctx['words'], ctx['dict'], ctx['audio'], handler)


if __name__ == '__main__':
    run()
