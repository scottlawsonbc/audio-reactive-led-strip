import os
import sys
import json
import time
import pprint
import threading
import subprocess

import flask

import plugin


app = flask.Flask(__name__)
root = 'plugins'
types = ('source', 'effect', 'display')
plugins = {t: plugin.discover(os.path.join(root, t)) for t in types}
pprint.pprint(plugins)


_rpc_lock = threading.Lock()
_rpc_process = {t: None for t in types}


def _plugin_lookup(method):
    for plugin_type in plugins:
        for p in plugins[plugin_type]:
            if method == p['name']:
                return p
    raise KeyError('Unrecognized method "{}"'.format(method))


def _plugin_args(p, params):
    args = [*p['exec']]
    for arg in p['args']:
        if arg['name'] in params:
            if 'flag' in arg:
                args.append(arg['flag'])
            args.append(str(params[arg['name']]))
    return args


def _kill_rpc():
    for t in types:
        if isinstance(_rpc_process[t], subprocess.Popen):
            print('Killing', t)
            _rpc_process[t].kill()


def run_command(params):
    source, source_params = params['source'], params['source_params']
    effect, effect_params = params['effect'], params['effect_params']
    display, display_params = params['display'], params['display_params']

    source_plugin = _plugin_lookup(source)
    effect_plugin = _plugin_lookup(effect)
    display_plugin = _plugin_lookup(display)

    source_args = _plugin_args(source_plugin, source_params)
    effect_args = _plugin_args(effect_plugin, effect_params)
    display_args = _plugin_args(display_plugin, display_params)

    with _rpc_lock:
        _kill_rpc()
        print(source_args)
        print(effect_args)
        print(display_args)

        _rpc_process['source'] = subprocess.Popen(
            args=source_args,
            cwd=source_plugin['path'],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            bufsize=0)
        _rpc_process['effect'] = subprocess.Popen(
            args=effect_args,
            cwd=effect_plugin['path'],
            stdin=_rpc_process['source'].stdout,
            stdout=subprocess.PIPE,
            bufsize=0)
        _rpc_process['display'] = subprocess.Popen(
            args=display_args,
            cwd=display_plugin['path'],
            stdin=_rpc_process['effect'].stdout,
            stdout=sys.stdout,
            bufsize=0)
    time.sleep(0.1)


@app.route('/api', methods=['POST'])
def api():
    request = flask.request.get_json()
    response = {'jsonrpc': '2.0', 'id': request['id']}

    try:
        if request['method'] == 'run':
            run_command(request['params'])
        response['result'] = 'Success!'
    except Exception as e:
        response['error'] = str(e)

    return flask.jsonify(response)


@app.route('/', methods=['GET'])
def index():
    with open('defaults.json') as f:
        defaults = json.load(f)
    return flask.render_template('index.html', plugins=plugins, defaults=defaults)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
