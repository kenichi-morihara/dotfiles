#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DOTFILES_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Link .zshrc from .bin/common/ to home directory
if [ -f "${SCRIPT_DIR}/common/.zshrc" ]; then
    ln -fnsv "${SCRIPT_DIR}/common/.zshrc" "$HOME/.zshrc"
fi

# Link .config directory files (excluding OS-specific directories)
if [ -d "${DOTFILES_DIR}/.config" ]; then
    CONFIG_SOURCE_DIR="${DOTFILES_DIR}/.config"
    mkdir -p "$HOME/.config"
    
    for config_item in "${CONFIG_SOURCE_DIR}"/*; do
        # Skip OS-specific directories (macos, linux)
        config_name=$(basename "$config_item")
        if [[ "$config_name" == "macos" ]] || [[ "$config_name" == "linux" ]]; then
            continue
        fi
        
        if [ -d "$config_item" ]; then
            target_dir="$HOME/.config/$config_name"
            ln -fnsv "$config_item" "$target_dir"
        elif [ -f "$config_item" ]; then
            target_file="$HOME/.config/$config_name"
            ln -fnsv "$config_item" "$target_file"
        fi
    done
    
    # Link OS-specific config directories
    case "$(uname -s)" in
        Darwin)
            if [ -d "${CONFIG_SOURCE_DIR}/macos" ]; then
                for config_item in "${CONFIG_SOURCE_DIR}/macos"/*; do
                    if [ -d "$config_item" ] || [ -f "$config_item" ]; then
                        config_name=$(basename "$config_item")
                        target_path="$HOME/.config/$config_name"
                        ln -fnsv "$config_item" "$target_path"
                    fi
                done
            fi
            ;;
        Linux)
            if [ -d "${CONFIG_SOURCE_DIR}/linux" ]; then
                for config_item in "${CONFIG_SOURCE_DIR}/linux"/*; do
                    if [ -d "$config_item" ] || [ -f "$config_item" ]; then
                        config_name=$(basename "$config_item")
                        target_path="$HOME/.config/$config_name"
                        ln -fnsv "$config_item" "$target_path"
                    fi
                done
            fi
            ;;
    esac
fi
