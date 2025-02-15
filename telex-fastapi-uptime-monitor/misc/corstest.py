import httpx

def check_cors_headers(url, origin):
    headers = {
        "Origin": origin,
        "Access-Control-Request-Method": "GET",
    }

    with httpx.Client() as client:
        response = client.options(url, headers=headers)
        if "access-control-allow-origin" in response.headers.keys():
            print(f"{url} allowed cors for {origin}")
        else:
            print(f"{url} did not allow cors for {origin}")

check_cors_headers("https://profanity-checker-omega.vercel.app/api/integration", "https://telex.im")
check_cors_headers("https://profanity-checker-omega.vercel.app/api/integration", "https://telexlove.im")
