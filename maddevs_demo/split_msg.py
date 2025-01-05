"""Manual check for fragments splitter"""

from pathlib import Path
import click

from msg_split import SplitMessageHTMLParser


@click.command()
@click.option('--max-len', '--max_len', type=int, help='Specific length for the fragments')
@click.argument('name')
def split_message_manual(name: str, max_len: int) -> None:
    """Splits the original message (`source`) into fragments of the specified length (`max_len`)."""
    file_path = Path(name)
    if file_path.exists() and file_path.is_file:
        with open(file_path, 'r') as fh:
            parser = SplitMessageHTMLParser(max_len=max_len, debug=True)
            parser.feed(fh.read())


if __name__ == '__main__':
    split_message_manual()