import os
import sys
import ast

class ConfigObject:
    def __init__(self, config_dict):
        self.config = config_dict

    def get(self, section, key, default=None):
        if section not in self.config:
            return default
        return self.config[section].get(key, default)

def parse_value(value_str):
    value_str = value_str.strip()
    try:
        return ast.literal_eval(value_str)
    except (ValueError, SyntaxError):
        if '#' in value_str:
            value_str = value_str.split('#')[0].strip()
        return value_str.strip('"').strip("'")

def load_config(file_path):
    """
    &section_name
    key = value
    """
    if not os.path.exists(file_path):
        print(f"Error: Config file '{file_path}' not found.")
        sys.exit(1)

    config_data = {}
    current_section = None

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    buffer_line = ""

    for line in lines:
        raw_line = line.strip()
        
        if not raw_line or raw_line.startswith('#'):
            continue

        if raw_line.startswith('&'):
            current_section = raw_line[1:].lower()
            config_data[current_section] = {}
            continue

        if '=' in raw_line:
            buffer_line = raw_line
        else:
            if buffer_line:
                buffer_line += " " + raw_line

        if buffer_line and '=' in buffer_line:
            open_sq = buffer_line.count('[')
            close_sq = buffer_line.count(']')
            open_rd = buffer_line.count('(')
            close_rd = buffer_line.count(')')
            
            if open_sq == close_sq and open_rd == close_rd:
                try:
                    key_part, val_part = buffer_line.split('=', 1)
                    key = key_part.strip()
                    val = parse_value(val_part)
                    
                    if current_section:
                        config_data[current_section][key] = val
                    else:
                        pass
                    
                    buffer_line = ""
                except Exception as e:
                    print(f"Warning: Failed to parse line: {buffer_line}\nError: {e}")
            else:
                continue

    return ConfigObject(config_data)
