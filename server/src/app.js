import { DataSet, Network } from 'vis/index-network';
import 'vis/dist/vis-network.min.css';
var Configurator = require("vis/lib/shared/Configurator").default;
let util = require('vis/lib/util');
import { saveAs } from 'file-saver';
import audioInputIcon from '../img/audioled.audio.AudioInput.png'
import spectrumIcon from '../img/audioled.audioreactive.Spectrum.png'
import vuIcon from '../img/audioled.audioreactive.VUMeterPeak.png'
import movingIcon from '../img/audioled.audioreactive.MovingLight.png'
import colorWheelIcon from '../img/audioled.colors.ColorWheel.png'
import colorIcon from '../img/audioled.colors.Color.png'
import ledIcon from '../img/audioled.devices.LEDOutput.png'
import combineIcon from '../img/audioled.effects.Combine.png'
import appendIcon from '../img/audioled.effects.Append.png'
import glowIcon from '../img/audioled.effects.AfterGlow.png'
import mirrorIcon from '../img/audioled.effects.Mirror.png'
import swimmingPoolIcon from '../img/audioled.generative.SwimmingPool.png'

var icons = {
  'audioled.audio.AudioInput':audioInputIcon,
  'audioled.audioreactive.Spectrum':spectrumIcon,
  'audioled.audioreactive.MovingLight':movingIcon,
  'audioled.audioreactive.VUMeterPeak':vuIcon,
  'audioled.audioreactive.VUMeterRMS':vuIcon,
  'audioled.colors.ColorWheel': colorWheelIcon,
  'audioled.colors.StaticRGBColor': colorIcon,
  'audioled.devices.LEDOutput':ledIcon,
  'audioled.effects.Combine':combineIcon,
  'audioled.effects.Append':appendIcon,
  'audioled.effects.AfterGlow':glowIcon,
  'audioled.effects.Mirror':mirrorIcon,
  'audioled.generative.SwimmingPool':swimmingPoolIcon

}

var nodes, edges, data, options, network, configurator;

class Emitter {
  constructor(emit) {
    this.emit = emit
  }
}

class Body {
  constructor(emit) {
    this.emitter = new Emitter(emit);
  }
}

class ConfigurationWrapper {
  constructor(nodeUid, body, parameters, state, callback) {
    this.nodeUid = nodeUid;
    this.body = new Body(this.emit);
    this.configurator = configurator;
    this.configurator = new Configurator(this, body, parameters);
    this.configurator.setOptions(true);
    this.configurator.setModuleOptions(state);
    this.state = state;
    this.callback = callback;
  }

  async emit(identifier, data) {
    
  }

  clear() {
    util.recursiveDOMDelete(this.configurator.wrapper);
  }

  getState() {
    return this.state;
  }

  // is called by Configurator once values change
  async setOptions(data) {
    util.deepExtend(this.state, data['parameters']);
    this.callback(this.nodeUid, data);
  }

}

const createNodesFromBackend = async() => {
  const response = await fetch('./nodes');
  const json = response.json();
  json.then(values => values.forEach(element => {
    addVisNode(element);
  }));
}

const createEdgesFromBackend = async() => {
  const response = await fetch('./connections');
  const json = response.json();
  json.then(values => values.forEach(element => {
    addVisConnection(element);
  }));
}

function conUid(inout, index, uid) {
  return inout + '_' + index + '_' + uid;
}

function addVisNode(node) {
  var visNode = {};
  updateVisNode(visNode, node);
  nodes.add(visNode);
  var numOutputChannels = node['py/state']['numOutputChannels'];
  var numInputChannels = node['py/state']['numInputChannels'];
  for(var i=0; i<numOutputChannels; i++) {
    var outNode = {};
    outNode.group = 'out'
    outNode.id = conUid('out', i, visNode.id);
    outNode.label = `${i}`
    outNode.shape = 'circle'
    outNode.nodeType = 'channel'
    outNode.nodeUid = visNode.id;
    outNode.nodeChannel = i;
    nodes.add(outNode);
    edges.add({id: outNode.id, from: visNode.id, to: outNode.id});
  }
  for(var i=0; i < numInputChannels; i++) {
    var inNode = {};
    inNode.group = 'in';
    inNode.id = conUid('in', i, visNode.id);
    inNode.label = `${i}`;
    inNode.shape = 'circle';
    inNode.nodeType = 'channel';
    inNode.nodeUid = visNode.id;
    inNode.nodeChannel = i;
    nodes.add(inNode);
    edges.add({id: inNode.id, from:inNode.id, to: visNode.id});

  }
  
}

function updateVisNode(node, json) {
  console.debug('Update Vis Node:', json["py/state"]);
  var uid = json["py/state"]["uid"];
  var name = json["py/state"]["effect"]["py/object"];
  node.id = uid;
  node.label = name;
  node.shape = 'circularImage';
  node.group = 'ok';
  node.nodeType = 'node';
  var icon = icons[name];
  node.image = icon ? icon : '';
}

function addVisConnection(con) {
  var edge = {};
  updateVisConnection(edge, con);
  edges.add(edge);
}

function updateVisConnection(edge, json) {
  console.debug('Update Vis Connection:',json["py/state"]);
  var state = json["py/state"];
  edge.id = state["uid"];
  //edge.from = state["from_node_uid"];
  edge.from = conUid('out', state['from_node_channel'], state['from_node_uid'])
  edge.from_channel = state["from_node_channel"];
  //edge.to = state["to_node_uid"];
  edge.to = conUid('in', state['to_node_channel'], state['to_node_uid'])
  edge.to_channel = state["to_node_channel"];
  edge.arrows = 'to'
}

function createNetwork() {
  // create an array with nodes
  nodes = new DataSet();

  // create an array with edges
  edges = new DataSet();

  // create a network
  var container = document.getElementById('network');
  data = {
    nodes: nodes,
    edges: edges
  };
  options = {
    layout: {
      hierarchical: {
        enabled: true,
        levelSeparation: 70,
        direction: "UD",
        nodeSpacing: 80,
        sortMethod: 'directed',

      },
    },
    physics: {
      enabled: true,
      barnesHut: {
        gravitationalConstant: -2000,
        centralGravity: 0.3,
        springLength: 25,
        springConstant: 0.5,
        damping: 0.88,
        avoidOverlap: 1
      },
      hierarchicalRepulsion: {
        centralGravity: .05,
        nodeDistance: 150,
        springLength: 100,
        springConstant: 0.5,
        damping: 0.8,
      },
      forceAtlas2Based: {
        gravitationalConstant: -26,
        centralGravity: 0.005,
        springLength: 100,
        springConstant: 0.18
      },
      maxVelocity: 146,
      timestep: 0.35,
      solver: 'barnesHut',
      stabilization: {
        enabled: false,
        onlyDynamicEdges: true
      },
    },
    interaction: {
      navigationButtons: false,
      hover:true
    },
    manipulation: {
      enabled: true,
      addNode: function (data, callback) {
        // filling in the popup DOM elements
        document.getElementById('node-operation').innerHTML = "Add Node";
        addNode(data, clearNodePopUp, callback);
      },
      deleteNode: function(data, callback) {
        data.nodes.forEach(id => {
          deleteNodeData(id);
          console.debug("Deleted node",id);
        });
        callback(data);
        
      },
      addEdge: function (data, callback) {
        if (data.from == data.to) {
          callback(null);
          return;
        }
        var fromNode = nodes.get(data.from);
        var toNode = nodes.get(data.to);
        if (fromNode.nodeType == 'channel' && fromNode.group == 'out' && toNode.nodeType == 'channel' && toNode.group == 'in' ) {
          console.log("could add edge")
          postEdgeData(fromNode.nodeUid, fromNode.nodeChannel, toNode.nodeUid, toNode.nodeChannel, data, callback )
        } else {
          console.log("could not add edge")
        }
        return;
        document.getElementById('edge-operation').innerHTML = "Add Edge";
        editEdgeWithoutDrag(data, callback);
      },
      deleteEdge: function(data, callback) {
        data.edges.forEach(edgeUid => {
          var edge = edges.get(edgeUid);
          var fromNode = nodes.get(edge.from);
          var toNode = nodes.get(edge.to);
          if (fromNode.nodeType == 'channel' && fromNode.group == 'out' && toNode.nodeType == 'channel' && toNode.group == 'in' ) {
          
            deleteEdgeData(edgeUid);
            
            console.debug("Deleted edge",edge);
          } else {
            console.log("could not delete edge")
            // Remove edge from callback data
            var index = data.edges.indexOf(edgeUid);
            if (index > -1) {
              data.edges.splice(index, 1);
            }
          }
        });
        callback(data);
      }
    },
    nodes: {
      borderWidth:4,
      size:64,
      color: {
        border: '#222222',
        background: '#666666'
      },
      font:{color:'#eeeeee'}
    },
    edges: {
      color: 'lightgray'
    },
    groups: {
      ok: {
        color: {
          border: '#222222',
          background: '#666666'
        },
        mass: 10
      }, error: {
        color: {
          border: '#ee0000',
          background: '#666666'
        },
        mass: 10
      },
      in: {
        //physics: false
        mass: 1
      },
      out: {
        //physics: false
        mass: 1
      }
    }
  };
  network = new Network(container, data, options);
  network.on("selectNode", function (params) {
    document.getElementById('node-operation').innerHTML = "Edit Node";
    editNode(params.nodes[0], clearNodePopUp, clearNodePopUp);
  });
  network.on("deselectNode", function () {
    clearNodePopUp();
  });
}


function addNode(data, cancelAction, callback) {
  var effectDropdown = document.getElementById('node-effectDropdown');
  effectDropdown.style.display = 'inherit';
  var effectTable = document.getElementById('node-effectTable');
  effectTable.style.display = 'inherit';
  var saveBtn = document.getElementById('node-saveButton');
  saveBtn.style.display='inherit';
  var i;
  for(i = effectDropdown.options.length - 1 ; i >= 0 ; i--)
  {
    effectDropdown.remove(i);
  }
  const fetchEffects = async() => {
    const response = await fetch('./effects');
    const json = response.json();

    json.then(values => {
      values.forEach(element => {
        effectDropdown.add(new Option(element["py/type"]))
      });
      sortSelect(effectDropdown);
      effectDropdown.selectedIndex = 0;
      updateNodeArgs();
    }).catch( err => {
      showError("Error fetching effects. See console for details");
      console.error("Error fetching effects:",err);
    })
  }
  fetchEffects();

  document.getElementById('node-saveButton').onclick = saveNodeData.bind(this, data, callback);
  document.getElementById('node-cancelButton').onclick = cancelAction.bind(this, callback);
  document.getElementById('node-popUp').style.display = 'block';
  document.getElementById('node-effectDropdown').onchange = updateNodeArgs.bind(this);
  updateNodeArgs();

}

function editNode(uid, cancelAction, callback) {
  var effectDropdown = document.getElementById('node-effectDropdown');
  effectDropdown.style.display = 'none';
  var effectTable = document.getElementById('node-effectTable');
  effectTable.style.display = 'none';
  var saveBtn = document.getElementById('node-saveButton');
  saveBtn.style.display='none';
  
  const fetchAndShow = async () => {
    const stateResponse = await fetch('/node/'+uid);
    const stateJson = stateResponse.json();
    const response = await fetch('./node/'+uid+'/parameter');
    const json = response.json();
    Promise.all([stateJson, json]).then(result => { 
      var effect = result[0]["py/state"]["effect"]["py/state"];
      var values = result[1];
      configurator = new ConfigurationWrapper(uid, document.getElementById('node-configuration'), values, effect, async (nodeUid, data) => {
        console.log("emitting", data['parameters']);
        await fetch('./node/'+nodeUid, {
          method: 'UPDATE', // or 'PUT'
          body: JSON.stringify(data['parameters']), // data can be `string` or {object}!
          headers:{
            'Content-Type': 'application/json'
          }
        }).then(res => res.json())
        .then(node => {
          console.debug('Update node successful:', JSON.stringify(node));
          // updateVisNode(data, node); // TODO: Needed?
        })
        .catch(error => {
          showError("Error on updating node. See console for details.")
          console.error('Error on updating node:', error);
        })
      });
      
    }) ;
  }
  fetchAndShow();
  document.getElementById('node-cancelButton').onclick = cancelAction.bind(this, callback);
  document.getElementById('node-effectDropdown').onchange = null;
  document.getElementById('node-popUp').style.display = 'block';
}

function sortSelect(selElem) {
  var tmpAry = new Array();
  for (var i=0;i<selElem.options.length;i++) {
      tmpAry[i] = new Array();
      tmpAry[i][0] = selElem.options[i].text;
      tmpAry[i][1] = selElem.options[i].value;
  }
  tmpAry.sort();
  while (selElem.options.length > 0) {
      selElem.options[0] = null;
  }
  for (var i=0;i<tmpAry.length;i++) {
      var op = new Option(tmpAry[i][0], tmpAry[i][1]);
      selElem.options[i] = op;
  }
  return;
}

async function saveNodeData(data, callback) {
  // gather data
  var effectDropdown = document.getElementById('node-effectDropdown')
  var selectedEffect = effectDropdown.options[effectDropdown.selectedIndex].value;
  var options = configurator.getState();
  console.log(options);
  // Save node in backend
  await fetch('./node', {
    method: 'POST', // or 'PUT'
    body: JSON.stringify([selectedEffect, options]), // data can be `string` or {object}!
    headers:{
      'Content-Type': 'application/json'
    }
  }).then(res => res.json())
  .then(node => {
    console.debug('Create node successful:', JSON.stringify(node));
    updateVisNode(data, node);
    callback(data);
  })
  .catch(error => {
    showError("Error on creating node. See console for details");
    console.error('Error on creating node:', error);
  })
  .finally(() => {
    clearNodePopUp();
  });
}

async function updateNodeData(data, callback) {
  var options = document.getElementById('node-args').value;
  // Save node in backend
  await fetch('./node/'+data, {
    method: 'UPDATE', // or 'PUT'
    body: JSON.stringify(options), // data can be `string` or {object}!
    headers:{
      'Content-Type': 'application/json'
    }
  }).then(res => res.json())
  .then(node => {
    console.debug('Update node successful:', JSON.stringify(node));
    // updateVisNode(data, node); // TODO: Needed?
    callback(data);
  })
  .catch(error => {
    console.error('Error on updating node:', error);
  })
  .finally(() => {
    clearNodePopUp();
  });
}

async function deleteNodeData(id) {
  await fetch('./node/'+id, {
    method: 'DELETE'
  }).then(res => {
    console.debug('Delete node successful:', id);
  }).catch(error => {
    console.error('Error on deleting node:', error)
  })
}

function cancelNodeEdit(callback) {
  clearNodePopUp();
  callback(null);
}

function clearNodePopUp() {
  if(configurator) {
    configurator.clear();
  }
  document.getElementById('node-saveButton').onclick = null;
  document.getElementById('node-cancelButton').onclick = null;
  document.getElementById('node-popUp').style.display = 'none';
}

async function fetchNode(uid) {
  return fetch('./node/'+uid).then(response => response.json())
}

function editEdgeWithoutDrag(data, callback) {
  // clean up
  var fromChannelDropdown = document.getElementById('edge-fromChannelDropdown');
  var i;
  for(i = fromChannelDropdown.options.length - 1 ; i >= 0 ; i--)
  {
    fromChannelDropdown.remove(i);
  }
  var toChannelDropdown = document.getElementById('edge-toChannelDropdown');
  var i;
  for(i = toChannelDropdown.options.length - 1 ; i >= 0 ; i--)
  {
    toChannelDropdown.remove(i);
  }

  var fromNodeUid = data.from;
  var toNodeUid = data.to;

  const fetchFromNode = async() => {
    var node = await fetchNode(fromNodeUid);
    var numFromChannels = node['py/state']['numOutputChannels'];
    for(var i=0; i<numFromChannels; i++) {
      fromChannelDropdown.add(new Option(i));
    }
  }
  fetchFromNode();
  const fetchToNode = async() => {
    var node = await fetchNode(toNodeUid);
    var numToChannels = node['py/state']['numInputChannels'];
    for(var i=0; i<numToChannels; i++) {
      toChannelDropdown.add(new Option(i));
    }
  }
  fetchToNode();

  // filling in the popup DOM elements
  document.getElementById('edge-saveButton').onclick = saveEdgeData.bind(this, data, callback);
  document.getElementById('edge-cancelButton').onclick = cancelEdgeEdit.bind(this,callback);
  document.getElementById('edge-popUp').style.display = 'block';
}

function clearEdgePopUp() {
  document.getElementById('edge-saveButton').onclick = null;
  document.getElementById('edge-cancelButton').onclick = null;
  document.getElementById('edge-popUp').style.display = 'none';
}
function cancelEdgeEdit(callback) {
  clearEdgePopUp();
  callback(null);
}
async function saveEdgeData(data, callback) {
  if (typeof data.to === 'object') {
    data.to = data.to.id
  }
  if (typeof data.from === 'object') {
    data.from = data.from.id
  }

  var fromChannelDropdown = document.getElementById('edge-fromChannelDropdown');
  var from_node_channel = fromChannelDropdown.options[fromChannelDropdown.selectedIndex].value;
  var toChannelDropdown = document.getElementById('edge-toChannelDropdown');
  var to_node_channel = toChannelDropdown.options[toChannelDropdown.selectedIndex].value;
  await postEdgeData(data.from, from_node_channel, data.to, to_node_channel, data, callback);
}
async function postEdgeData(from_node_uid, from_node_channel, to_node_uid, to_node_channel, data, callback) {
  var postData = {from_node_uid: from_node_uid, from_node_channel: from_node_channel, to_node_uid: to_node_uid, to_node_channel: to_node_channel};

  // Save node in backend
  await fetch('./connection', {
    method: 'POST', // or 'PUT'
    body: JSON.stringify(postData), // data can be `string` or {object}!
    headers:{
      'Content-Type': 'application/json'
    }
  })
  .then(res => res.json())
  .then(
    connection => {
      console.debug('Create connection successful:',data);
      updateVisConnection(data, connection)
      callback(data);
    })
  .catch(error => {
    console.error('Error on creating connection:', error);
  })
  .finally(() => {
    clearEdgePopUp();
  });
}

async function deleteEdgeData(data) {
  var edge = edges.get(data);
  var id = edge.id;
  await fetch('./connection/'+id, {
    method: 'DELETE'
  }).then(res => {
    console.debug('Delete connection successful:', id);
  }).catch(error => {
    console.error('Error on deleting connection:', error)
  })
}

async function updateNodeArgs() {
  var effectDropdown = document.getElementById('node-effectDropdown');
  var selectedEffect = effectDropdown.options[effectDropdown.selectedIndex].value;

  const response = await fetch('./effect/'+selectedEffect+'/parameter');
  const json = response.json();
  const defaultReponse = await fetch('./effect/'+selectedEffect+'/args');
  const defaultJson = defaultReponse.json();
  Promise.all([json,defaultJson]).then(result => { 
    var parameters = result[0];
    var defaults = result[1];
    console.log(parameters);
    console.log(defaults);
    configurator = new ConfigurationWrapper(selectedEffect, document.getElementById('node-configuration'), parameters, defaults, async (nodeUid, data) => {
      // do nothing
    });
  }).catch(err => {
    showError("Error updating node configuration. See console for details.");
    console.err("Error updating node configuration:",err);
  });
}

createNetwork();
createNodesFromBackend();
createEdgesFromBackend();
createOther();



function createOther() {
  document.getElementById('config-saveButton').onclick = saveConfig.bind(this);
  document.getElementById('file-input').addEventListener('change', readSingleFile, false);
}

function readSingleFile(e) {
  var file = e.target.files[0];
  if (!file) {
    return;
  }
  var reader = new FileReader();
  reader.onload = function(e) {
    var contents = e.target.result;
    displayContents(contents);
  };
  reader.readAsText(file);
}

async function saveConfig() {
  try {
    var isFileSaverSupported = !!new Blob;
  } catch (e) {
    console.error("FileSaver not supported")
  }
  await fetch('./configuration').then(response => response.json()).then(json => {
    var blob = new Blob([JSON.stringify(json, null, 4)], {type: "text/plain;charset=utf-8"});
    saveAs(blob, "configuration.json");
  })
}

function displayContents(contents) {
  console.log(contents);
  const postData = async () => fetch('./configuration', {
    method: 'POST', // or 'PUT'
    body: JSON.stringify(contents), // data can be `string` or {object}!
    headers:{
      'Content-Type': 'application/json'
    }
  })
  .then(
    () => {
      console.log("Successfully loaded");
      location.reload();
    })
  .catch(error => {
    console.error('Error on loading configuration:', error);
  })
  postData();
}

async function loadConfig() {
  await fetch()
}

function showError(message) {
  var error = document.getElementById('alert');
  var errorInfo = document.getElementById('alert-info');
  error.style.display='inherit';
  errorInfo.innerHTML = "<strong>Danger!</strong> "+ message;
}

function hideError() {
  var error = document.getElementById('alert');
  error.style.display='none';
}

window.setInterval(function(){
  /// call your function here
  const fetchErrors = async() => fetch('./errors').then(response => response.json()).then(json => {
    for (var entry in nodes.get()) {
      var node = nodes.get()[entry];
      if(node.group == 'error') {
        node.group = 'ok';
        nodes.update(node);
      }
    }
    var hasErrors = false;
    for (var key in json) {
      // check if the property/key is defined in the object itself, not in parent
      
      if (json.hasOwnProperty(key)) {           
          var node = nodes.get(key);
          node.group = 'error';
          nodes.update(node);
          console.log(json[key])
          showError(json[key])
          hasErrors = true;
      } 
    }
    if (!hasErrors) {
      hideError();
    }
  });
  fetchErrors();
}, 2000);