class publication:
    def __init__(self, pId, pAuthor,pAddress, pPrice,pDebut,pFin,pCity,pLocation,pImgUrl,pOpenPlace):
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

    def to_dict(self):
        return {'id':self.id , 'author': self.author_id, 'address': self.address,
                'price': self.price,'start': self.start, 'end': self.end,
                'city': self.city, 'location': self.location, 'img': self.img,
                'open_place': self.open_place}

    

