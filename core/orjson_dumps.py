import orjson


class OrjsonDumps:

    def dumps(self,value):
        data = orjson.dumps(value).decode()
        return data

    def loads(self, value):
        data = orjson.loads(value)
        return data


orjson_repo = OrjsonDumps()