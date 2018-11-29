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

@app.route('/connections', methods=['GET'])
def connections_get():
    connections = [con for con in fg._filterConnections]
    return jsonpickle.encode(connections)

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
    print("TODO: Add effect {}".format(request.json))
    full_class_name = request.json
    module_name, class_name = full_class_name.rsplit(".", 1)
    if module_name != "audioled.audio" and module_name != "audioled.effects" and module_name != "audioled.devices":
        abort(403)
    class_ = getattr(importlib.import_module(module_name), class_name)
    instance = class_()
    node = fg.addEffectNode(instance)
    return jsonpickle.encode(node)

@app.route('/effects', methods=['GET'])
def effects_get():
    childclasses = inheritors(effects.Effect)
    return jsonpickle.encode([child for child in childclasses])

@app.route('/effect/<full_class_name>/args', methods=['GET'])
def effect_effectname_args_get(full_class_name):
    print(full_class_name)
    module_name, class_name = full_class_name.rsplit(".", 1)
    if module_name != "audioled.audio" and module_name != "audioled.effects" and module_name != "audioled.devices":
        abort(403)
    class_ = getattr(importlib.import_module(module_name),class_name)
    argspec = inspect.getargspec(class_.__init__)
    result = {"args": argspec.args[1:]}
    return jsonify(result)


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