class publication:
    def __init__(self, pId, pAuthor,pAddress, pPrice,pDebut,pFin,pCity,pLocation,pImgUrl,pOpenPlace,pPlaceUse,pUse):
        self.id = pId
        self.author_id = pAuthor
        self.address = pAddress
        self.price = pPrice
        self.start = pDebut
        self.end = pFin
        self.city = pCity
        self.location = pLocation
        self.img = pImgUrl
        self.open_place = pOpenPlace
        self.place_use = pPlaceUse
        self.use = pUse

    def to_dict(self):
        return {'id':self.id , 'author': self.author_id, 'address': self.address,
                'price': self.price,'start': self.start, 'end': self.end,
                'city': self.city, 'location': self.location, 'img': self.img,
                'open_place': self.open_place,'place_use':self.place_use,'open':self.use}


class reservation:
    def __init__(self, pId, pClient,pDebut,pFin,pPublication):
        self.id = pId
        self.author_id = pClient
        self.start = pDebut
        self.end = pFin
        self.post = pPublication

    def to_dict(self):
        return {'id':self.id , 'author': self.author_id,'start': self.start, 'end': self.end,
                'post': self.post}


