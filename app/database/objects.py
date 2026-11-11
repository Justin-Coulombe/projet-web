class publication:
    def __init__(self, pId, pAuthor, pAddress, pPrice, pCity,
                 pLocation, pImgUrl, pPlaceTotal, pBanni = False,
                 pLatitude=None, pLongitude=None):
        self.id = pId
        self.author_id = pAuthor
        self.address = pAddress
        self.price = pPrice
        self.city = pCity
        self.location = pLocation
        self.img = pImgUrl
        self.placeTotal = pPlaceTotal
        self.banni = pBanni
        self.latitude = pLatitude
        self.longitude = pLongitude

    def to_dict(self):
        return {
            'id': self.id, 'author': self.author_id,
            'address': self.address, 'price': self.price,
            'city': self.city, 'location': self.location,
            'img': self.img, 'place_total': self.placeTotal,
            'banni' : self.banni,'latitude': self.latitude,
            'longitude': self.longitude
        }


class reservation:
    def __init__(self, pId, pClient, pDebut, pFin, pPublication):
        self.id = pId
        self.author_id = pClient
        self.start = pDebut
        self.end = pFin
        self.post = pPublication

    def to_dict(self):
        return {
            'id': self.id, 'author': self.author_id,
            'start': self.start, 'end': self.end, 'post': self.post
        }
