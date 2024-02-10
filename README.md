A Python implementation of [OpenLCB](http://www.openlcb.org)/[LCC](https://www.nmra.org/lcc) based on the [LccTools](https://apps.apple.com/sr/app/lcctools/id1640295587) app's [Swift implementation](https://github.com/bobjacobsen/OpenlcbLibrary) as of January 2024.

Requires Python 3.10 or later.

Windows note: In various instructions in this project's documentation,
if you are using Windows you must install Python 3.10 or higher from
python.org with the "py" runner and PATH options both enabled during
install.
- After that you must replace "python3.10" or "python3" command with
  "py -3" (or simply "python" if you only have Python 3 and not 2
  installed).


## Optional Virtual Environment
Optionally you can create a virtual environment. The purpose would be
to ensure you evaluate what packages are necessary to run this project
(and not interfere with similar requirements testing of your other
Python projects on the same machine, & same user if running pip in
userspace).

Linux:
```
mkdir -p ~/.virtualenvs
python3.10 -m venv ~/.virtualenvs/pytest-env
source ~/.virtualenvs/pytest-env/bin/activate
``` 

Windows:
```
md %USERPROFILE%\virtualenvs
py -3 -m venv %USERPROFILE%\virtualenvs\pytest-env
%USERPROFILE%\virtualenvs\pytest-env\Scripts\activate
```

On any OS, type "deactivate" or close the command line window to exit
the virtual environment.


## Development
At this time, all development components listed in this section and subsections are optional, though `pytest` can ensure all tests are run as opposed to ones listed in test_all.py.

Using PEP8 formatting can reduce linter output so that various static analysis tools can identify potential issues without many extra issues related to spacing and line length. Avoiding spaces at the end of lines can be automated and also help keep commits clean since others' IDEs may be set to do that.

If using VSCode (or fully open-source VSCodium):
- Open the workspace file rather than the directory, to load settings for extensions below.
  - Potentially other settings can be stored here in the future, but avoid putting computer-specific settings such as Python path in there. Use directory or user tab in VSCode settings for such settings instead to prevent causing problems for others using the project file.
- Some related extensions:
  - (optional) **ruff**: realtime linting
  - (optional) **ReWrap**: To wrap comments, select then press Alt+Q
  - (recommended, reduces commit diffs) **Trailing Spaces** by Shardul Mahadik
  - (recommended) **autoDocstring**: Type `"""` below a method or class and it will create a Sphinx-style template for you.
    - The workspace file has `"autoDocstring.docstringFormat": "google"` set since Google style is widely used and comprehensive (documents types etc).

### Testing
To run the unit test suite:
```
python3.10 -m pip install --user pytest
# ^ or use a 
python3.10 -m pytest
# or to auto-detect test and run with standard log level:
# python3.10 -m pytest tests

# or to use with only unittest not pytest:
# python3.10 test_all.py
```


#### Examples
There are examples for using the code at various levels of integration:
```
python3.10 example_string_interface.py
python3.10 example_frame_interface.py
python3.10 example_message_interface.py
python3.10 example_datagram_transfer.py
python3.10 example_memory_transfer.py
python3.10 example_node_implementation.py
```

These will require the right host name and port number; and if different Node ID(s) are necessary for your hardware configuration, they would have to be edited manually in the example py file(s) (or parameterized in a program based on the example(s)): See near top of the files, below imports.

You can override the hard-coded IP address and port by passing it as the first argument on the command line. Example:
```
python3.10 example_node_implementation.py 192.168.1.40
python3.10 example_node_implementation.py 192.168.1.40:12021
```

For an overview of the structure, see [this diagram](doc/Overview.png) of the example programs.

#### Checking Implementations

The "olcbchecker" directory contains the beginning of an implementation checking package.
For more information, see the [README.md](olcbchecker/README.md) file there.

