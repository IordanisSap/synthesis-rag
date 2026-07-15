import tomllib

def parse(path):
    with open(path, "rb") as f:
        data = tomllib.load(f)
        return data