#!/usr/bin/python

from array import array
import csv

import set_common as s

def JSDataView(type):
  if type == "u8":
    return "Uint8"
  if type == "s8":
    return "Int8"
  if type == "u16":
    return "Uint16"
  if type == "s16":
    return "Int16"
  if type == "u32":
    return "Uint32"
  if type == "s32":
    return "Int32"
  if type == "float":
    return "Float32"
  if type == "double":
    return "Float64"

def JSDataViewSize(type):
  if type == "u8":
    return "1"
  if type == "s8":
    return "1"
  if type == "u16":
    return "2"
  if type == "s16":
    return "2"
  if type == "u32":
    return "4"
  if type == "s32":
    return "4"
  if type == "float":
    return "4"
  if type == "double":
    return "8"

f = open("../web_configurator/blechars.js","w")
f.write("""\
//
//
//  !!! THIS FILE IS AUTOMATICALLY GENERATED, DO NOT EDIT DIRECTLY !!!
//
//  Modify /utils/settings.csv and execute buildsettings.py to generate this source file
//

let radioService;
let gattServer;
let commandCharacteristic;
""")

# Read the settings
s.readSettings()

# Data Storage Variables
for row in s.settings:
  if row[s.colbleaddr].strip() != "":
    name = row[s.colname].strip()
    addr = row[s.colbleaddr].upper().strip()
    f.write("let " + name + "_promise;\n")
    f.write("let " + name + "_value;\n")

# Update Fields Function
f.write("\nfunction updateFields()\n{\n")
for row in s.settings:
  if row[s.colbleaddr].strip() != "":
    name = row[s.colname].strip()
    f.write("  $(\"#inp_" + name + "\").val("+ name + "_value);\n")
f.write("}\n\n")

# Field Changed, Upload to Tracker
for row in s.settings:
  if row[s.colbleaddr].strip() != "":
    name = row[s.colname].strip()
    addr = row[s.colbleaddr].upper().strip()
    txt = """\
$('#inp_{name}').on('change', function() {{
  const buffer = new ArrayBuffer({arrsize});
  new DataView(buffer).set{type}(0, $('#inp_{name}').val(), true)
  {name}_promise.writeValue(buffer);
  updateParameter('{name}',$('#inp_{name}').val())
}});
""".format(name = name, type=JSDataView(row[s.coltype]), arrsize = JSDataViewSize(row[s.coltype]))
    f.write(txt);
f.write("\n")

f.write("""
function connectToHT() {
  if (radioService == null) {
    navigator.bluetooth.requestDevice({
      filters: [{
        services: [0xFFFA]  // Headtracker Bluetooth Configuration Service
      }]
    })
    .then(device => {
      btConnectionStatus('Connecting to HeadTracker...');
      showLoader();
      return device.gatt.connect();
    })
    .then(server => {
      gattServer = server;
      return gattServer.getPrimaryService(0xFFFA);
    })
    .then(service => {
      radioService = service;
      return radioService.getCharacteristic(0xFF00); // Get command characteristic
    })
    .then(characteristic => {
      commandCharacteristic = characteristic;
      btConnectionStatus('Got the Command Characteristic');
      readValues(btConnectionStatus, connectionEstablished);
    })
    .catch(error => {
      console.error(error);
      connectionFault(error);
    })
  }
}

function readValues(messageFunc, onCompleted) {
  if(gattServer == null) {
    console.log("No Gatt Server");
    return;
  }

  if(gattServer.connected == false) {
    console.log("Gatt Server not Connected");
    return;
  }

  radioService.getCharacteristic(0xF000)""")

first = True
_lastname = ""
_lasttype = ""
_lastround = ""
_name = ""
_addr = ""
for row in s.settings:
  if row[s.colbleaddr].strip() != "":
    _name = row[s.colname].strip()
    _addr = row[s.colbleaddr].upper().strip()
    _type = row[s.coltype]
    _round = row[s.colround]
    _roundto = ""
    if _lasttype.lower() == "float":
      _roundto = ".toFixed(" + str(int(_lastround) - 1) + ")"

    if first == True:
      first = False
    else:
      txt = """\
  .then(characteristic => {{
    {lname}_promise = characteristic;
    return {lname}_promise.readValue();
  }})
  .then(value => {{
    messageFunc(' Got {lname}');
    {lname}_value = value.get{jtype}(0, true){roundto};
    return radioService.getCharacteristic(0x{addr}); // Get {name} characteristic
  }})
""".format(name = _name, lname = _lastname, addr = _addr, jtype = JSDataView(_lasttype), roundto = _roundto)
      f.write(txt)
    _lastname = _name
    _lasttype = _type
    _lastround = _round

if _lasttype.lower() == "float":
  _lastround = ".toFixed(" + str(int(_lastround) - 1) + ")"
txt = """\
  .then(characteristic => {{
    {lname}_promise = characteristic;
    return {lname}_promise.readValue();
  }})
    .then(value => {{
    {lname}_value = value.get{jtype}(0, true){roundto};
    messageFunc("Completed");
    if(onCompleted != null)
      onCompleted()
    updateFields();
  }})
  .catch(error => {{ console.error(error); connectionFault(error); return true;}});
""".format(name = _name, lname = _lastname, addr = _addr, jtype = JSDataView(_lasttype), roundto = _lastround)
f.write(txt)

f.write("}\n")
f.close()

print("Generated WebBle Settings File blechars.js")


# BUILD THE HTML SETTINGS LIST

# Data Storage Variables
f = open("../web_configurator/settings.html","w")
f.write("<table id='settingsTable'>\n")
for row in s.settings:
  if row[s.colbleaddr].strip() != "":
    name = row[s.colname].strip()
    min = row[s.colmin]
    max = row[s.colmax]
    desc = row[s.coldesc]
    type = row[s.coltype]
    stepvalue = ""
    if type.lower() == "float":
      stepvalue = "step='" + str(1.0 / pow(10,int(row[s.colround])-1)) + "' "
    f.write("<tr><td>" + desc + "</td><td><input type='number' class='htInputField' " + stepvalue +  "id='inp_" + name + "'></td></tr>\n")
f.write("</table>\n")
f.close()

print("Generated WebBle Settings File settings.html")