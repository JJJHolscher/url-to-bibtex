# URL-TO-BIBTEX

```sh
nix run github:jjjholscher/url-to-bibtex \
  10.48550/arXiv.2105.14111 \
  https://deepmind.google/discover/blog/how-undesired-goals-can-arise-with-correct-rewards/
```

outputs

```
@misc{langosco_goal_2021,
	title = {Goal {Misgeneralization} in {Deep} {Reinforcement} {Learning}},
    [...]
	year = {2021},
}


@misc{noauthor_how_2024,
	title = {How undesired goals can arise with correct rewards},
    [...]
	year = {2024},
}

```

You can instead also supply urls, doi's or other identifiers through text files or the stdin. Stdin input or text files should look like this:

```
# Comments are ignored.
https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4959137/ # a comment
# The zotero translation server supports a lot of different links.
https://youtu.be/fVN_5xsMDdg?si=6qYJG-IbZqMqkt-B

# Though some sites might throttle you or prevent you from accessing it through the server.
https://www.nytimes.com/2018/06/11/technology/net-neutrality-repeal.html
# in such failed cases, the bare link will be added to the output, so you know your bibliography is incomplete (surpress this functionality with --hide-failures).
```

Zotero's translation server also supports other bibliograpy formats.
Find more info on their [github](https://github.com/zotero/translation-server/tree/master).

```
usage: url-to-bibtex [-h] [-o OUTPUT] [-f FORMAT] [--hide-failures] [-v]
                     [inputs ...]

Process URLs, DOIs, other identifiers, and file paths.

positional arguments:
  inputs                URLs, DOIs, other identifiers, or file paths

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output file to write the results
  -f FORMAT, --format FORMAT
                        Format to store the results in, defaults to bibtex.
  --hide-failures       Don't comment failed items.
  -v, --verbose         Don't suppress error messages to the stderr.
```

Alternatively if you want more control, you can use my [flake.nix on a fork of the zotero translation server](https://github.com/jjjholscher/translation-server) to launch the server yourself.

```
nix run github:jjjholscher/translation-server
```

## quirks

### timeout

The translation server sometimes reports a timeout error that you can see if you pass the `--verbose` flag.
```
501 Server Error: Not Implemented for url: http://127.0.0.1:1969/search
(1)(+0000003): Unhandled rejection: Error: ESOCKETTIMEDOUT
```
In such cases, you _might_ be able to still get it to work if just try again a few times.

### slow

The server can take a while to get the metadata, on top of that I sleep the program for a second for every link to prevent you from getting throttled.
Little I can do here, seeing how the zotero application can also be a bit slow about this, I think this is just a fact of life.
