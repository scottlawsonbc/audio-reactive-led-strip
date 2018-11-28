#!flask/bin/python
from flask import Flask, jsonify, abort, send_from_directory
from audioled import filtergraph
from audioled import audio
from audioled import effects
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

if __name__ == '__main__':

    app.run(debug=True)