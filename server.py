#!flask/bin/python
from flask import Flask, jsonify
from audioled import filtergraph
from audioled import audio
from audioled import effects
import jsonpickle

num_pixels = 300

app = Flask(__name__)
fg = filtergraph.FilterGraph()

audio_in = audio.AudioInput()
fg.addEffectNode(audio_in)

movingLights = effects.MovingLightEffect(num_pixels, audio_in.getSampleRate())
fg.addEffectNode(movingLights)

fg.addConnection(audio_in,0,movingLights,0)

@app.route('/', methods=['GET'])
def home():
    return "Hello world!"

@app.route('/nodes', methods=['GET'])
def nodes_get():
    effects = [node.effect for node in fg._filterNodes]
    return jsonpickle.encode(effects)

@app.route('/connections', methods=['GET'])
def connections_get():
    connections = [con for con in fg._filterConnections]
    return jsonpickle.encode(connections)

if __name__ == '__main__':

    app.run(debug=True)