class classproperty(object):
    def __init__(self, fget):
        self.fget = fget

    def __get__(self, obj, obj_type):
        return self.fget(obj_type)
