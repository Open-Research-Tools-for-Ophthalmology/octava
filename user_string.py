import os
import sys
from pathlib import Path
import platform
import ctypes

def hide_folder(path: Path):
    """Hide a folder cross-platform."""
    if platform.system() == "Windows":
        # Windows: set hidden attribute
        FILE_ATTRIBUTE_HIDDEN = 0x02
        ctypes.windll.kernel32.SetFileAttributesW(str(path), FILE_ATTRIBUTE_HIDDEN)
    elif platform.system() == "Darwin":
        # macOS: prepend '.' to hide folder (already done if folder starts with .)
        pass
    else:
        # Linux: prepend '.' to hide folder (already done if folder starts with .)
        pass

def user_string(string_name, new_string=None):
    """
    Get/set a user-specific string stored in a .txt file.

    Args:
        string_name (str): Name of the string (used as filename <string_name>.txt)
        new_string (str, optional): If provided, saves this string.

    Returns:
        tuple: (string_or_success, file_name)
            - If getting string: returns string stored in file
            - If setting string: returns True/False for success
            - file_name: path of the .txt file used
    """
    if not isinstance(string_name, str):
        raise ValueError("string_name must be a string.")

    fname = f"{string_name}.txt"

    # Determine current script folder
    try:
        script_folder = Path(__file__).parent
    except NameError:
        # If __file__ is not defined (interactive mode), use cwd
        script_folder = Path.cwd()

    ignore_dir = script_folder / ".ignore"
    file_name = ignore_dir / fname
    default_file_name = file_name

    # User preference folder fallback
    prefdir = Path.home() / ".user_strings"
    prefdir.mkdir(parents=True, exist_ok=True)

    if new_string is not None:
        # Set string
        if not isinstance(new_string, str):
            raise ValueError("new_string must be a string.")

        # Ensure save directory exists
        try:
            ignore_dir.mkdir(parents=True, exist_ok=True)
            hide_folder(ignore_dir)
        except Exception:
            return False, file_name

        # Write to file
        try:
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write(new_string)
        except Exception:
            # fallback to prefdir
            file_name = prefdir / fname
            try:
                with open(file_name, 'w', encoding='utf-8') as f:
                    f.write(new_string)
            except Exception:
                return False, default_file_name
        return True, file_name

    else:
        # Get string
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                result = f.readline().strip()
        except Exception:
            # fallback to prefdir
            file_name = prefdir / fname
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    result = f.readline().strip()
            except Exception:
                return '', default_file_name

        # If string looks like a path, ensure it exists
        if result and ("/" in result or "\\" in result):
            if not Path(result).exists():
                result = ''

        return result, file_name
