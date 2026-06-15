#!/usr/bin/env python3

import subprocess
import json
from typing import Optional, List, Dict

# Import kitty modules only when running as a kitten
try:
    from kitty.boss import Boss
    RUNNING_AS_KITTEN = True
except ImportError:
    # Running standalone (e.g., for testing)
    Boss = None
    RUNNING_AS_KITTEN = False

# fzf binary path - will be set during installation
FZF_BINARY_PATH = "/opt/homebrew/bin/fzf"
# op (1Password CLI) binary path - kittens run with a minimal PATH so we
# need the absolute path here.
OP_BINARY_PATH = "/opt/homebrew/bin/op"

def has_fzf() -> bool:
    """Check if fzf is available for fuzzy search"""
    result = subprocess.run(["which", "fzf"], capture_output=True)
    return result.returncode == 0


def authenticate() -> Optional[str]:
    """Authenticate with 1Password and return session token"""
    # Try to authenticate
    try:
        # First try biometric unlock if available
        result = subprocess.run([OP_BINARY_PATH, "signin", "--raw"], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            session_token = result.stdout.strip()
            # If we got a session token, return it
            if session_token:
                return session_token
            else:
                # App integration mode - no token returned, but authentication succeeded
                return "APP_INTEGRATION"  # Special marker for app integration
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
        pass
    
    # Fallback to interactive signin
    try:
        print("Please authenticate with 1Password...")
        # Run interactive signin with --raw, allow stdin but capture stdout
        result = subprocess.run([OP_BINARY_PATH, "signin", "--raw"], 
                              stdout=subprocess.PIPE, 
                              text=True)
        if result.returncode == 0:
            session_token = result.stdout.strip()
            if session_token:
                return session_token
            else:
                return "APP_INTEGRATION"
    except Exception:
        pass
    
    return None

def get_1password_items(session_token: str, query: str = "") -> List[Dict]:
    """Get items from 1Password with session token"""
    try:
        # Build command based on whether we have app integration or session token
        if session_token == "APP_INTEGRATION":
            cmd = [OP_BINARY_PATH, "item", "list", "--format=json"]
        else:
            cmd = [OP_BINARY_PATH, "item", "list", "--format=json", "--session", session_token]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        
        if result.returncode != 0:
            return []
        
        items = json.loads(result.stdout)
        
        # Filter by query if provided
        if query:
            query_lower = query.lower()
            filtered_items = []
            for item in items:
                title = item.get("title", "").lower()
                tags = " ".join(item.get("tags", [])).lower()
                category = item.get("category", "").lower()
                
                if (query_lower in title or 
                    query_lower in tags or 
                    query_lower in category):
                    filtered_items.append(item)
            return filtered_items
        
        return items
    except (json.JSONDecodeError, Exception):
        return []

def get_password_from_1password(session_token: str, item_id: str) -> Optional[str]:
    """Retrieve password from 1Password for a specific item"""
    try:
        # Build command based on whether we have app integration or session token
        if session_token == "APP_INTEGRATION":
            cmd = [OP_BINARY_PATH, "item", "get", item_id, "--fields=password", "--reveal"]
        else:
            cmd = [OP_BINARY_PATH, "item", "get", item_id, "--fields=password", "--reveal",
                   "--session", session_token]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def get_field_from_1password(session_token: str, item_ref: str, field: str = "password") -> Optional[str]:
    """Retrieve an arbitrary field for an item by title, UUID, or op:// reference."""
    try:
        # If the caller passed a full secret reference, use `op read` instead.
        if item_ref.startswith("op://"):
            if session_token == "APP_INTEGRATION":
                cmd = [OP_BINARY_PATH, "read", item_ref]
            else:
                cmd = [OP_BINARY_PATH, "read", item_ref, "--session", session_token]
        else:
            if session_token == "APP_INTEGRATION":
                cmd = [OP_BINARY_PATH, "item", "get", item_ref, f"--fields={field}", "--reveal"]
            else:
                cmd = [OP_BINARY_PATH, "item", "get", item_ref, f"--fields={field}", "--reveal",
                       "--session", session_token]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def fuzzy_select_item(items: List[Dict]) -> Optional[Dict]:
    """Use fzf for fuzzy selection of items"""
    if not items:
        return None
    
    return fuzzy_select_with_fzf(items)

def fuzzy_select_with_fzf(items: List[Dict]) -> Optional[Dict]:
    """Use fzf for interactive fuzzy selection"""
    # Prepare items for fzf
    fzf_input = []
    for i, item in enumerate(items):
        title = item.get("title", "Untitled")
        category = item.get("category", "Unknown")
        url = item.get("urls", [{}])[0].get("href", "") if item.get("urls") else ""
        
        display_line = f"{title} ({category})"
        if url:
            display_line += f" - {url}"
        
        fzf_input.append(f"{i}:{display_line}")
    
    try:
        # Determine fzf command
        fzf_cmd = FZF_BINARY_PATH if FZF_BINARY_PATH else "fzf"
        
        # Use subprocess.Popen to control stdin/stdout/stderr separately
        fzf_process = subprocess.Popen(
            [fzf_cmd, "--prompt=Select 1Password item: ", "--height=40%", "--reverse"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,  # Let stderr go to terminal
            text=True
        )
        
        stdout, _ = fzf_process.communicate("\n".join(fzf_input))
        
        if fzf_process.returncode == 0 and stdout.strip():
            # Extract index from fzf output
            selected_line = stdout.strip()
            index = int(selected_line.split(":", 1)[0])
            return items[index]
    except (subprocess.CalledProcessError, ValueError, IndexError):
        pass
    
    return None

def main(args: List[str]) -> str:
    """Main entry point for the kitten.

    Usage:
        kitten onepassword_kitten.py                 -> fuzzy-pick an item
        kitten onepassword_kitten.py <item>          -> paste that item directly
        kitten onepassword_kitten.py <item> <field>  -> paste a specific field

    <item> may be anything `op item get` accepts: title, UUID, or a
    secret reference like "op://Personal/GitHub/password".
    <field> defaults to "password".
    """
    # args[0] is the kitten script path, real args start at args[1:].
    # Strip flags (handled in handle_result) so they aren't treated as item refs.
    user_args = [a for a in args[1:] if a and not a.startswith("--")]

    # Authenticate
    session_token = authenticate()
    if not session_token:
        return "ERROR: Authentication failed"

    # Direct mode: an item was specified, skip the picker.
    if user_args:
        item_ref = user_args[0]
        field = user_args[1] if len(user_args) > 1 else "password"
        value = get_field_from_1password(session_token, item_ref, field)
        if value:
            return value
        return f"ERROR: Could not retrieve '{field}' for '{item_ref}'"

    # Picker mode (original behavior)
    items = get_1password_items(session_token)
    if not items:
        return "ERROR: No items found in 1Password"

    selected_item = fuzzy_select_item(items)
    if not selected_item:
        return "CANCELLED"

    password = get_password_from_1password(session_token, selected_item["id"])
    if password:
        return password
    else:
        return "ERROR: Could not retrieve password"

def handle_result(args: List[str], answer: str, target_window_id: int, boss: Boss) -> None:
    """Handle the result from main(). Default: copy to clipboard.
    Pass --paste as the first kitten arg to paste into the terminal instead.
    """
    if answer.startswith("ERROR:") or answer == "CANCELLED":
        print(f"\n{answer}")
        return

    # args[0] is the kitten script path; flags follow.
    paste_mode = "--paste" in args[1:]

    if paste_mode:
        w = boss.window_id_map.get(target_window_id)
        if w is not None:
            w.paste_text(answer)
        return

    # Clipboard mode (default): use kitty's clipboard API.
    try:
        boss.set_clipboard_string(answer)
    except Exception:
        # Fallback to pbcopy on macOS if the boss API is unavailable.
        try:
            subprocess.run(["pbcopy"], input=answer, text=True, check=False)
        except Exception:
            pass