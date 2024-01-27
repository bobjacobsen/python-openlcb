
A Python implementation of [OpenLCB](http://www.openlcb.org)/[LCC](https://www.nmra.org/lcc) based on the [LccTools](https://apps.apple.com/sr/app/lcctools/id1640295587) app's [Swift implementation](https://github.com/bobjacobsen/OpenlcbLibrary) as of January 2024.

Requires Python 3.10 or later.

To run the unit test suite:
```
python3.10 pythonolcb/all_test.py
```

There are examples for using the code at various levels of integration:
```
python3.10 pythonolcb/example_string_interface.py
python3.10 pythonolcb/example_frame_interface.py
python3.10 pythonolcb/example_message_interface.py
python3.10 pythonolcb/example_datagram_transfer.py
python3.10 pythonolcb/example_memory_transfer.py
```

These will require editing to have the right host name, port number, and in some cases the right remote node ID for your hardware configuration. See the top of the files.

For an overview of the structure, see [this diagram](doc/Overview.png) of the example programs
