import { DataSet, Network } from 'vis/index-network';
import 'vis/dist/vis-network.min.css';

var nodes, edges, data, options, network;

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

function addVisNode(node) {
  var visNode = {};
  updateVisNode(visNode, node);
  nodes.add(visNode);
}

function updateVisNode(node, json) {
  console.debug('Update Vis Node:', json["py/state"]);
  var uid = json["py/state"]["uid"];
  var name = json["py/state"]["effect"]["py/object"];
  node.id = uid;
  node.label = name;
  node.shape = 'box';
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
  edge.from = state["from_node_uid"];
  edge.from_channel = state["from_node_channel"];
  edge.to = state["to_node_uid"];
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
    interaction: {
      navigationButtons: false,
      hover:true
    },
    manipulation: {
      enabled: true,
      addNode: function (data, callback) {
        // filling in the popup DOM elements
        document.getElementById('node-operation').innerHTML = "Add Node";
        editNode(data, clearNodePopUp, callback);
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
        document.getElementById('edge-operation').innerHTML = "Add Edge";
        editEdgeWithoutDrag(data, callback);
      },
      deleteEdge: function(data, callback) {
        data.edges.forEach(data => {
          deleteEdgeData(data);
          console.debug("Deleted edge",data);
        });
        callback(data);
      }
    }
  };
  network = new Network(container, data, options);
  network.on("selectNode", function (params) {
    showNodeInfo(params.nodes[0]);
  });
  network.on("deselectNode", function () {
    hideNodeInfo();
  });
}

function showNodeInfo(uid) {
  document.getElementById('infoPanel').style.display = 'block';
  const fetchAndShow = async () => {
    const response = await fetch('./node/'+uid);
    const json = response.json();
    json.then(values => { 
      var effect = values["py/state"]["effect"];
      document.getElementById('infoPanel').innerHTML = '<h2>Node Info:</h2>' + JSON.stringify(effect, null, 4);
    }) ;
  }
  fetchAndShow();
}

function hideNodeInfo() {
  document.getElementById('infoPanel').style.display = 'none';
}

function editNode(data, cancelAction, callback) {
  var effectDropdown = document.getElementById('node-effectDropdown');
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
    })
  }
  fetchEffects();

  document.getElementById('node-args').value = "";
  document.getElementById('node-saveButton').onclick = saveNodeData.bind(this, data, callback);
  document.getElementById('node-cancelButton').onclick = cancelAction.bind(this, callback);
  document.getElementById('node-popUp').style.display = 'block';
  document.getElementById('node-effectDropdown').onchange = updateNodeArgs.bind(this);
  updateNodeArgs();

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
  var options = document.getElementById('node-args').value;

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
    console.error('Error on creating node:', error);
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

  var postData = {from_node_uid: data.from, from_node_channel: from_node_channel, to_node_uid: data.to, to_node_channel: to_node_channel};

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
  await fetch('./effect/'+selectedEffect+'/args')
    .then(response => response.json())
    .then(json => {
      console.debug('NodeArgs:',json);
      document.getElementById('node-args').value = JSON.stringify(json, null, 4);
    });
  console.log(selectedEffect);
}

createNetwork();
createNodesFromBackend();
createEdgesFromBackend();