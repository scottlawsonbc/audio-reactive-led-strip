#!flask/bin/python
import importlib
import inspect
import time
import random
import threading
import atexit
import asyncio
import json
from flask import Flask, jsonify, abort, send_from_directory, request
from audioled import filtergraph
from audioled import audio
from audioled import effects
from audioled import colors
from audioled import devices
from audioled import configs
import jsonpickle
from timeit import default_timer as timer
from werkzeug.serving import is_running_from_reloader

num_pixels = 300
device = devices.FadeCandy('192.168.9.241:7890')
default_values = {}

POOL_TIME = 0.001 #Seconds

# lock to control access to variable
dataLock = threading.Lock()
# thread handler
ledThread = threading.Thread()
event_loop = None
# timing
current_time = None
last_time = None
# errors
errors = []

fg = filtergraph.FilterGraph(recordTimings=True)

audio_in = audio.AudioInput(num_channels=2)

fs = audio_in.getSampleRate()

fg.addEffectNode(audio_in)

led_out = devices.LEDOutput(device)
fg.addEffectNode(led_out)



#fg = configs.createSpectrumGraph(num_pixels, device)
#fg = configs.createMovingLightGraph(num_pixels, device)
#fg = configs.createVUPeakGraph(num_pixels, device)
fg = configs.createSwimmingPoolGraph(num_pixels, device)
#fg = configs.createDefenceGraph(num_pixels, device)

default_values['fs'] = fs
default_values['num_pixels'] = num_pixels/2 # specific for spectrum


# @app.route('/', methods=['GET'])
# def home():
#     return app.send_static_file('index.html')

def create_app():
    app = Flask(__name__,  static_url_path='/')

    def interrupt():
        print('cancelling LED thread')
        global ledThread
        ledThread.cancel()
        ledThread.join()
        print('LED thread cancelled')

    @app.route('/<path:path>')
    def send_js(path):
        return send_from_directory('resources', path)

    @app.route('/nodes', methods=['GET'])
    def nodes_get():
        global fg
        nodes = [node for node in fg._filterNodes]
        return jsonpickle.encode(nodes)



    @app.route('/node/<nodeUid>', methods=['GET'])
    def node_uid_get(nodeUid):
        global fg
        try:
            node = next(node for node in fg._filterNodes if node.uid == nodeUid)
            return jsonpickle.encode(node)
        except StopIteration:
            abort(404,"Node not found")

    @app.route('/node/<nodeUid>', methods=['DELETE'])
    def node_uid_delete(nodeUid):
        global fg
        try:
            node = next(node for node in fg._filterNodes if node.uid == nodeUid)
            fg.removeEffectNode(node.effect)
            return "OK"
        except StopIteration:
            abort(404, "Node not found")

    @app.route('/node/<nodeUid>', methods=['UPDATE'])
    def node_uid_update(nodeUid):
        global fg
        if not request.json:
            abort(400)
        try:
            node = next(node for node in fg._filterNodes if node.uid == nodeUid)
            #data =  json.loads(request.json)
            print(request.json)
            node.effect.updateParameter(request.json)
            return jsonpickle.encode(node)
        except StopIteration:
            abort(404, "Node not found")

    @app.route('/node/<nodeUid>/parameter', methods=['GET'])
    def node_uid_parameter_get(nodeUid):
        global fg
        try:
            node = next(node for node in fg._filterNodes if node.uid == nodeUid)
            return json.dumps(node.effect.getParameter())
        except StopIteration:
            abort(404, "Node not found")

    @app.route('/node', methods=['POST'])
    def node_post():
        global fg
        if not request.json:
            abort(400)
        full_class_name = request.json[0]
        parameters = request.json[1] # TODO: Don't pickle!
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
        global fg
        connections = [con for con in fg._filterConnections]
        return jsonpickle.encode(connections)

    @app.route('/connection', methods=['POST'])
    def connection_post():
        global fg
        if not request.json:
            abort(400)
        json = request.json
        connection = fg.addNodeConnection(json['from_node_uid'], int(json['from_node_channel']), json['to_node_uid'], int(json['to_node_channel']))
        
        return jsonpickle.encode(connection)

    @app.route('/connection/<connectionUid>', methods=['DELETE'])
    def connection_uid_delete(connectionUid):
        global fg
        try:
            connection = next(connection for connection in fg._filterConnections if connection.uid == connectionUid)
            fg.removeConnection(connection.fromNode.effect, connection.fromChannel, connection.toNode.effect, connection.toChannel)
            return "OK"
        except StopIteration:
            abort(404, "Node not found")

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
        
        result.update({key : default_values[key] for key in default_values if key in result})
        print(result)
        return jsonify(result)
    
    @app.route('/effect/<full_class_name>/parameter', methods=['GET'])
    def effect_effectname_parameters_get(full_class_name):
        module_name, class_name = None, None
        try:
            module_name, class_name = getModuleAndClassName(full_class_name)
        except RuntimeError:
            abort(403)
        class_ = getattr(importlib.import_module(module_name),class_name)
        return json.dumps(class_.getParameterDefinition())

    def getModuleAndClassName(full_class_name):
        module_name, class_name = full_class_name.rsplit(".", 1)
        if module_name != "audioled.audio" and module_name != "audioled.effects" and module_name != "audioled.devices" and module_name != "audioled.colors" and module_name != "audioled.audioreactive" and module_name != "audioled.generative":
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
    
    @app.route('/errors', methods=['GET'])
    def errors_get():
        result = {}
        for error in errors:
            result[error.node.uid] = error.message
        return json.dumps(result)

    @app.route('/configuration', methods=['GET'])
    def configuration_get():
        config = jsonpickle.encode(fg)
        return config
    
    @app.route('/configuration', methods=['POST'])
    def configuration_post():
        global fg
        if not request.json:
            abort(400)
        fg = jsonpickle.decode(request.json)
        return "OK"

    
    def processLED():
        global fg
        global ledThread
        global event_loop
        global last_time
        global current_time
        global errors
        dt = 0
        try:
            with dataLock:
                last_time = current_time
                current_time = timer()
                dt = current_time - last_time
                if event_loop is None:
                    event_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(event_loop)
                
                fg.update(dt, event_loop)
                fg.process()
                # clear errors (if any have occured in the current run, we wouldn't reach this)
                errors.clear()
                
        except filtergraph.NodeException as ne:
            print("NodeError: {}".format(ne))
            errors.clear()
            errors.append(ne)
        except Exception as e:
            print("Unknown error: {}".format(e))
        finally:
            #fg.printProcessTimings()
            # Set the next thread to happen
            real_process_time = timer() - current_time
            timeToWait = max(POOL_TIME, 0.01-real_process_time)
            ledThread = threading.Timer(timeToWait, processLED, ())
            ledThread.start()   

    def startLEDThread():
        # Do initialisation stuff here
        global ledThread
        global last_time
        global current_time
        # Create your thread
        current_time = timer()
        ledThread = threading.Timer(POOL_TIME, processLED, ())
        print('starting LED thread')
        ledThread.start()

    def loadConfig(json):
        global fg
        fg = jsonpickle.decode(json)

    

    # Initiate
    
    if is_running_from_reloader() == False: 
        startLEDThread()
    # When you kill Flask (SIGTERM), clear the trigger for the next thread
    atexit.register(interrupt)
    return app



    

if __name__ == '__main__':
    
    app = create_app()
    app.run(debug=False)
