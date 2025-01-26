import json


class JSONParser:
    def __init__(self, json_data):
        """
        Initialize with parsed JSON data
        :param json_data: Python object (from json.loads() or json.load())
        """
        self.json_data = json_data
        self.result = {}
        self._parse_modules(self.json_data.get('Modules', []))

    def _parse_modules(self, modules):
        """Recursively process modules and submodules"""
        for module in modules:
            if not (title := module.get('Title')):
                continue

            # Collect valid identifiers from topics with TypeIdentifier == 'File'
            self.result[title] = [
                t['Identifier'] for t in module.get('Topics', [])
                if t.get('TypeIdentifier') == 'File' and 'Identifier' in t
            ]

            # Process nested modules
            if 'Modules' in module:
                self._parse_modules(module['Modules'])

    def get_dict(self):
        """Explicit method to get result dictionary"""
        return self.result

    @classmethod
    def from_string(cls, json_string):
        """Alternative constructor from JSON string"""
        return cls(json.loads(json_string))

    @classmethod
    def from_file(cls, file_path):
        """Alternative constructor from file path"""
        with open(file_path, 'r') as f:
            return cls(json.load(f))


# Example usage
if __name__ == "__main__":
    json_data = """<your JSON string here>"""
    parser = JSONParser.from_string(json_data)
    print(parser.get_dict())
