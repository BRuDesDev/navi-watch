#!/bin/bash

bashrc_location="$HOME/.bashrc"
if [ -f "$bashrc_location" ]; then
    echo "source $HOME/.navi/navi.sh" >> "$bashrc_location"
    echo "Navi Shorts setup complete. Please restart your terminal or run 'source $HOME/.bashrc' to apply changes."
else
    echo "Error: .bashrc file not found at $bashrc_location. Please check your home directory."
fi

# Setup system wide Alias commands
alias activate='source .venv/bin/activate && echo "Virtual environment activated."'
alias daemon-reload='sudo systemctl --user daemon-reload'
alias pull='git pull && echo "Repositories updated."'
alias push='git add . && git commit -m "Update" && git push && echo "Changes pushed to remote repository."'
alias install-reqs='pip install -r requirements.txt && echo "Dependencies installed."'

# Setup Navi Alias commands

alias navi='navi-wake && echo "Navi service started."'

alias get_navi_logs='journalctl --user -u navi-wake -f && echo "Retrieving Navi service logs..."'

alias restart_navi_service='sudo systemctl --user restart navi-wake && echo "Restarting Navi service..."'
alias enable_navi_service='sudo systemctl --user enable navi-wake && echo "Enabling Navi service..."'
alias start_navi_service='sudo systemctl --user start navi-wake && echo "Starting Navi service..."'
alias stop_navi_service='sudo systemctl --user stop navi-wake && echo "Stopping Navi service..."'
alias cat_navi_service='sudo systemctl --user cat navi-wake && echo "Pulling Navi service file..."'
alias status_navi_service='sudo systemctl --user status navi-wake --no-pager && echo "Checking status of Navi service..."'
alias disable_navi_service='sudo systemctl --user disable navi-wake && echo "Disabling Navi service..."'

alias remove_navi_cache='sudo rm -f assets/tts_cache/* && echo "Cleaning out Navi cache..."'

alias edit_navi_config='sudo nano ~/.config/navi/navi.env && echo "Editing Navi configuration..."'
alias edit_navi_service='sudo nano /etc/systemd/user/navi-wake.service && echo "Editing Navi service file..."'
