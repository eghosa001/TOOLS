"""Verify official Kraken Futures ETH open-interest history coverage before any model uses it."""
import json
import urllib.request
from datetime import datetime,timezone
url="https://futures.kraken.com/api/charts/v1/analytics/PF_ETHUSD/open-interest?interval=14400"
request=urllib.request.Request(url,headers={"User-Agent":"crypto-consensus-research/1.0"})
with urllib.request.urlopen(request,timeout=25) as response:
    data=json.load(response)
print("OPEN_INTEREST_RESPONSE_TYPE",type(data).__name__)
print("OPEN_INTEREST_KEYS",list(data)[:25] if isinstance(data,dict) else "list")
if isinstance(data,dict):
    for key,value in data.items():
        if isinstance(value,list):
            print("OPEN_INTEREST_ARRAY",key,len(value),str(value[:2])[:1600],str(value[-2:])[:1600])
        elif key not in ("candles","data"):
            print("OPEN_INTEREST_META",key,str(value)[:200])
elif isinstance(data,list):
    print("OPEN_INTEREST_ITEMS",len(data),str(data[:2])[:1800],str(data[-2:])[:1600])

r=data.get('result',{})
print('RESULT_FIELD_NAMES',list(r))
for k,v in r.items():
    print('RESULT_FIELD',k,'length',len(v) if isinstance(v,list) else 'other','first',str(v[:3])[:200] if isinstance(v,list) else str(v)[:100],'last',str(v[-3:])[:200] if isinstance(v,list) else '')
if r.get('timestamp'):
    print('START_TIME',datetime.fromtimestamp(r['timestamp'][0],timezone.utc).isoformat(),'END_TIME',datetime.fromtimestamp(r['timestamp'][-1],timezone.utc).isoformat())
