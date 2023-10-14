class SenderNotFound(Exception):
    def __init__(self):
        super().__init__("Sender is not found!")
