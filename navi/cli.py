import click
from rich import print

@click.group()
def cli():
    print("[bold cyan]NÄVÎ: The Home Sentinel AI[/bold cyan]")

@cli.command()
def wake():
    """Listen once for wake word -> command -> respond, then exit."""
    from navi.modules.speech.wake_word import listen_for_wake_word
    listen_for_wake_word()

@cli.command()
@click.argument("text", nargs=-1)
def say(text):
    """Speak a sentence using TTS (Polly)."""
    from navi.modules.speech.tts import speak
    msg = " ".join(text) or "Hello. This is a test."
    speak(msg)

@cli.command()
def daemon():
    """Run the wake-word loop forever (service mode)."""
    from navi.services.run_wake import main
    main()

if __name__ == "__main__":
    cli()
