import os
import json
import warnings

import jsonschema


with open('schema.json') as f:
    schema = json.load(f)


def discover(plugin_root=None, lookfor='plugin.json'):

    def yield_plugins():
        for name in os.listdir(plugin_root):
            plugin_dir = os.path.join(plugin_root, name)
            plugin_path = os.path.join(plugin_dir, lookfor)
            if os.path.isdir(plugin_dir) and os.path.exists(plugin_path):
                with open(plugin_path, 'r') as f:
                    plugin_json = json.load(f)
                    plugin_json['name'] = name
                    plugin_json['path'] = plugin_dir
                try:
                    jsonschema.validate(plugin_json, schema)
                    yield plugin_json
                except jsonschema.exceptions.ValidationError as e:
                    msg = ('Failed to validate a plugin.\n'
                           'Plugin name: {}\n'
                           'Plugin path: {}\n'
                           'Error: {}\n').format(name, plugin_dir, e.message)
                    warnings.warn(msg)

    return list(yield_plugins())


if __name__ == '__main__':
    import pprint

    root = 'plugins'
    join = os.path.join
    plugins = {}
    for ptype in ('source', 'effect', 'display'):
        plugins[ptype] = discover(join(root, ptype))
    pprint.pprint(plugins)

