---
title: Playball
subtitle: Light that is passed on
idx: "00010"
order: 2
featured: true
year: "2018"
disciplines: [Installation, Electronics, Light]
summary: 64 suspended spheres, each a wireless module with collision detection and light. When one ball hits another, the light is passed on.
meta:
  - [Shown at, "LLUM BCN light festival, Barcelona"]
  - [Scale, "64 independent modules"]
  - [Tech, "Wireless modules, sound-triggered collision detection, LEDs"]
  - [Software, "Node.js server, MQTT, web interface for animations"]
  - [Credits, "Team project"]
hero: playball/cloud
hero_video: playball-drift
ai_motion: true
glyph: glyph/playball
films:
  - [fppi2PifkpE, "Llum festival Barcelona 2018 · video by Billy Craigan for IAAC"]
  - [bhjlvhkh3pk, "Testing the installation before the festival"]
gallery:
  - [pf/playball/179, ""]
  - [pf/playball/180, ""]
  - [pf/playball/181, ""]
  - [playball/visitors, ""]
  - [pf/playball/182, ""]
  - [pf/playball/178, ""]
  - [pf/playball/176, "64 modules, suspended"]
  - [pf/playball/177, ""]
  - [pf/playball/174, "Installing"]
  - [pf/playball/172, "Assembly"]
  - [pf/playball/173, "Custom boards"]
  - [pf/playball/175, "One of the 64 modules, opened"]
---
Playball is an installation we developed for the LLUM light festival in Barcelona. It consists of 64 balls suspended in the air. Each ball is an independent module with full wireless connectivity, sound-triggered collision detection and LED lights.

As one ball hits another, light is passed on, revealing the playful nature of the installation.

All the balls are connected to a Node.js server, with a web interface for making custom animations or watching which ball is active at any given moment. We chose MQTT as the communication protocol because it is very lightweight and offers quality of service to ensure packet delivery.
