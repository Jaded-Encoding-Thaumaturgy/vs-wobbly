# vs-wobbly

<p align="center">
    <img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/vswobbly">
    <a href="https://pypi.org/project/vswobbly/"><img alt="PyPI" src="https://img.shields.io/pypi/v/vswobbly"></a>
    <a href="https://github.com/Jaded-Encoding-Thaumaturgy/vs-wobbly/commits/master"><img alt="GitHub commits since tagged version" src="https://img.shields.io/github/commits-since/Jaded-Encoding-Thaumaturgy/vs-wobbly/latest"></a>
    <a href="https://github.com/Jaded-Encoding-Thaumaturgy/vs-wobbly/blob/master/LICENSE"><img alt="PyPI - License" src="https://img.shields.io/pypi/l/vswobbly"></a>
    <a href="https://discord.gg/XTpc6Fa9eB"><img alt="Discord" src="https://img.shields.io/discord/856381934052704266?label=discord"></a>
</p>

A collection of VapourSynth functions for parsing and filtering wobbly files.
Full information on how every function works,
as well as a list of dependencies and links,
can be found in the docstrings of each function and class.
For further support,
drop by `#dev` in the [JET Discord server](https://discord.gg/XTpc6Fa9eB).

## How to install

Install `vswobbly` with the following command:

```shell
pip install vswobbly
```

## How to use

Simplest way to use it is to pass a wobbly file (`.wob`) to `WobblyProcessor.from_file()`,
followed by calling `apply()`.

```python
from vswobbly import WobblyProcessor,

wob = WobblyProcessor.from_file('C:/path/to/wobbly.wob')
clip = wob.apply()
```

If you only need the parsed wobbly data,
you can use `WobblyParser.from_file()`:

```python
from vswobbly import WobblyParser

wob = WobblyParser.from_file('C:/path/to/wobbly.wob')
```

This will return a `WobblyParser` data class,
containing all the relevant data for video processing.
Note that metadata, information about wobbly's UI,
and wibbly parameters are currently excluded.

### Strategies

Different "strategies" can be passed to `WobblyProcessor`
to change how certain problems are handled internally.
This package comes with a handful included.

For example,
automatically handling combed frames
with vinverse:

```python
from vswobbly import WobblyProcessor, DecombVinverseStrategy

wob = WobblyProcessor.from_file(
    'C:/path/to/wobbly.wob',
    strategies=[DecombVinverseStrategy()]
)

clip = wob.apply()
```

Which would then run the [DecombVinverseStrategy](./vswobbly/process/strategies/combed.py) strategy
on all combed frames.

This is written to be really flexible,
and allow users to handle these problems however they see fit.
To implement your own strategy,
create a class and inherit from [AbstractProcessingStrategy](./vswobbly/process/strategies/abstract.py).
Refer to the existing strategies and the docstrings of the abstract class for examples.

Note: For orphan field handling to be handled correctly,
the strategy *must* have 'Orphan' in its name.
