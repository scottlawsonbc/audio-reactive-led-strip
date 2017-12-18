from PyQt5 import QtCore, QtGui, QtWidgets

__all__ = ['QFloatSlider']


class QFloatSlider(QtWidgets.QSlider):
    """
    Subclass of QtWidgets.QSlider
    Horizontal slider giving floating point values.
    Usage: QFloatSlider(min, max, step, default)
    where min = minimum value of slider
          max = maximum value of slider
          step = interval between values. Must be a factor of (max-min)
          default = default (starting) value of slider
    """ 
    def __init__(self, min_value, max_value, step, default):
        super().__init__(QtCore.Qt.Horizontal)
        self.precision = 0.001
        self.min_value = min_value
        self.max_value = max_value
        self.step = step
        self.default = default
        self.quotient, self.remainder = self._float_divmod(\
                             self.max_value-self.min_value, self.step)
        if self.remainder:
            raise ValueError("{} does not fit evenly between {} and {}"\
                             .format(step, min_value, max_value))
        super().setMinimum(0)
        super().setMaximum(self.quotient)
        super().setSingleStep(1)
        super().setValue(self._float_to_int(self.default))
        super().valueChanged.connect(self._value_handler)
        self.slider_value = 2.0
        
    # This is mostly disgusting python i hate floating points >:(        
    def _float_divmod(self,a,b):
        """
        Basically the divmod function but it works for floats (try 0.3 % 0.1 smh)
        Returns the quotient, and a remainder.
        """
        a = abs(a)
        b = abs(b)
        n = 1
        while True:
            c = a - b
            c = abs(c)
            if c < self.precision:
                return (n, 0)
            elif c > a:
                return (n-1, a)
            a = c
            n += 1

    def _float_to_int(self, a):
        return int(round(a/self.step))

    def _int_to_float(self, a):
        return self.min_value+a*self.step
        
    def _value_handler(self):
        self.slider_value = self._int_to_float(super().value())
