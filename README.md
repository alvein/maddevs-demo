# SplitMessageHTMLParser
Simple wrapper for the python **HTMLParser** for splitting the initial HTML-string into fragments with specific length.

## Command line usage
```shell
$ poetry shell
$ cd maddevs_demo
$ python split_msg.py --max-len=3072 <PATH_TO_FILE>
```

- `--max-len` or `--max_len` - fragment length
- `<PATH_TO_FILE>` - path to the HTML file

## Unit tests
```shell
$ poetry shell
$ cd maddevs_demo
$ python tests.py -v
```