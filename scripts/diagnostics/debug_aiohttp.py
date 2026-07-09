
print("Start import aiohttp")
try:
    import aiohttp
    print("Success import aiohttp")
    print("Version:", aiohttp.__version__)
except Exception as e:
    print("Failed:", e)
