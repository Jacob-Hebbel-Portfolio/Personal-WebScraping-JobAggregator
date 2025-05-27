import asyncio
import aiohttp
import requests
import proxyscrape

#1. create session

#2. fetch proxylist from proxifly

#3. test proxylist in batches (uses )

#4. write to data/proxies.txt

async def validationTask(proxy, session):
    # benchmark task for determining if a proxy is good / bad

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }

    try:
        async with session.get(
            "https://www.linkedin.com", 
            headers=headers, 
            proxy=f"{proxy}", 
            timeout=10
        ) as r:
            text = await r.text()
            if r.status == 200 and "LinkedIn" in text:
                return True
    except:
        return False
    
async def runTasksAsync(batch, session):
    # aggregates which proxies to test and
    # runs the validation task for each asynchronously

    goodProxies = []
    badProxies = []

    # collecting the tasks and executing them together
    tasks = [validationTask(proxy, session) for proxy in batch]
    results = await asyncio.gather(*tasks)

    # sorting the proxies based on their result
    for proxy, result in zip(batch, results):
        if result:
            print(f"found a good proxy: {proxy}")
            goodProxies.append(proxy)
        else:
            badProxies.append(proxy)

    return goodProxies, badProxies

async def main():

    session = aiohttp.ClientSession()
    url = "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt"
    response = requests.get(url)

    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch proxies: {response.status_code}")

    proxiflyProxies = [line.strip() for line in response.text.strip().splitlines() if line.strip()]

    untestedProxies = proxiflyProxies
    
    batches = [untestedProxies[i:i + 1000] for i in range(0, len(untestedProxies), 1000)]
    goodProxies = []
    badProxies = []
    for count, batch in enumerate(batches):
        print(f"sending batch {count+1}. {float((1+count)*100) / len(batches):.2f}% done")
        good, bad = await runTasksAsync(batch, session)
        goodProxies += good
        badProxies += bad
    await session.close()

    print(f"list fully parsed\nFound {len(goodProxies)} suitable proxies out of {len(untestedProxies)} options")
    try:
        with open('../data/proxies.txt', "r") as f:
            existingProxies = set(line.strip() for line in f if line.strip())
    except FileNotFoundError:
        existingProxies = set()

    existingProxies.update(goodProxies[:100])

    with open('../data/proxies.txt', "w") as f:
        for proxy in sorted(existingProxies):
            f.write(proxy + "\n")
    

if __name__ == '__main__':
    asyncio.run(main())

