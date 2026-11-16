import urllib.request
import json

url = 'http://127.0.0.1:8000/api/v1/temporal/discovery?ra=269.452083&dec=4.693333&fov=0.5'
req = urllib.request.Request(url)
res = urllib.request.urlopen(req)
data = json.loads(res.read().decode())
print('discovery_state:', data.get('discovery_state'))
print('temporal_coverage_status:', data.get('temporal_coverage_status'))
print('coverage_status:', data.get('coverage_status'))
print('total_observations_found:', data.get('total_observations_found'))
print('is_sufficient_for_differencing:', data.get('is_sufficient_for_differencing'))
for k, v in data.get('archive_queries', {}).items():
    print(f"  collection {k}: status={v.get('status')} msg={v.get('message')}")
