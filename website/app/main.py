import flask
from flask import request, jsonify, render_template
from datetime import datetime

import pandas as pd
import numpy as np
import json
import hashlib

import random

import os
from os import path

app = flask.Flask(__name__)
app.config["DEBUG"] = True



# Create some test data for our catalog in the form of a list of dictionaries.


@app.route('/', methods=['GET'])
@app.route('/index')
def home():
    user = {'username': 'chris'}
    return render_template('index.html', title='Home', user=user)
@app.route('/observe', methods=['GET'])
def observe():
    d = request.values.to_dict()
    ra, dec, fov = 5,5,60
    if 'ra' in d:
        ra = d['ra']
    if 'dec' in d:
        dec = d['dec']
    if 'fov' in d:
        fov = d['fov']
    coords = {'ra':ra,'dec':dec,'fov':fov}
    user = d['user']
    return render_template('observe.html', title='Observe', user=user, coords=coords)


if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True,port=int("80"))
