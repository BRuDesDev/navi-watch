import click
from rich import print

@click.group()
def cli():
    print("[bold cyan]NÄVÎ: The Home Sentinel AI[/bold cyan]")

@cli.command()
def greet():
    print("Yes sir? Awaiting your command...")

@cli.command()
def wake():
    print("🎙️ Say 'Hey Navi' to wake...")
    from navi.modules.speech.wake_word import listen_for_wake_word
    listen_for_wake_word()
    print("Yes sir? 👂")