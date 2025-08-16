"""
run_wake.py
-----------
Daemon loop for NÄVÎ that continuously listens for the wake word,
then processes a single wake/command/response cycle.
"""

import time
import traceback
from navi.modules.speech.wake_word import listen_for_wake_word

def main():
    print("[Daemon] NÄVÎ wake-word listener starting up...")
    while True:
        try:
            # This call will:
            #  - Listen for wake word
            #  - Play sir.mp3
            #  - Listen for command
            #  - Send to AI
            #  - Speak AI response
            listen_for_wake_word()

            # Small delay to prevent immediate retrigger
            time.sleep(0.4)

        except KeyboardInterrupt:
            print("[Daemon] Stopping on keyboard interrupt.")
            break
        except Exception:
            print("[Daemon] Unhandled error, retrying in 2s...")
            traceback.print_exc()
            time.sleep(2)

if __name__ == "__main__":
    main()
