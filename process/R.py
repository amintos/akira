class R(object):
    def __init__(self, reducedRepresentation):
        self.reducedRepresentation = reducedRepresentation
    def __reduce__(self):
        return self.reducedRepresentation
    def __call__(self):
        raise NotImplementedError('this should never be called')

