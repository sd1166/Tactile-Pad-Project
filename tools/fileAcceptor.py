class FileAcceptor:

    def __init__(self, accepted_extensions):
        self.accepted_extensions = accepted_extensions
        

    def accept(self, file_path):
        extension = file_path.split('.')[-1].lower()
        return extension in self.accepted_extensions
    
