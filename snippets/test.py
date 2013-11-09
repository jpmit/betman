class A(object):
    def __init__(self):
        self.speak()

    def speak(self):
        print "I am A"

class B(A):
    def __init__(self):
        super(B, self).__init__()

    def speak(self):
        print "I am B"
