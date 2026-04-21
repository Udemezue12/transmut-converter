class SerializeResponse:
    def get_list_dumps(self, paginated_props):
        return [p.model_dump() for p in paginated_props]

    def get_list_json_dumps(self, paginated_props):
        return [p.model_dump(mode="json") for p in paginated_props]

    def get_single_json_dumps(self, prop):
        return prop.model_dump(mode="json")
