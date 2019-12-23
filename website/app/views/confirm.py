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

confirm_blueprint = Blueprint('confirm',__name__)

@confirm_blueprint.route('/confirm', methods=['GET'])
def confirm():
    d = request.values.to_dict()
    query = "select * from observers where id = " + str(d['obs'])
    obsdict = querytodict(engine.execute(query))
    if d['key'] != obsdict[0]['key']:
        return "key doesn't match observer!"
    if d['key'] != obsdict[0]['key']:
        return "key doesn't match observer!"
    checktime = "select time_confirmed from matches where event_id = " + d['event'] + " AND obs_id = " + d['obs']
    timedict = querytodict(engine.execute(checktime))
    if timedict[0]['time_confirmed'] is None:
        query = "update matches set time_confirmed = CURRENT_TIMESTAMP where event_id = " + d['event'] + " AND obs_id = " + d['obs']
        engine.execute(query)
    user = obsdict[0]['name'][15:]
    query = "select * from galaxies where id = " + str(d['gal'])
    galdict = querytodict(engine.execute(query))
    galaxy = galdict[0]['name']
    if d['confirm'] == '1':
        query = "update matches set source_found = 1 where event_id = " + d['event'] + " AND obs_id = " + d['obs']
        engine.execute(query)
        return render_template('yes.html', title='Confirm')
    query = "update matches set source_found = 0 where event_id = " + d['event'] + " AND obs_id = " + d['obs']
    engine.execute(query)
    return render_template('no.html', title='Confirm')
