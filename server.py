#!flask/bin/python
import importlib
import inspect
from flask import Flask, jsonify, abort, send_from_directory, request
from audioled import filtergraph
from audioled import audio
from audioled import effects
from audioled import colors
import jsonpickle

num_pixels = 300

app = Flask(__name__,  static_url_path='/')
fg = filtergraph.FilterGraph()

audio_in = audio.AudioInput()
fg.addEffectNode(audio_in)

movingLights = effects.MovingLightEffect(num_pixels, audio_in.getSampleRate())
fg.addEffectNode(movingLights)

fg.addConnection(audio_in,0,movingLights,0)

# @app.route('/', methods=['GET'])
# def home():
#     return app.send_static_file('index.html')

@app.route('/<path:path>')
def send_js(path):
    return send_from_directory('resources', path)

@app.route('/nodes', methods=['GET'])
def nodes_get():
    nodes = [node for node in fg._filterNodes]
    return jsonpickle.encode(nodes)



@app.route('/node/<nodeUid>', methods=['GET'])
def node_uid_get(nodeUid):
    try:
        node = next(node for node in fg._filterNodes if node.uid == nodeUid)
        return jsonpickle.encode(node)
    except StopIteration:
        abort(404,"Node not found")

@app.route('/node/<nodeUid>', methods=['DELETE'])
def node_uid_delete(nodeUid):
    try:
        node = next(node for node in fg._filterNodes if node.uid == nodeUid)
        fg.removeEffectNode(node.effect)
        return "OK"
    except StopIteration:
        abort(404, "Node not found")

@app.route('/node', methods=['POST'])
def node_post():
    if not request.json:
        abort(400)
    full_class_name = request.json[0]
    parameters = jsonpickle.decode(request.json[1])
    print(parameters)
    module_name, class_name = None, None
    try:
        module_name, class_name = getModuleAndClassName(full_class_name)
    except RuntimeError:
        abort(403)
    class_ = getattr(importlib.import_module(module_name), class_name)
    instance = class_(**parameters)
    node = fg.addEffectNode(instance)
    return jsonpickle.encode(node)

@app.route('/connections', methods=['GET'])
def connections_get():
    connections = [con for con in fg._filterConnections]
    return jsonpickle.encode(connections)

@app.route('/connection', methods=['POST'])
def connection_post():
    if not request.json:
        abort(400)
    connection = request.json
    fg.addNodeConnection(connection['from_node_uid'], int(connection['from_node_channel']), connection['to_node_uid'], int(connection['to_node_channel']))
    
    return "OK"

@app.route('/effects', methods=['GET'])
def effects_get():
    childclasses = inheritors(effects.Effect)
    return jsonpickle.encode([child for child in childclasses])

@app.route('/effect/<full_class_name>/args', methods=['GET'])
def effect_effectname_args_get(full_class_name):
    module_name, class_name = None, None
    try:
        module_name, class_name = getModuleAndClassName(full_class_name)
    except RuntimeError:
        abort(403)
    class_ = getattr(importlib.import_module(module_name),class_name)
    argspec = inspect.getargspec(class_.__init__)
    argsWithDefaults = dict(zip(argspec.args[-len(argspec.defaults):],argspec.defaults))
    result = argsWithDefaults.copy()
    result.update({key : None for key in argspec.args[1:len(argspec.args)-len(argspec.defaults)]}) # 1 removes self
    print(result)
    return jsonify(result)

def getModuleAndClassName(full_class_name):
    module_name, class_name = full_class_name.rsplit(".", 1)
    if module_name != "audioled.audio" and module_name != "audioled.effects" and module_name != "audioled.devices" and module_name != "audioled.colors":
        raise RuntimeError("Not allowed")
    return module_name, class_name

def inheritors(klass):
    subclasses = set()
    work = [klass]
    while work:
        parent = work.pop()
        for child in parent.__subclasses__():
            if child not in subclasses:
                subclasses.add(child)
                work.append(child)
    return subclasses


if __name__ == '__main__':

    app.run(debug=True)