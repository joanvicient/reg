import pickle
import os
import logging

logger = logging.getLogger(__name__)

class AutoSaveDict:
    def __init__(self):
        if os.path.isdir('/data') and os.access('/data', os.W_OK):
            self.file_name = '/data/autosave.pickle'
        elif os.access('.', os.W_OK):
            self.file_name = 'autosave.pickle'
        else:
            self.file_name = '/tmp/autosave.pickle'

        logger.debug(f"Using autosave file {self.file_name}")
        self.data = self.load_dict()

    def load_dict(self):
        """Loads the dictionary from a file if it exists."""
        if os.path.exists(self.file_name):
            with open(self.file_name, 'rb') as file:
                return pickle.load(file)
        return {}

    def save_dict(self):
        """Saves the dictionary to a file."""
        with open(self.file_name, 'wb') as file:
            pickle.dump(self.data, file)

    def __setitem__(self, key, value):
        """Set a dictionary item and automatically save it."""
        self.data[key] = value
        self.save_dict()

    def __getitem__(self, key):
        """Retrieve a dictionary item."""
        return self.data[key]

    def __delitem__(self, key):
        """Delete a dictionary item and automatically save it."""
        del self.data[key]
        self.save_dict()

    def __contains__(self, key):
        """Check if a key is in the dictionary."""
        return key in self.data

    def __repr__(self):
        """Return the string representation of the dictionary."""
        return repr(self.data)
    
    def __str__(self) -> str:
        """Return the string representation of the dictionary."""
        return str(self.data)

    def to_dict(self):
        return self.data

if __name__ == '__main__':
    d = AutoSaveDict()
    d['a'] = 1
    d['b'] = 2
    print(d)
    print(d.file_name)