import os
import sys
import ast

class ConfigObject:
    def __init__(self, config_dict):
        self.config = config_dict

    def get(self, section, key, default=None):
        if section not in self.config:
            return default
        sec_data = self.config[section]
        if isinstance(sec_data, dict):
            return sec_data.get(key, default)
        return default

    def __getitem__(self, key):
        return self.config.get(key)

    def __contains__(self, key):
        return key in self.config
    
    def get_global(self, key, default=None):
        return self.config.get(key, default)

def parse_value(value_str):
    value_str = value_str.strip()
    try:
        return ast.literal_eval(value_str)
    except (ValueError, SyntaxError):
        if '#' in value_str:
            value_str = value_str.split('#')[0].strip()
        return value_str.strip('"').strip("'")

def load_config(file_path):
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
            if buffer_line:
                print(f"[Warning] Incomplete line before new section: {buffer_line}")
                buffer_line = ""
            
            current_section = raw_line[1:].lower()
            
            if current_section not in config_data:
                config_data[current_section] = {}
            continue

        if not buffer_line:
            buffer_line = raw_line
        else:
            buffer_line += " " + raw_line

        if '=' in buffer_line:
            open_sq = buffer_line.count('[')
            close_sq = buffer_line.count(']')
            open_rd = buffer_line.count('(')
            close_rd = buffer_line.count(')')
            open_br = buffer_line.count('{')
            close_br = buffer_line.count('}')
            
            if open_sq == close_sq and open_rd == close_rd and open_br == close_br:
                try:
                    key_part, val_part = buffer_line.split('=', 1)
                    key = key_part.strip()
                    val = parse_value(val_part)
                    
                    if current_section:
                        config_data[current_section][key] = val
                    else:
                        config_data[key] = val

                    buffer_line = ""
                except Exception as e:
                    pass
            else:
                continue

    return ConfigObject(config_data)