import sys

class ConfigParser:
    def __init__(self, input_file):
        self.config = {
            'cell': {},
            'dft': {},
            'analyze': {},
            'submit': {},
            'collect': {}
        }
        self._parse(input_file)

    def _parse(self, filename):
        try:
            with open(filename, 'r') as f:
                lines = f.readlines()
        except FileNotFoundError:
            print(f"Error: INPUT file '{filename}' not found.")
            sys.exit(1)

        current_section = None
        section_code_blocks = {}

        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'): continue
            
            if line.startswith('&'):
                current_section = line[1:].lower()
                if current_section not in section_code_blocks:
                    section_code_blocks[current_section] = ""
            elif current_section:
                section_code_blocks[current_section] += line + "\n"

        for section, code_block in section_code_blocks.items():
            if section not in self.config:
                self.config[section] = {}

            local_scope = {}
            try:
                exec(code_block, {}, local_scope)
                for key, value in local_scope.items():
                    if not key.startswith('__'):
                        self.config[section][key] = value
            except Exception as e:
                print(f"Warning: Failed to parse section '&{section}'\nError: {e}")

    def get(self, section, key, default=None):
        return self.config.get(section, {}).get(key, default)