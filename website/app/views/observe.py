from flask import Blueprint, render_template, request

import pandas as pd
import numpy as np
import json
import hashlib
import random

import os
from astropy import units as u
from astropy.coordinates import SkyCoord
import sqlalchemy as db

MYSQL_USER = os.environ['MYSQL_USER']
MYSQL_PASSWORD = os.environ['MYSQL_PASSWORD']
MYSQL_HOST = os.environ['MYSQL_HOST']
MYSQL_PORT = os.environ['MYSQL_PORT']
MYSQL_DB = os.environ['MYSQL_DB']

connect = 'mysql+pymysql://'+MYSQL_USER+':'+MYSQL_PASSWORD+'@'+MYSQL_HOST+':'+MYSQL_PORT+'/'+MYSQL_DB
engine = db.create_engine(connect)
connection = engine.connect()

def querytodict(resultproxy):
    return [{column: value for column, value in rowproxy.items()} for rowproxy in resultproxy]

observe_blueprint = Blueprint('observe',__name__)

@observe_blueprint.route('/observe', methods=['GET'])
def observe():
    d = request.values.to_dict()
    ra = float(d['ra'])
    dec = float(d['dec'])
    fov = d['fov']
    query = "select * from observers where id = " + str(d['obs'])
    resultproxy = engine.execute(query)
    obsdict = querytodict(resultproxy)
    if d['key'] != obsdict[0]['key']:
        return "key doesn't match observer!"
    c = SkyCoord(ra=ra*u.degree, dec=dec*u.degree, frame='icrs')
    coords = {'ra':ra,'dec':dec,'fov':fov,'ra_dec':c.to_string('hmsdms')}
    if d['key'] != obsdict[0]['key']:
        return "key doesn't match observer!"
    checktime = "select time_clicked from matches where event_id = " + d['event'] + " AND obs_id = " + d['obs']
    timedict = querytodict(engine.execute(checktime))
    print(timedict)
    if timedict[0]['time_clicked'] is None:
        query = "update matches set time_clicked = CURRENT_TIMESTAMP where event_id = " + d['event'] + " AND obs_id = " + d['obs']
        engine.execute(query)
    user = obsdict[0]['name'][15:]
    query = "select * from galaxies where id = " + str(d['gal'])
    resultproxy = engine.execute(query)
    galdict = querytodict(resultproxy)
    galaxy = galdict[0]['name']
    return render_template('observe.html', title='Observe', user=user, obs=obsdict[0], coords=coords, galaxy=galdict[0], event=d['event'])

