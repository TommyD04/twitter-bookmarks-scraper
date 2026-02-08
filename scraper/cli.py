import argparse
import getpass
from dataclasses import dataclass


@dataclass
class Config:
    output: str
    username: str
    email: str
    password: str


def parse_args(args=None) -> Config:
    parser = argparse.ArgumentParser(description="Scrape Twitter bookmarks")
    parser.add_argument("--output", required=True, help="Destination folder path")
    parser.add_argument("--username", help="Twitter username")
    parser.add_argument("--email", help="Twitter email")
    parser.add_argument("--password", help="Twitter password")

    parsed = parser.parse_args(args)

    username = parsed.username or input("Twitter username: ")
    email = parsed.email or input("Twitter email: ")
    password = parsed.password or getpass.getpass("Twitter password: ")

    return Config(
        output=parsed.output,
        username=username,
        email=email,
        password=password,
    )
