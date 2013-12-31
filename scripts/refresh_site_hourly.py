import requests
import datetime

r = requests.get('http://www.diseasegraph.com')
if r.status_code == 200:
    print 'refreshed site at ' + str(datetime.datetime.utcnow())
else:
    print 'error refreshing site.'