"""
Examples GUI

This file is part of the PythonOlcbNode project
(<https://github.com/bobjacobsen/PythonOlcbNode>).

Contributors: Poikilos

Purpose: Provide an easy way to enter settings for examples and run them.
- tkinter is used since it is included in Python (except in Debian-based
  distros, which require the python3-tk package due to Debian requirements
  for GUI components to be packaged separately).
"""
import json
import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk
from collections import OrderedDict

from examples_settings import Settings

zeroconf_enabled = False
try:
    from zeroconf import ServiceBrowser, ServiceListener, Zeroconf
    zeroconf_enabled = True
except ImportError:
    class Zeroconf:
        """Placeholder for when zeroconf is *not* present"""
        pass

    class ServiceListener:
        """Placeholder for when zeroconf is *not* present"""
        pass

    class ServiceBrowser:
        """Placeholder for when zeroconf is *not* present"""
        pass


class MyListener(ServiceListener):
    pass


class DataField():
    """Store various widgets and data associated with a single data field.
    Attributes:
        label (Label): A label associated with (usually left of) the field.
        var (Union[StringVar,IntVar]): Makes value accessible in a uniform way
            (self.var.get()) regardless of widget class.
        widget (Misc): The widget used to enter data (value is stored in var).
        button (Button): optional command button.
        tooltip (Label): An extra label associated with (usually below) the
            field.
    """
    def __init__(self):
        self.label = None
        self.var = None
        self.widget = None
        self.button = None
        self.tooltip = None

    def get(self):
        return self.var.get()

    def set(self, value):
        self.var.set(value)


class MainForm(ttk.Frame):
    """The interface to choose device(s) for examples.

    The program is organized into fields. Each field contains a label, entry
    widget, and potentially a tooltip Label and command button.

    - The entry widget for each field may be a ttk.Entry, ttk.Combobox, or
      potentially another ttk widget subclass.

    - Each field has a key. Only keys in self.settings are directly used
      as settings.

    Attributes:
        w1 (Union[Tk,Frame]): The Tk (first and only Window typically). It is
            set automatically to self.winfo_toplevel() by gui method.
        parent (Union[Tk,Frame]): Tk (same as self.w1 in that case) or tk.Frame
            instance, whichever contains self.
        fields (list[DataField]): A list of settings.
        example_buttons (OrderedDict[Button]): The example module name is the
            key and the Button instance is the value.
        example_modules (OrderedDict[str]): The example
            module name is the key, and the full path is the value. If
            examples are made modular, the value will not be nessary, but
            for now just run the file in another Python instance (See
            run_example method).

    Args:
        parent (Union[Tk,Frame,0]): The Tk (first and only Window typically) or
            tk.Frame, either way containing self. 0 to make a new Tk. The
            tk instance is always stored in self.w1 regardless of parent.
    """

    def __init__(self, parent):
        self.zeroconf = None
        self.listener = None
        self.browser = None
        self.errors = []
        try:
            self.settings = Settings()
        except json.decoder.JSONDecodeError as ex:
            self.errors.append(
                "Error: {} not loaded! {}".format(Settings.SETTINGS_NAME, ex)
            )
            # Try again (load defaults), since Settings is expected to
            #   have backed up & moved the bad JSON file:
            self.settings = Settings()
        self.detected_services = OrderedDict()
        self.fields = OrderedDict()
        self.proc = None
        self.gui(parent)
        self.w1.after(1, self.on_form_loaded)  # must go after gui
        self.example_modules = OrderedDict()
        self.example_buttons = OrderedDict()
        if zeroconf_enabled:
            self.zeroconf = Zeroconf()
            self.listener = MyListener()
            self.listener.update_service = self.update_service
            self.listener.remove_service = self.remove_service
            self.listener.add_service = self.add_service

    def on_form_loaded(self):
        self.load_settings()
        self.load_examples()
        count = self.show_next_error()
        if not count:
            self.set_status(
                "Welcome! Select an example. Run also saves settings."
            )

    def show_next_error(self):
        if not self.errors:
            return 0
        error = self.errors.pop(0)
        if not error:
            return 0
        self.set_status(error)
        return 1

    def remove_examples(self):
        for module_name, button in self.example_buttons.items():
            button.grid_forget()
            self.row -= 1
        self.example_buttons.clear()
        self.example_modules.clear()

    def load_examples(self):
        self.remove_examples()
        repo_dir = os.path.dirname(os.path.realpath(__file__))
        self.example_var = tk.IntVar()  # Shared by *all* in radio group.
        # ^ The value refers to an entry in examples:
        self.examples = []
        for sub in sorted(os.listdir(repo_dir)):
            if not sub.startswith("example_"):
                continue
            if not sub.endswith(".py"):
                continue
            sub_path = os.path.join(repo_dir, sub)
            name, _ = os.path.splitext(sub)  # name, dot+extension
            self.example_modules[name] = sub_path
            button = ttk.Radiobutton(
                self,
                text=name,
                variable=self.example_var,
                value=len(self.examples),
                # command=lambda x=name: self.run_example(module_name=x),
                # x=name is necessary for early binding, otherwise all
                # lambdas will have the *last* value in the loop.
            )
            self.examples.append(name)
            button.grid(row=self.row, column=1)
            self.example_buttons[name] = button
            self.row += 1
        self.run_button = ttk.Button(
            self,
            text="Run",
            command=self.run_example,
            # command=lambda x=name: self.run_example(module_name=x),
            # x=name is necessary for early binding, otherwise all
            # lambdas will have the *last* value in the loop.
        )
        self.run_button.grid(row=self.row, column=1)
        self.row += 1

    def run_example(self, module_name=None):
        """Run the selected example.

        Args:
            module_name (str, optional): The module name (file without
                extension) of the example. Defaults to selected
                Radiobutton.
        """
        if not module_name:
            # for name, radiobutton in self.example_buttons.items():
            index = self.example_var.get()
            if index is None:
                self.set_status("Select an example first.")
                return
            module_name = self.examples[index]

        self.set_status("")
        node_ids = (
            self.fields['localNodeID'].get(),
            self.fields['farNodeID'].get(),
        )
        for node_id in node_ids:
            if (":" in node_id) or ("." not in node_id):
                self.set_status("Error: expected dot-separated ID")
                return
        self.save_settings()
        module_path = self.example_modules[module_name]
        args = (sys.executable, module_path)
        self.set_status("Running {} (see console for results)..."
                        "".format(module_name))
        self.proc = subprocess.Popen(
            args,
            shell=True,
            # close_fds=True, close file descriptors >= 3 before running
            # stdin=None, stdout=None, stderr=None,
        )

    def load_settings(self):
        # import json
        # print(json.dumps(self.settings._meta, indent=1, sort_keys=True))

        # print("[gui] self.settings['localNodeID']={}"
        #       .format(self.settings['localNodeID']))
        for key, var in self.fields.items():
            if key not in self.settings:
                # The field must not be a setting. Don't try to load
                #   (Avoid KeyError).
                continue
            self.fields[key].set(self.settings[key])
        # print("[gui] self.fields['localNodeID']={}"
        #       .format(self.fields['localNodeID'].get()))

    def save_settings(self):
        for key, field in self.fields.items():
            if key not in self.settings:
                # Skip runtime GUI data fields such as
                #   self.fields['service_name'] that aren't directly used as
                #   settings.
                print("{} is not in settings.".format(key))
                continue
            print("{} is in settings.".format(key))
            value = field.get()
            _types = self.settings.get_types(key)
            if _types:
                if not isinstance(value, _types):
                    _type = self.settings.get_preferred_type(key)
                    # ^ Get the preferred type in case multiple are allowed
                    #   (usually float or int in that case)
                    value = _type(value)
            self.settings[key] = value
        self.settings.save()

    def gui(self, parent):
        print("Using {}".format(self.settings.settings_path))
        # import json
        # print(json.dumps(self.settings._meta, indent=1, sort_keys=True))
        self.parent = parent
        ttk.Frame.__init__(self, self.parent)
        self.row_count = 0
        self.column_count = 0
        self.tooltip_column = 0
        self.tooltip_columnspan = 3
        self.grid_args = {
            'sticky': tk.NSEW,  # N is top ("north"), W is left, etc.
            # 'padx': 8,
            # 'pady': 8,
        }
        # self.w1.place(x=0, y=0, width=500, height=450)
        self.w1 = self.winfo_toplevel()  # a.k.a. root
        # self.parent.pack(fill=tk.BOTH)

        self.grid(sticky=tk.NSEW, row=0, column=0)  # place *self*
        # ^ Only one other widget is in the parent: statusLabel
        # self.statusSV = tk.StringVar(master=self.w1)

        self.parent.rowconfigure(0, weight=1)
        self.parent.columnconfigure(0, weight=1)
        self.row = 0
        self.add_field("service_name",
                       "TCP Service name (optional, sets host&port)",
                       gui_class=ttk.Combobox, tooltip="")
        self.fields["service_name"].var.trace('w', self.on_service_name_change)
        self.add_field("host", "IP address/hostname",
                       command=self.detect_hosts,
                       command_text="Detect")
        self.add_field(
            "port",
            "Port",
            command=self.default_port,
            command_text="Default",
        )
        self.add_field(
            "localNodeID",
            "Local Node ID",
            command=self.default_local_node_id,
            command_text="Default",
            tooltip=('("05.01.01.01.03.01 for Python openlcb examples only:'),
        )
        self.unique_ranges_url = "https://registry.openlcb.org/uniqueidranges"
        underlined_url = \
            ''.join([letter+'\u0332' for letter in self.unique_ranges_url])
        # ^ '\u0332' is unicode for "underline previous character"
        #   and is a way of underlining without creating potential
        #   cross-platform issues when choosing a font name when creating
        #   a tk.Font instance.
        self.local_node_url_label = ttk.Label(
            self,
            text='See {})'.format(underlined_url),
        )
        # A label is not a button, so must bind to mouse button event manually:
        self.local_node_url_label.bind(
            "<Button-1>",  # Mouse button 1 (left click)
            lambda e: self.open_url(self.unique_ranges_url)
        )
        self.local_node_url_label.grid(row=self.row,
                                       column=self.tooltip_column,
                                       columnspan=self.tooltip_columnspan,
                                       sticky=tk.N)
        self.row += 1

        self.add_field(
            "farNodeID", "Far Node ID",
            gui_class=ttk.Combobox,
            # command=self.detect_nodes,  # TODO: finish detect_nodes & use
            # command_text="Detect",  # TODO: finish detect_nodes & use
        )

        self.add_field(
            "device", "Serial Device (or COM port)",
            gui_class=ttk.Combobox,
            command=lambda: self.load_default("device"),
            command_text="Default",
        )

        # The status widget is the only widget other than self which
        #   is directly inside the parent widget (forces it to bottom):
        self.statusLabel = ttk.Label(self.parent)
        self.statusLabel.grid(sticky=tk.S, row=1, column=0,
                              columnspan=self.column_count)
        # Use the counts determined so far to weight column width equally (use
        #   same weight):
        if self.row > self.row_count:
            self.row_count = self.row
        if self.column > self.column_count:
            self.column_count = self.column
        for column in range(self.column_count):
            self.columnconfigure(column, weight=1)
        # for row in range(self.row_count):
        #     self.rowconfigure(row, weight=1)
        # self.rowconfigure(self.row_count-1, weight=1)  # make last row expand

    def on_service_name_change(self, index, value, op):
        key = self.fields['service_name'].get()
        info = self.detected_services.get(key)
        if not info:
            # The user may be typing, so don't spam screen with messages,
            #   just ignore incomplete entries.
            return
        # We got info, so use the info to set *other* fields:
        self.fields['host'].set(info['server'])
        self.fields['port'].set(info['port'])
        self.set_status("Hostname & Port have been set ({server}:{port})"
                        .format(**info))

    def add_field(self, key, text, gui_class=ttk.Entry, command=None,
                  command_text=None, tooltip=None):
        """Generate a uniform data field that may or may not affect a setting.

        The row(s) for the data field will start at self.row, and self.row will
        be incremented for (each) row added by this function.

        Args:
            text (str): Text for the label.
            key (str): Key to store the widget.
            gui_class (Misc): The ttk widget class or function to use to create
                the data entry widget (field.widget).
            command (function, optional): Command for button. Defaults to None.
            command_text (str, optional): Text for button. Defaults to None.
            tooltip (str, optional): Add a tooltip tk.Label as field.tooltip
                with this text. Added even if "". Defaults to None (not added
                in that case).
        """
        # self.row should already be set to an empty row.
        self.column = 0  # Return to beginning of row

        if command:
            if not command_text:
                raise ValueError("command_caption is required for command.")
        if command_text:
            if not command:
                raise ValueError("command is required for command_caption.")

        field = DataField()
        field.label = ttk.Label(self, text=text)
        field.label.grid(row=self.row, column=self.column, **self.grid_args)
        self.host_column = self.column
        self.column += 1
        self.fields[key] = field
        field.var = tk.StringVar(self.w1)
        field.widget = gui_class(
            self,
            textvariable=field.var,
        )
        field.widget.grid(row=self.row, column=self.column, **self.grid_args)
        self.column += 1

        if command:
            field.button = ttk.Button(self, text=command_text,
                                      command=command)
            field.button.grid(row=self.row, column=self.column,
                              **self.grid_args)
        self.column += 1  # go to next column even if button wasn't added,
        #   to keep columns uniform in case another column is added.

        self.row += 1

        # return field
        if tooltip is not None:
            # Even if "", still add it.
            field.tooltip = ttk.Label(self, text=tooltip)
            field.tooltip.grid(row=self.row, column=self.tooltip_column,
                               columnspan=self.tooltip_columnspan, sticky=tk.N)
            # ^ tk.N ("north') is top. Stick to top since the tip describes the
            #   field.widget above it.
            # ^ **self.gridargs is not necessary here (sticky is always tk.N).
            self.row += 1

        if self.column > self.column_count:
            self.column_count = self.column

    def open_url(self, url):
        import webbrowser
        webbrowser.open_new_tab(url)

    def default_local_node_id(self):
        self.load_default('localNodeID')

    def default_port(self):
        self.load_default('port')

    def load_default(self, key):
        self.fields[key].set(self.settings.getDefault(key))

    def set_status(self, msg):
        self.statusLabel.configure(text=msg)

    def set_tooltip(self, key, msg):
        self.fields[key].tooltip.configure(text=msg)

    def show_services(self):
        self.fields['service_name'].widget['values'] = \
            list(self.detected_services.keys())

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        if name in self.detected_services:
            self.detected_services[name]['type'] = type_
            print(f"Service {name} updated")
        else:
            self.detected_services[name] = {'type': type_}
            print(f"Warning: {name} was not present yet during update.")
        self.show_services()

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        if name in self.detected_services:
            del self.detected_services[name]
            self.set_status(f"{name} disconnected from the Wi-Fi/LAN")
            print(f"Service {name} removed")
        else:
            print(f"Warning: {name} was already removed.")
        self.show_services()

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        """
        This must use name as key, since multiple services can be advertised by
        one server!
        """
        info = zc.get_service_info(type_, name)
        if name not in self.detected_services:
            self.detected_services[name] = {}
            self.detected_services[name]['type'] = info.type
            # By now we only have ones where type==servicetype
            #   (See detect_hosts) unless servicetype is set to None.
            self.detected_services[name]['server'] = info.server  # hostname
            self.detected_services[name]['port'] = info.port
            self.detected_services[name]['properties'] = info.properties
            # ^ properties is a dict potentially containing various info
            #   (no properties are known to be useful in this case)
            self.detected_services[name]['addresses'] = info.addresses
            # ^ addresses is a list of bytes objects
            # other info attributes: priority, weight, added, interface_index
            self.set_tooltip(
                'service_name',
                f"Found {name} on Wi-Fi/LAN. Select an option above."
            )
            print(f"Service {name} added, service info: {info}")
        else:
            print(f"Warning: {name} was already added.")
        self.show_services()

    def detect_hosts(self, servicetype="_openlcb-can._tcp.local."):
        if not zeroconf_enabled:
            self.set_status("The Python zeroconf package is not installed.")
            return
        if not self.zeroconf:
            self.set_status("Zeroconf was not initialized.")
            return
        if not self.listener:
            self.set_status("Listener was not initialized.")
            return
        if self.browser:
            self.set_status("Already listening for {} devices."
                            .format(self.servicetype))
            return
        self.servicetype = servicetype
        self.browser = ServiceBrowser(self.zeroconf, self.servicetype,
                                      self.listener)
        self.set_status("Detecting hosts...")

    def detect_nodes(self):
        self.set_status("Detecting nodes...")
        self.set_status("Detecting nodes...not implemented here."
                        " See example_node_implementation.")

    def exit_clicked(self):
        self.top = self.winfo_toplevel()
        self.top.quit()


def main():
    root = tk.Tk()
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    window_w = round(screen_w / 2)
    window_h = round(screen_h * .75)
    root.geometry("{}x{}".format(
        window_w,
        window_h,
    ))  # WxH+X+Y format
    root.minsize = (window_w, window_h)
    mainform = MainForm(root)
    mainform.master.title("Python OpenLCB Examples")
    try:
        mainform.mainloop()
    finally:
        if mainform.zeroconf:
            mainform.zeroconf.close()
            mainform.zeroconf = None
    return 0


if __name__ == "__main__":
    sys.exit(main())
