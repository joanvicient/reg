import pickle
import os
import logging

logger = logging.getLogger(__name__)

class AutoSaveDict(dict):
    def __init__(self):
        if os.path.isdir('/data') and os.access('/data', os.W_OK):
            self.file_name = '/data/autosave.pickle'
        elif os.access('.', os.W_OK):
            self.file_name = 'autosave.pickle'
        else:
            self.file_name = '/tmp/autosave.pickle'

        logger.info(f"Using autosave file {self.file_name}")
        super().update(self.load_dict())

    def load_dict(self):
        """Loads the dictionary from a file if it exists."""
        if os.path.exists(self.file_name):
            with open(self.file_name, 'rb') as file:
                return pickle.load(file)
        return {}

    def save_dict(self):
        """Saves the dictionary to a file."""
        with open(self.file_name, 'wb') as file:
            pickle.dump(dict(self), file)

    def __setitem__(self, key, value):
        """Set a dictionary item and automatically save it."""
        super().__setitem__(key, value)
        self.save_dict()

    def __delitem__(self, key):
        """Delete a dictionary item and automatically save it."""
        super().__delitem__(key)
        self.save_dict()


if __name__ == '__main__':
    d = AutoSaveDict()
    d['a'] = 1
    d['b'] = 2
    print(d)
    print(d.file_name)