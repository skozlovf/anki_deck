"""
This module implements command line interface for the anki_deck.

:copyright: (c) 2015 by Sergey Kozlov
:license: MIT, see LICENSE for more details.
"""
import sys
import os.path as op
import logging
import click
from anki_deck.apkg import Deck
from anki_deck.flashcards import FlashcardsWriter
from anki_deck.parser import get_cards


@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--input-dir', '-i',
              help="Input data dir with 'dict.xdxf' and 'audio/'.")
@click.option('--dict', '-d',  help='Dictionary file in xdxf format.')
@click.option('--audio', '-a', help='Directory with audio files in ogg format.')
@click.option('--words', '-w', help='Input words file.', default='words.txt',
              show_default=True)
@click.pass_context
def run(ctx, input_dir, dict, audio, words):
    """Tool to generate cards file which may be imported to Anki."""

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    ctx.meta['input_dir'] = input_dir
    ctx.meta['dict'] = dict
    ctx.meta['audio'] = audio
    ctx.meta['words'] = words

    if input_dir:
        if not dict:
            ctx.meta['dict'] = op.join(input_dir, 'dict.xdxf')
        if not audio:
            ctx.meta['audio'] = op.join(input_dir, 'audio')


@run.command()
@click.option('--out', '-o', default='flashcards.txt', show_default=True,
              help="Output filename.")
@click.pass_context
def txt(ctx, out):
    """Generate text flashcards file."""
    handler = FlashcardsWriter(out)
    get_cards(ctx.meta['words'], ctx.meta['dict'], ctx.meta['audio'], handler)


@run.command()
@click.option('--deck-name', '-n', help="Deck name.")
@click.argument('out')
@click.pass_context
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

    handler = Deck(out, ctx.meta['audio'], deck_name)
    get_cards(ctx.meta['words'], ctx.meta['dict'], ctx.meta['audio'], handler)


if __name__ == '__main__':
    run()
