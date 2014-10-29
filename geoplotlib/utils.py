from collections import defaultdict
import csv
from datetime import datetime
import json
from math import radians, cos, sin, asin, sqrt
import urllib2
import numpy as np


def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    m = 6367000 * c
    return m


class DataAccessObject():

    def __init__(self, dict):
        self.dict = dict


    @staticmethod
    def from_dataframe(df):
        return DataAccessObject({col: df[col].values for col in df.columns})


    def __getitem__(self, key):
        return self.dict[key]


    def __setitem__(self, key, value):
        assert type(value) == np.ndarray
        self.dict[key] = value


    def __delitem__(self, key):
        del self.dict[key]


    def rename(self, mapping):
        for old_key, new_key in mapping:
            self.dict[new_key] = self.dict[old_key]
            del self.dict[old_key]


    def where(self, mask):
        assert len(mask) == len(self)
        return DataAccessObject({k: self.dict[k][mask] for k in self.dict})


    def groupby(self, field1, field2=None):
        if field2 is None:
            uniquevalues = list(set(self.dict[field1]))
            return [(v, self.where(self.dict[field1] == v)) for v in uniquevalues]
        else:
            uniquevalues = set([tuple(row) for row in np.vstack([self.dict[field1],self.dict[field2]]).T])
            return [((v1,v2), self.where((self.dict[field1] == v1) & (self.dict[field2] == v2))) \
                    for v1,v2 in uniquevalues]


    def head(self, n):
        return DataAccessObject({k: self.dict[k][:n] for k in self.dict})


    def keys(self):
        return self.dict.keys()


    def values(self):
        return self.dict.values()


    def __str__(self):
        return 'DataAccessObject(%s x %d)' % (str(self.dict.keys()), len(self))


    def __repr__(self):
        return self.__str__()


    def __len__(self):
        return len(self.dict.values()[0])


def read_csv(fname):
    values = defaultdict(list)
    with open(fname) as f:
        reader = csv.DictReader(f)
        for row in reader:
            for (k,v) in row.items():
                values[k].append(v)
    npvalues = {k: np.array(values[k]) for k in values.keys()}
    for k in npvalues.keys():
        for datatype in [np.int, np.float]:
            try:
                npvalues[k][:1].astype(datatype)
                npvalues[k] = npvalues[k].astype(datatype)
                break
            except:
                pass
    dao = DataAccessObject(npvalues)
    return dao


def epoch_to_str(epoch, fmt='%Y-%m-%d %H:%M:%S'):
    return datetime.fromtimestamp(epoch).strftime(fmt)


def parse_raw_str(v):
    try:
        v = v.decode('utf-8')
    except:
        try:
            v = v.decode('latin1')
        except:
            pass
    return v


class BoundingBox():

    def __init__(self, north, west, south, east):
        self.north = north
        self.west = west
        self.south = south
        self.east = east


    @staticmethod
    def from_points(lons, lats):
        north, west = max(lats), min(lons)
        south, east = min(lats), max(lons)
        return BoundingBox(north=north, west=west, south=south, east=east)


    @staticmethod
    def from_bboxes(bboxes):
        north = max([b.north for b in bboxes])
        south = min([b.south for b in bboxes])
        west = min([b.west for b in bboxes])
        east = max([b.east for b in bboxes])
        return BoundingBox(north=north, west=west, south=south, east=east)


    def __str__(self):
        return 'BoundingBox(north=%.6f, west=%.6f, south=%.6f, east=%.6f)' % (self.north, self.west, self.south, self.east)


    @staticmethod
    def from_nominatim(query):
        url = urllib2.urlopen('http://nominatim.openstreetmap.org/search.php?q=%s&format=json' % query)
        jo = json.load(url)

        if len(jo) == 0:
            raise Exception('No results found')

        south, north, west, east = map(float, jo[0]['boundingbox'])
        print 'bbox from Nominatim:', south, north, west, east
        return BoundingBox(north=north, west=west, south=south, east=east)


BoundingBox.WORLD = BoundingBox(north=85, west=-170, south=-85, east=190)
BoundingBox.DK = BoundingBox(north=57.769, west=7.932, south=54.444, east=12.843)
BoundingBox.DTU = BoundingBox(north=55.7925, west=12.5092, south=55.7784, east=12.5309)
BoundingBox.KBH = BoundingBox(north=55.8190, west=12.0369, south=55.5582, east=12.7002)