"""Define options and an options loader that can be managed during runtime.

Contributors: Poikilos
"""
import copy
import json
import os
import shutil
import sys

CONFIGS_DIR = os.path.dirname(os.path.realpath(__file__))

DEFAULT_SETTINGS = {
    "host": "192.168.16.212",
    "port": 12021,
    "localNodeID": "05.01.01.01.03.01",   # Warning: *only for openlcb*:
    #   See localNodeID_comment in SETTINGS_COMMENTS.
    "farNodeID": "02.01.57.00.04.9C",  # Serialized if hardware:
    #   See farNodeID_comment in SETTINGS_COMMENTS.
    "trace": False,  # Such as for example_remote_nodes.py
    "timeout": 0.5,  # Such as for example_remote_nodes.py
    "device": "/dev/cu.usbmodemCC570001B1",
    # ^ serial device such as for example_string_serial_interface.py
    # "service_name": "",  # mdns service name (maybe more than 1 on host)
    # ^ service_name isn't saved here, since it is not used by LCC
    #   examples (See examples_gui instead, which finds it dynamically,
    #   and where it is associated with a host and port).
}

SETTINGS_COMMENTS = {
    "localNodeID_comment": (
        "Warning: *only for openlcb*:"
        " 05.01.01.01.03.01 is reserved by OpenLCB Python examples."
        " Find or suggest your organization's range"
        " at http://registry.openlcb.org/uniqueidranges"
        " and serialize if producing hardware (See LCC Standard(s))."
    ),
    "farNodeID_comment": (
        "serialized hardware node: for example,"
        " 02.01.57.00.04.9C and 09.00.99.03.00.35 are bobjacobsen's"
    )
}


class Settings:
    """Load runtime settings that can be shared by examples.

    Can load data from JSON (which is not committed to git, but) can be
    generated during runtime before importing this since some example code may
    run in the core of the module rather than in portable functions.

    Attributes:
        _meta (dict): All of the settings, guaranteed to have the keys and
            child keys if any of DEFAULT_SETTINGS as long as used properly (not
            used directly by code outside of class). Defaults to
            DEFAULT_SETTINGS.
        settingtypes (dict): A list of setting types. This should at least be
            set for float, int and bool, since in tkinter, IntVar is used for
            bool in the case of Checkbutton, and StringVar is usually used for
            numbers (if using Entry or Combobox).

    """
    SETTINGS_NAME = "settings.json"
    SETTINGS_PATH = os.path.join(CONFIGS_DIR, SETTINGS_NAME)
    _settingtypes = {
        "trace": {"type": bool},
        "port": {"type": int},
        "timeout": {"type": (float, int)},  # first one is preferred if tuple
    }

    def __init__(self):
        # See class docstring for more info.
        self._meta = None
        self.known_program_keys = {
            "example_remote_nodes": ["trace", "timeout"],
            "example_string_serial_interface": ["device"],
        }
        self.settings_path = Settings.SETTINGS_PATH
        self.load(self.settings_path, required=False)

    def __getitem__(self, key):
        """The dunder method to allow brackets to get a value"""
        if key not in self._meta:
            raise KeyError(
                "Error: either {} is not a valid setting,"
                " _meta was manipulated outside of the class,"
                " or the key should be added to DEFAULT_SETTINGS"
                " to guarantee it exists."
                "".format(key)
            )
        return self._meta.get(key)

    def __setitem__(self, key, value):
        """The dunder method to allow brackets to set a value"""
        if key is None:
            raise KeyError('None is not a valid setting name.')
        if key not in self._meta:
            print("Warning: {} is not the name of a known setting."
                  " To ensure it is the correct name and type,"
                  " use an existing one or add it to DEFAULT_SETTINGS.",
                  file=sys.stderr)
        old_value = self._meta.get(key)
        old_type = type(old_value)
        if old_value is None:
            # In case the value was set to None in a previous call to this,
            #   use the default to determine the type:
            old_type = type(DEFAULT_SETTINGS.get(key))
        if (value is not None) and (old_type is not None):
            if not isinstance(value, type(old_value)):
                raise TypeError(
                    'Expected a(n) {} for {} but got {}({})'
                    ''.format(type(old_value), key, type(value).__name__,
                              value)
                )
        self._meta[key] = value

    def __iter__(self):
        """The dunder method to allow `key in settings` as a boolean
        check, or after `for` to iterate. Works along with __next__ to
        implement using an instance of this class as an iterator.
        """
        self._keys = list(self._meta.keys())
        self._iterate_i = 0
        return self

    def __next__(self):
        """The dunder method to allow `key in settings` as a boolean
        check, or after `for` to iterate. Works along with __iter__ to
        implement using an instance of this class as an iterator.
        """
        if self._iterate_i >= len(self._keys):
            raise StopIteration
        key = self._keys[self._iterate_i]
        self._iterate_i += 1
        return key

    def keys(self):
        """Return the keys iterator from the settings dictionary.

        Returns:
            iterator(str): All settings (each value is the name of a
                setting).
        """
        return self._meta.keys()

    def dumps(self, indent=2, sort_keys=True):
        """Show all settings.
        For args documentation, see json.dumps.

        Returns:
            str: All settings, in JSON format.
        """
        return json.dumps(self._meta, indent=indent, sort_keys=sort_keys)

    def get_types(self, key):
        """Get the type or tuple of types allowed for a setting.

        Typically, set result to the return then you can do:
        if result and not isinstance(var, result): # then depending on
        the scenario, cast # (via `get_preferred_type(key)(var)`) or #
        show a warning/error. See note under "Returns".

        Args:
            key (str): The name of the setting.

        Returns:
            Union(type,tuple(type)): A type or types, or None if not
                defined (typically set the setting to a str value in
                that case). NOTE: isinstance accepts a type or a tuple
                of types, so the return of this method is designed to
                match its usage (but only use return if it is not None).
        """
        info = self._settingtypes.get(key)
        if not info:
            return None
        return info.get("type")

    def get_preferred_type(self, key):
        """Get the type for casting.

        This can be used alongside get_types, but always use
        get_preferred_type to cast, since get_types may return a tuple
        of types.

        Args:
            key (str): The name of the setting.

        Returns:
            type: A type to use. For example, set _type to the return
                then do _type(value) (potentially, a casting function
                could also be returned here, so only use the return
                in that way. For isinstance, use get_types instead).
        """
        _type = self.get_types(key)
        if not _type:
            return None
        if isinstance(_type, tuple):
            return _type[0]  # The first entry is preferred.
        return _type  # There is only one entry, so it is preferred.

    def getDefault(self, key):
        """Get default value of a setting.

        Args:
            key (str): The name of the setting.

        Returns:
            Misc: A value of whatever type is in DEFAULT_SETTINGS.
        """
        if key not in DEFAULT_SETTINGS:
            print("Warning: {} is not in DEFAULT_SETTINGS."
                  " You should probably use a known setting or a value for {}"
                  " should be added to DEFAULT_SETTINGS".format(key, key),
                  file=sys.stderr)
        return DEFAULT_SETTINGS.get(key)

    def load(self, settings_path=None, required=False):
        """Load the settings file.

        Args:
            settings_path (str): Settings json path structured like
                DEFAULT_SETTINGS. Defaults to Settings.SETTINGS_PATH.
            required (bool): Whether to require the file exists and
                raise an error if not. Ok to be False since: whether file is
                present or not (and if False), this method places any missing
                defaults into self._meta. Defaults to False.

        Raises:
            FileNotFoundError: The settings file is not present and required is
                True.
        """
        if not settings_path:
            settings_path = Settings.SETTINGS_PATH
        if os.path.isfile(settings_path):
            try:
                with open(settings_path, 'r') as stream:
                    self._meta = json.load(stream)
            except json.decoder.JSONDecodeError:
                self._meta = copy.deepcopy(DEFAULT_SETTINGS)
                no_ext, dot_ext = os.path.splitext(settings_path)
                bad_path = no_ext+".bad_json.txt"
                i = 1
                while os.path.isfile(bad_path):
                    # Find an unused filename for the backup.
                    i += 1
                    bad_path = no_ext+"."+str(i)+".bad_json.txt"
                print("Error: {} was not proper JSON. Backing up to {}"
                      " and loading defaults."
                      "".format(settings_path, bad_path),
                      file=sys.stderr)
                shutil.move(settings_path, bad_path)
                # ^ must be outside of "with" statement to move file
                raise
        elif required:
            # self._meta = copy.deepcopy(DEFAULT_SETTINGS)
            raise FileNotFoundError(settings_path)
        if not self._meta:
            # settings_path neither found nor required so load defaults
            self._meta = copy.deepcopy(DEFAULT_SETTINGS)

        # self.settings_path = settings_path
        for key, value in DEFAULT_SETTINGS.items():
            if key not in self._meta:
                # If the saved settings file has a missing entry, add it.
                self._meta[key] = copy.deepcopy(value)
            if isinstance(value, dict):
                # If the saved settings file has a missing child entry, add it.
                for child_key, child in value.items():
                    if child_key not in self._meta[key]:
                        self._meta[key][child_key] = copy.deepcopy(child)

    def save(self, settings_path=None):
        """Save the settings.

        Args:
            settings_path (str, optional): Path for saving. Defaults to
                self.settings_path.
        """
        if not settings_path:
            settings_path = self.settings_path
        self._meta.update(SETTINGS_COMMENTS)  # include latest warnings in json
        with open(settings_path, 'w') as stream:
            json.dump(self._meta, stream, indent=1, sort_keys=True)

    def usage(self):
        if not self.caller_documentation:
            return
        print(self.caller_documentation, file=sys.stderr)

    def load_cli_args(self, docstring=None):
        """Load command-line interface arguments.

        Returns:
            int: 0 if ok, otherwise failed (error was shown on stderr).
        """
        self.caller_documentation = docstring
        if len(sys.argv) == 2:
            self['host'] = sys.argv[1]
            parts = self['host'].split(":")
            if len(parts) == 2:
                self['host'] = parts[0]
                try:
                    self['port'] = int(parts[1])
                except ValueError:
                    self.usage()
                    print("Error: Port {} is not an integer.".format(parts[1]),
                          file=sys.stderr)
                    return 1
            elif len(parts) > 2:
                self.usage()
                print("Error: blank, address or address:port format expected.",
                      file=sys.stderr)
                return 1
        elif len(sys.argv) > 2:
            self.usage()
            print("Error: blank, address or address:port format expected"
                  "but got too many arguments: {}".format(sys.argv[1:]),
                  # 1: to skip name of file
                  file=sys.stderr)
            return 1
        return 0


if __name__ == "__main__":
    print(__doc__, file=sys.stderr)
    print("Error: This file is a module."
          " See actual example files which may use it like:",
          file=sys.stderr)
    print("from examples_settings import Settings", file=sys.stderr)
    print("settings = Settings()  # loads {} or defaults"
          "".format(Settings.SETTINGS_NAME), file=sys.stderr)
