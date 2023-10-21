

def compose(f, g):
    def composed(*args, **kwargs):
        return f(g(*args, **kwargs))
    return composed