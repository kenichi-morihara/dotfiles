#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DOTFILES_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Recursively link files into a target directory (merge, do not replace the directory).
# Needed for Omarchy-managed dirs like ~/.config/hypr and ~/.config/omarchy.
link_config_tree() {
    local source="$1"
    local target="$2"

    if [ -d "$source" ]; then
        mkdir -p "$target"
        local child
        for child in "$source"/*; do
            [ -e "$child" ] || continue
            link_config_tree "$child" "$target/$(basename "$child")"
        done
    elif [ -f "$source" ]; then
        ln -fnsv "$source" "$target"
    fi
}

# Link .zshrc from .bin/common/ to home directory
if [ -f "${SCRIPT_DIR}/common/.zshrc" ]; then
    ln -fnsv "${SCRIPT_DIR}/common/.zshrc" "$HOME/.zshrc"
fi

# Link .config directory files (excluding OS-specific directories)
if [ -d "${DOTFILES_DIR}/.config" ]; then
    CONFIG_SOURCE_DIR="${DOTFILES_DIR}/.config"
    mkdir -p "$HOME/.config"
    
    for config_item in "${CONFIG_SOURCE_DIR}"/*; do
        # Skip OS-specific directories (macos, linux, windows)
        config_name=$(basename "$config_item")
        if [[ "$config_name" == "macos" ]] || [[ "$config_name" == "linux" ]] || [[ "$config_name" == "windows" ]]; then
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
                    [ -e "$config_item" ] || continue
                    config_name=$(basename "$config_item")
                    target_path="$HOME/.config/$config_name"
                    if [ -d "$config_item" ]; then
                        link_config_tree "$config_item" "$target_path"
                    elif [ -f "$config_item" ]; then
                        ln -fnsv "$config_item" "$target_path"
                    fi
                done
            fi
            ;;
        Linux)
            if [ -d "${CONFIG_SOURCE_DIR}/linux" ]; then
                for config_item in "${CONFIG_SOURCE_DIR}/linux"/*; do
                    [ -e "$config_item" ] || continue
                    config_name=$(basename "$config_item")
                    target_path="$HOME/.config/$config_name"
                    if [ -d "$config_item" ]; then
                        link_config_tree "$config_item" "$target_path"
                    elif [ -f "$config_item" ]; then
                        ln -fnsv "$config_item" "$target_path"
                    fi
                done
            fi
            ;;
        MINGW*|MSYS*|CYGWIN*)
            if [ -d "${CONFIG_SOURCE_DIR}/windows" ]; then
                link_config_tree "${CONFIG_SOURCE_DIR}/windows" "$HOME/.config/windows"
            fi
            ;;
    esac
fi

# Link .tool-versions to home directory
if [ -f "${DOTFILES_DIR}/.tool-versions" ]; then
    ln -fnsv "${DOTFILES_DIR}/.tool-versions" "$HOME/.tool-versions"
fi

# Link Cursor user rules into ~/.cursor/rules (merge; do not replace ~/.cursor)
# Cursor loads user file rules from ~/.cursor/rules/*.mdc across all projects.
if [ -d "${DOTFILES_DIR}/.cursor/rules" ]; then
    link_config_tree "${DOTFILES_DIR}/.cursor/rules" "$HOME/.cursor/rules"
fi
