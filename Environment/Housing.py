class HousingUnit:
    def __init__(self, id, price, rent, location, size, bedrooms, bathrooms, type, quality):
        self.id = id
        self.price = price
        self.rent = rent
        self.location = location
        self.size = size
        self.bedrooms = bedrooms
        self.bathrooms = bathrooms
        self.type = type
        self.quality = quality
    def __repr__(self):
        return (f"HousingUnit(id={self.id}, price={self.price}, rent={self.rent}, "
                f"location='{self.location}', size={self.size}, bedrooms={self.bedrooms}, "
                f"bathrooms={self.bathrooms}, type='{self.type}', quality='{self.quality}')")

