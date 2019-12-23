import gcn
import healpy as hp
import copy
import pandas as pd
from datetime import datetime
import ephem
from astropy.io import fits
from ligo.skymap.postprocess import find_greedy_credible_levels
import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
import sqlalchemy as sql
import time
import slack
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from cartopy.feature.nightshade import Nightshade
import wget
from ligo.skymap.tool.ligo_skymap_plot import main as skyplot
from astropy.utils.data import download_file
import os

############################
# Config
############################
test_alert = False
check_sun = True
check_moon = False
check_minalt = False
plot_map = True
prob_check = 0.9
write_event = True
max_alt = ephem.degrees('30')
max_sun = ephem.degrees('0')
min_alt = ephem.degrees('-20')
logfile = 'event_log.log'
event_types = ['NSBH', 'BNS']
send_slack = True
SLACK_BOT_TOKEN = os.environ['SLACK_BOT_TOKEN']
SLACK_CHANNEL = os.environ['SLACK_CHANNEL']
MYSQL_USER = os.environ['MYSQL_USER']
MYSQL_PASSWORD = os.environ['MYSQL_PASSWORD']
MYSQL_HOST = os.environ['MYSQL_HOST']
MYSQL_PORT = os.environ['MYSQL_PORT']
MYSQL_DB = os.environ['MYSQL_DB']
WEBSITE_URL = os.environ['WEBSITE_URL']

connect_string = 'mysql+pymysql://'+MYSQL_USER+':'+MYSQL_PASSWORD+'@'+MYSQL_HOST+':'+MYSQL_PORT+'/'+MYSQL_DB

galinfov = False

############################
# Functions
############################
def getRADec(hpx, ipix):
    npix = len(hpx)
    nside = hp.npix2nside(npix)
    theta, phi = hp.pix2ang(nside, ipix)
    ra = np.rad2deg(phi)
    dec = np.rad2deg(0.5 * np.pi - theta)
    return SkyCoord(ra=ra * u.degree, dec=dec * u.degree, frame='icrs')


def getPixel(hpx, ra, dec):
    npix = len(hpx)
    nside = hp.npix2nside(npix)
    theta = 0.5 * np.pi - np.deg2rad(dec)
    phi = np.deg2rad(ra)
    ipix = hp.ang2pix(nside, theta, phi)
    return ipix


if send_slack:
    slack_client = slack.WebClient(token=SLACK_BOT_TOKEN)


################################################
# GCN HANDLER
################################################

# Function to call every time a GCN is received.
# Run only for notices of type
# LVC_PRELIMINARY, LVC_INITIAL, or LVC_UPDATE.
@gcn.handlers.include_notice_types(
    gcn.notice_types.LVC_PRELIMINARY,
    gcn.notice_types.LVC_INITIAL,
    gcn.notice_types.LVC_UPDATE,
    gcn.notice_types.LVC_RETRACTION)
def process_gcn(payload, root):
    if write_event:
        event_log = open(logfile, 'a+')
    # Respond only to 'test' events.
    # VERY IMPORTANT! Replace with the following code
    # to respond to only real 'observation' events.
    print("starting process")
    print(datetime.utcnow())
    if write_event:
        event_log.write("starting process")
        event_log.write('\n')
        event_log.write(root.attrib['role'])
        event_log.write('\n')
    print(root.attrib['role'])

    """ Uncomment when we only want to do real observations
    if root.attrib['role'] != 'observation':
       return
    """

    # Read all of the VOEvent parameters from the "What" section.

    params = {elem.attrib['name']:
                  elem.attrib['value']
              for elem in root.iterfind('.//Param')}

    # Respond only to 'CBC' events. Change 'CBC' to "Burst'
    # to respond to only unmodeled burst events.
    print(params['Group'])
    if write_event:
        event_log.write(params['Group'])
        event_log.write('\n')
    if params['Group'] != 'CBC':
        print('not CBC')
        return
    if params['AlertType'] != 'Preliminary':
        print('not Preliminary')
        return
    if 'Pkt_Ser_Num' in params:  # Test events send same event twice, only choose first one.
        check = float(params['Pkt_Ser_Num'])
        if check > 1.1:
            return

    """ COMPLETE TO DEFINE WHICH EVENTS WE ARE LOOKING FOR
    if 'BNS' in params:
       check = float(params['BNS'])
       if  check < 50.0:
          print("not BNS event, skipping")
          return
    else:
       print("not BNS event, skipping")
       return
    """
    # Print all parameters.
    for key, value in params.items():
        print(key, '=', value)
        if write_event:
            event_log.writelines(str(key + '=' + value))

    if 'skymap_fits' in params:
        # Read the HEALPix sky map and the FITS header.i
        skymap, header = hp.read_map(params['skymap_fits'], h=True, verbose=False)
        header = dict(header)

        # Print some values from the FITS header.
        print('Distance =', header['DISTMEAN'], '+/-', header['DISTSTD'])
        if write_event:
            event_log.writelines('Distance =' + str(header['DISTMEAN']) + '+/-' + str(header['DISTSTD']))
            event_log.write('\n')

        # write event information to SQL
        datadict = {'gracedb_id': [params['GraceID']], 'link': [params['EventPage']], 'dist': [header['DISTMEAN']],
                    'dist_err': [header['DISTSTD']]}
        sql_engine = sql.create_engine(connect_string)
        headers = ['gracedb_id', 'link', 'dist', 'dist_err']
        dtypes = {'gracedb_id': 'str', 'link': 'str', 'dist': 'float64', 'dist_err': 'float64'}
        df = pd.DataFrame.from_dict(datadict)
        df.to_sql('events', sql_engine, if_exists='append', index=False)

        # get event ID back
        query = "select * from events ORDER BY 'ID' DESC"
        df = pd.read_sql_query(query, sql_engine)
        event = df['ID'].iloc[-1]

        credible_levels = find_greedy_credible_levels(skymap)

        if send_slack:
            slackmsg = ""
            for key, value in params.items():
                slackmsg = slackmsg + str(key) + '=' + str(value) + '\n'

            slack_client.chat_postMessage(channel=SLACK_CHANNEL, text=slackmsg)
        # get df of galaxies from SQL
        query = "select * from galaxies"
        galaxies = pd.read_sql_query(query, sql_engine)
        gal_ipix = getPixel(skymap, galaxies['ra'], galaxies['dec'])
        """
        offset = ephem.Observer()
        offset.lat = '0.0'
        offset.long = '180'
        offset.date = datetime.utcnow()
        offangle = float(offset.sidereal_time() * 180 / np.pi)
        """
        if plot_map:
            #ax = plt.axes(projection=ccrs.Mollweide(central_longitude=-1 * offangle))
            ax = plt.axes(projection=ccrs.Mollweide())
            ax.stock_img()

        galaxies['credible'] = credible_levels[gal_ipix]
        banana_galaxies = galaxies[(galaxies.credible <= prob_check)]
        banana_galaxies.sort_values(by=['credible'], inplace=True)

        #get list of observatories from SQL
        query = "select * from observers"
        observatories = pd.read_sql_query(query, sql_engine)
        #Find Sun RA/DEC
        sun = ephem.Sun()
        #setup pyephem observer
        telescope = ephem.Observer()
        telescope.date = datetime.utcnow()
        #create a copy of galaxy list in case it ends up depleted
        galaxy_list = copy.deepcopy(banana_galaxies)
        galaxy_list = galaxy_list.values.tolist()
        galaxy_depleted = False
        slackmsg = ''
        matches = []
        slack_count = 0
        for x in range(0, len(observatories)):
            extra_matches = []
            # Check if all galaxies have been assigned, if so start assigning duplicates
            if len(galaxy_list) == 0:
                galaxy_list = copy.deepcopy(banana_galaxies)
                galaxy_list = galaxy_list.values.tolist()
                galaxy_depeleted = True
            telescope.lat = str(observatories['lat'][x]).strip()
            telescope.long = str(observatories['lon'][x]).strip()
            sun.compute(telescope)
            # if sun is up, observatory can be skipped
            if check_sun:
                if sun.alt > max_sun:
                    # print(str(observatories['Code'][x]) + " skipped, Sun is up")
                    continue
            for i in range(0, len(galaxy_list)):
                star = ephem.FixedBody()
                star._ra = ephem.degrees(str(galaxy_list[i][2]))
                star._dec = ephem.degrees(str(galaxy_list[i][3]))
                star.compute(telescope)

                # if the first object is more than 20 degrees below elevation, unlikely any objects will be higher than 45 degrees
                if check_minalt:
                    if star.alt < min_alt:
                        # print(str(observatories['Code'][x]) + " skipped " + str(star.alt) + " is less than -20 degrees")
                        break
                # assign galaxy to observer
                if star.alt > max_alt:
                    matches.append(
                        {'event_id': event, 'obs_ID': observatories['ID'][x], 'galaxy_id': galaxy_list[i][0]})
                    # print(galaxy_list[i])
                    listing = WEBSITE_URL+'/observe?key=' + str(
                        observatories['key'][x]) + '&event=' + str(event) + '&obs=' + str(
                        observatories['ID'][x]) + '&gal=' + str(galaxy_list[i][0]) + '&ra=' + str(
                        galaxy_list[i][2]) + '&dec=' + str(galaxy_list[i][3]) + '&fov=' + str(observatories['fov'][x])
                    print(listing)
                    if write_event:
                        event_log.writelines(listing)
                        event_log.write('\n')
                    #only writing the first 5 urls to slack
                    if send_slack:
                        if slack_count < 5:
                            slack_count += 1
                            slackmsg = slackmsg + listing + '\n'
                    #find extra galaxies within FOV
                    j = i+1
                    y = []
                    print(len(galaxy_list[j:]))
                    if galinfov:
                        for z in range(j,len(galaxy_list)):
                            extra = ephem.FixedBody()
                            extra._ra = ephem.degrees(str(galaxy_list[z][2]))
                            extra._dec = ephem.degrees(str(galaxy_list[z][3]))
                            extra.compute(telescope)
                            sep = float(ephem.separation(star,extra))*180/np.pi
                            if sep < 0.5/2:
                            #if sep < observatories['fov'][x]/2:
                                extra_matches.append({'event_id': event, 'obs_ID': observatories['ID'][x], 'galaxy_id': galaxy_list[z][0]})
                                print(z,sep,ephem.separation(star,extra))
                                y.append(z)
                    if len(y)>1:
                        print(y)
                        y.reverse()
                        for k in y:
                            del galaxy_list[k]
                            
                    # print(str(observatories['ID'][x]) + " " + observatories['name'][x].strip()[15:] + " at Lat:" +str(telescope.lat) + ",Lon:" + str(telescope.lon) + " gets galaxy " + str(galaxy_list[i][1]) + ' ra='+str(star.ra) + ' dec=' + str(star.dec) + ' alt='+str(star.alt))
                    del galaxy_list[i]
                    if plot_map:
                        plt.scatter(telescope.lon * 180 / np.pi, telescope.lat * 180 / np.pi, color='red',
                                    transform=ccrs.Geodetic())
                    break
            if len(extra_matches) > 0:
                extra_matches = pd.DataFrame(extra_matches)
                extra_matches.to_sql('matches_extra', sql_engine, if_exists='append', index=False)
        matches = pd.DataFrame(matches)
        matches.to_sql('matches', sql_engine, if_exists='append', index=False)
        event_log.close()
        if send_slack:
            if len(slackmsg) > 0:
                slack_client.chat_postMessage(channel=SLACK_CHANNEL, text=slackmsg)
                if galaxy_depleted:
                    text = "All" + str(len(banana_galaxies)) + " galaxies assigned"
                    query = "update events set assigned = " + str(len(banana_galaxies)) + ", possible = " + str(
                        len(banana_galaxies)) + " where ID = " + str(event)
                else:
                    text = str(len(banana_galaxies) - len(galaxy_list)) + " galaxies assigned out of " + str(
                        len(banana_galaxies))
                    query = "update events set assigned = " + str(
                        len(banana_galaxies) - len(galaxy_list)) + ", possible = " + str(
                        len(banana_galaxies)) + " where ID = " + str(event)
                    slack_client.chat_postMessage(channel=SLACK_CHANNEL, text=text)
                sql_engine.execute(query)
            else:
                slack_client.chat_postMessage(channel=SLACK_CHANNEL, text="No Galaxies Assigned")
        if plot_map:
            ax.add_feature(Nightshade(datetime.utcnow(), alpha=0.2))
            plt.title("Map of Observable Sites")
            plt.savefig("map.png")
            if send_slack:
                slack_client.files_upload(channels=SLACK_CHANNEL, file="map.png", title=params['GraceID'])
        filename = download_file(params['skymap_fits'], cache=True)
        skyplot([filename, '--annotate', '--geo', '--contour', '50', '90'])
        plt.savefig("hp.png")
        if send_slack:
            slack_client.files_upload(channels=SLACK_CHANNEL, file="hp.png", title=params['GraceID'])
        return


print("Starting Listener...")
if send_slack:
    slack_client.chat_postMessage(channel=SLACK_CHANNEL, text="Starting Listener...")

if test_alert:
    while True:
        print("starting test")
        import lxml.etree

        payload = open('MS181101ab-1-Preliminary.xml', 'rb').read()
        root = lxml.etree.fromstring(payload)
        process_gcn(payload, root)
        time.sleep(300)
gcn.listen(handler=process_gcn)

