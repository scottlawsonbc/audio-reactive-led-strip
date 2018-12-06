class Effect(object):
    """
    Base class for effects

    Effects have a number of input channels and a number of output channels.
    Before each processing the effect is updated.

    Input values can be accessed by self._inputBuffer[channelNumber], output values
    are to be written into self_outputBuffer[channelNumber].
    """
    def __init__(self):
        self.__initstate__()

    def __initstate__(self):
        self._t = 0.0
        try:
            self._inputBuffer
        except AttributeError:
            self._inputBuffer = None
        try:
            self._outputBuffer
        except AttributeError:
            self._outputBuffer = None

    def numOutputChannels(self):
        """
        Returns the number of output channels for this effect
        """
        raise NotImplementedError('numOutputChannels() was not implemented')

    def numInputChannels(self):
        """
        Returns the number of input channels for this effect.
        """
        raise NotImplementedError('numInputChannels() was not implemented')

    def setOutputBuffer(self,buffer):
        """
        Set output buffer where processed data is to be written
        """
        self._outputBuffer = buffer

    def setInputBuffer(self, buffer):
        """
        Set input buffer for incoming data
        """
        self._inputBuffer = buffer

    def process(self):
        """
        The main processing function:
        - Read input data from self._inputBuffer
        - Process data
        - Write output data to self._outputBuffer
        """
        raise NotImplementedError('process() was not implemented')

    async def update(self, dt):
        """
        Update timing, can be used to precalculate stuff that doesn't depend on input values
        """
        self._t += dt

    def __cleanState__(self, stateDict):
        """
        Cleans given state dictionary from state objects beginning with __
        """
        for k in list(stateDict.keys()):
            if k.startswith('_'):
                stateDict.pop(k)
        return stateDict

    def __getstate__(self):
        """
        Default implementation of __getstate__ that deletes buffer, call __cleanState__ when overloading
        """
        state = self.__dict__.copy()
        self.__cleanState__(state)
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.__initstate__()

    def updateParameter(self, stateDict):
        self.__setstate__(stateDict)

    def getParameter(self):
        return {}

    @staticmethod
    def getParameterDefinition():
        return {}

    def _inputBufferValid(self, index):
        if self._inputBuffer is None:
            return False
        if len(self._inputBuffer) <= index:
            return False
        if self._inputBuffer[index] is None:
            return False
        return True

