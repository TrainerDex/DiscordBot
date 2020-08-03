class User:
    def __init__(self, conn, data):
        self.http = conn
        self._update(data)

    def _update(self, data):
        self.id = int(data.get("id"))
        self.username = data.get("username")
        self.first_name = data.get("first_name")
        self.old_id = int(data.get("trainer"))
