import os

from twikit import Client


async def login(config) -> Client:
    cookies_file = os.path.join(config.output, "cookies.json")
    client = Client("en-US")

    if os.path.exists(cookies_file):
        print("Using saved session...")
        client.load_cookies(cookies_file)
    else:
        print("Logging in...")
        await client.login(
            auth_info_1=config.username,
            auth_info_2=config.email,
            password=config.password,
        )
        client.save_cookies(cookies_file)

    return client
