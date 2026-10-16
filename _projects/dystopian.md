---
title: Dystopian Places
subtitle: Feel what your planet feels
idx: "00100"
order: 4
featured: true
year: "2018"
disciplines: [Interaction, Wearable, Electronics]
summary: A mask that restricts your breathing to match the oxygen levels of real hypoxic "dead zones" in the world's waters.
meta:
  - [Made in, "Barcelona"]
  - [Components, "Airflow-restricting mask + interactive world map"]
  - [Data, "Global hypoxic zones"]
  - [Tech, "Raspberry Pi, Node.js, MQTT, servo-driven diaphragm"]
  - [Mask, "Wireless, battery powered"]
hero: pf/dystopian/057
glyph: glyph/dystopian
films:
  - [ClmSuncslRw, "Teaser · sound by Pietro Sofi"]
gallery:
  - [pf/dystopian/056, "Two versions of the mask"]
  - [pf/dystopian/059, ""]
  - [pf/dystopian/061, ""]
  - [dystopian/mask, "The mask, render"]
  - [dystopian/map, "The virtual map of hypoxic zones"]
  - [pf/dystopian/055, ""]
  - [dystopian/wire, "The diaphragm mechanism"]
  - [dystopian/render, ""]
---
**Dystopian Places is a simulation designed to make you feel uncomfortable.**

Human development has brought us to where we are today, but not without consequences. One of the many repercussions of our actions is a phenomenon called water hypoxia: a detrimental decrease in the oxygen levels of a body of water. Areas with extreme hypoxia are commonly known as "dead zones" because of colossal die-offs. Although the process can occur naturally, the severity with which hypoxia is affecting our waters today is the result of irresponsible human development.

Dystopian Places invites users to attempt to breathe in a hypoxic area. The simulation has two main parts: a mask and a virtual map. The mask restricts the airflow the wearer receives. The reduced air intake mimics the oxygen deprivation of the area selected on the map, so the person wearing the mask understands what it would be like to be a fish living in a hypoxic zone.

On the technical side, a Raspberry Pi runs a Node server and an MQTT broker. The Node server serves a web page: the interface, a world map with markers in places with water hypoxia. When the user clicks a marker, a web socket notifies the server, which sends a message to the mask through MQTT. The mask is completely wireless and battery powered. When a message arrives, the value is translated into a servo position that closes or opens the diaphragm.

Dystopian Places hopes to be one piece of the puzzle in moving towards a more environmentally conscious world. We are at a point where action needs to be taken at a large scale, and sometimes we need to feel in order to understand.
