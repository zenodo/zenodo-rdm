#!/usr/bin/env bash
# -*- coding: utf-8 -*-

# create admin role
invenio roles create admin
invenio access allow superuser-access role admin
# and then add the role to your user
invenio roles add ppanero@cern.ch admin  # pablo
invenio roles add zacharias.zacharodimos@cern.ch admin  # zach
invenio roles add manuel.alejandro.de.oliveira.da.costa@cern.ch admin  # manuel
invenio roles add a.ioannidis@cern.ch admin  # alex