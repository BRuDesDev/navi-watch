# navi/cli.py
import click
from rich import print

@click.group()
def cli():
    print("[bold cyan]NÄVÎ: The Home Sentinel AI[/bold cyan]")

@cli.command()
@click.argument("text", nargs=-1)
def say(text):
    """Speak a sentence with Amazon Polly."""
    from navi.modules.speech.tts import speak
    msg = " ".join(text) or "Hello from Olivia. This is a test."
    speak(msg)

# existing greet/wake commands...
if __name__ == "__main__":
    cli()
