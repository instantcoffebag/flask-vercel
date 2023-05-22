class User:
    def __init__(self, name, email, password, rooms):
        self.name = name
        self.email = email
        self.password = password
        self.rooms = rooms

    def __str__(self):
        res = f"{self.name},{self.email},{self.password},"
        res += str(len(self.rooms))
        try:
            namelist = list(self.rooms.keys())
        except AttributeError:
            res = ',' + res + ',' + '[]' + ',' + '[]'
            return res
        idlist = list(self.rooms.values())
        for name in range(len(namelist)):
            res += "," + namelist[name] + "," + idlist[name]
        return res
