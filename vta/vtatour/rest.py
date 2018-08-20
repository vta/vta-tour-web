import requests

url = "https://vtavirtualtransit-7c904.firebaseapp.com/api/route-details/low-resolution/201/b/front"

 


payload = "{\n  \"videoUrl\":\"201/Mon_Jul_16_04:40:04_PDT_2018_201_b_Low_Development_forward.mp4\",\n  \"KmlUrl\":\"201/Mon_Jul_16_04:40:04_PDT_2018_201_b_Low_Development_forward.kml\"\n}"

{'apikey': 'X+eH>F>9Kvb897h`', 'content-type': 'application/json', 'cache-control': 'no-cache'}

headers = {
    'content-type': "application/json",
    'cache-control': "no-cache",
    'apikey': "X+eH>F>9Kvb897h`"
    }
print payload
response = requests.request("POST", url, data=payload, headers=headers)
print "PAYLOAD :\n"
print payload
print "\nRESPONSE :\n"
print(response.text)


 
