import os

from twikit import Client

from scraper.cookies import load_browser_cookies


async def login(config) -> Client:
    cookies_file = os.path.join(config.output, "cookies.json")
    client = Client("en-US")

    if os.path.exists(cookies_file):
        print("Using saved session...")
        client.load_cookies(cookies_file)
    elif config.cookies:
        print("Importing browser cookies...")
        cookies = load_browser_cookies(config.cookies)
        client.set_cookies(cookies)
        client.save_cookies(cookies_file)
    else:
        print("Logging in...")
        await client.login(
            auth_info_1=config.username,
            auth_info_2=config.email,
            password=config.password,
        )
        client.save_cookies(cookies_file)

    return client
