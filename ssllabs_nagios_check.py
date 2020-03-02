#!/usr/bin/env python

import requests
import time
import sys
import logging

API = 'https://api.ssllabs.com/api/v3/'


def requestAPI(path, payload={}):
    '''This is a helper method that takes the path to the relevant
        API call and the user-defined payload and requests the
        data/server test from Qualys SSL Labs.

        Returns JSON formatted data'''

    url = API + path

    try:
        response = requests.get(url, params=payload)
    except requests.exception.RequestException:
        logging.exception('Request failed.')
        sys.exit(1)

    data = response.json()
    return data


def resultsFromCache(host, publish='off', startNew='off', fromCache='on', all='done'):
    path = 'analyze'
    payload = {
                'host': host,
                'publish': publish,
                'startNew': startNew,
                'fromCache': fromCache,
                'all': all
              }
    data = requestAPI(path, payload)
    return data


def newScan(host, publish='off', startNew='on', all='done', ignoreMismatch='on'):
    path = 'analyze'
    payload = {
                'host': host,
                'publish': publish,
                'startNew': startNew,
                'all': all,
                'ignoreMismatch': ignoreMismatch
              }
    results = requestAPI(path, payload)

    payload.pop('startNew')

    while results['status'] != 'READY' and results['status'] != 'ERROR':
        time.sleep(30)
        results = requestAPI(path, payload)

    return results

def main(argv):
    servername = argv[:1].pop()
    data = resultsFromCache(servername)
    exitcode = 0

    if 'status' in data:
        if data['status'] not in {'READY', 'ERROR'}:
            print("[%s] processing result..." % (servername))
        if data['status'] == 'ERROR':
            print("[%s] got an error: %s" % (servername, data['statusMessage']))
            exitcode = 3
        elif data['status'] == 'READY':
            for e in data['endpoints']:
                if 'statusMessage' in e and e['statusMessage'] == 'Ready':
                    print("%s [%s]: Grade %s" % (servername, e['ipAddress'], e['grade']))

                    if 'hasWarnings' in e and e['hasWarnings'] and exitcode == 0:
                        exitcode = 1
                    elif 'grade' in e and e['grade'] in {'B', 'T', 'F'}:
                        exitcode = 2
                else:
                    print("%s [%s]: %s" % (servername, e['ipAddress'], e['statusMessage']))
                    exitcode = 2
        else:
            print(data)

    print("Exit Code: %d" % exitcode)

    sys.exit(exitcode)

if __name__ == '__main__':
    main(sys.argv[1:])
