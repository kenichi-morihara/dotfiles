#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Link dotfiles in .bin directory to home directory
for dotfile in "${SCRIPT_DIR}"/.??* ; do
    [[ "$dotfile" == "${SCRIPT_DIR}/.git" ]] && continue
    [[ "$dotfile" == "${SCRIPT_DIR}/.github" ]] && continue
    [[ "$dotfile" == "${SCRIPT_DIR}/.DS_Store" ]] && continue

    ln -fnsv "$dotfile" "$HOME"
done

# Link .config directory files
if [ -d "${SCRIPT_DIR}/../.config" ]; then
    CONFIG_SOURCE_DIR="$(cd "${SCRIPT_DIR}/../.config" && pwd)"
    for config_dir in "${CONFIG_SOURCE_DIR}"/*; do
        if [ -d "$config_dir" ]; then
            config_name=$(basename "$config_dir")
            target_dir="$HOME/.config/$config_name"
            mkdir -p "$HOME/.config"
            ln -fnsv "$config_dir" "$target_dir"
        elif [ -f "$config_dir" ]; then
            config_name=$(basename "$config_dir")
            target_file="$HOME/.config/$config_name"
            mkdir -p "$HOME/.config"
            ln -fnsv "$config_dir" "$target_file"
        fi
    done
fi
