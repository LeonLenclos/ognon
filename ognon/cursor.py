"""
This module defines the Cursor class.
The cursor is the most importants object of the ognon's structure.
It is a required argument for every control and view functions.
"""

from . import model
from . import tags

class NoProjectError(AttributeError):
    """
    This exception will be raised if a cursor action require a poject. And no
    one is selected."""
    pass

class Cursor():
    """
    A Cursor is a point of view on an ognon project, a *tape head*.

    It store informations about his position and his state and a reference to
    the project. It provides a bunch of getters and setters to move the cursor,
    know where it is and access to the ellements under it.

    Attributes:
    
    - `proj` : a model.Project instance.
    - `_pos` : a dict that store the cursor position.
        - `_pos['anim']` : The name of an animation in the project anims dict.
        - `_pos['layer']` : The index of a layer in the animation layers list.
        - `_pos['frm']` : A specific instant of the animation.
    - `playing` : The cursor state (playing or not playing)

    """

    def __init__(self, proj=None):
        """
        Init a cursor with an optional ognon project.
        """
        self._proj = proj
        self._pos = {
            'anim':'master',
            'layer':0,
            'frm':0,
        }
        self.playing = False

    @property
    def proj(self):
        if not self._proj:
            raise NoProjectError
        return self._proj
    
    @proj.setter
    def proj(self, value):
        self._proj = value
    
    def get_pos(self, key=None):
        """
        Get the cursor position.

        If a key is passed, return the specified position ('anim', 'layer' or
        'frm'). 
        This method first call set_pos without arguments to ensure that the
        position is valid (e.g. not pointing an inexisting layer)
        """
        self.set_pos()
        if key:
            return self._pos[key]
        return self._pos

    def set_pos(self, anim=None, layer=None, frm=None):
        """
        Set the cursor position. (anim, layer and frm)

        Positions are constrained to valid values : frm is constained using the
        constrain_frm method, anim is set to 'masster' if current value refer
        to an unexisting animation and layer is set to 0 if the current value is
        an out of range index.

        If the anim argument is passed but layer or frm are not, set them to 0.

        If no arguments are passed, just constain the three values.

        If no project, raise a NoProjectError
        """

        # Ok, I think all the  exception for inapropriate requests can be raised
        # From this method. (not sure)


        # Set position.
        if anim is not None:
            self._pos['anim'] = anim
            self._pos['layer'] = 0
            self._pos['frm'] = 0
        if layer is not None:
            self._pos['layer'] = layer
        if frm is not None:
            self._pos['frm'] = frm
        # try:
        if self._pos['anim'] not in self.proj.anims:
            self._pos['anim'] = 'master'
        # except AttributeError:
            # raise NoProjectError()
        # Constrain layer.
        if self._pos['layer'] >= len(self.proj.anims[self._pos['anim']].layers) \
        or self._pos['layer']  < 0:
            self._pos['layer'] = 0   
        # Constrain frm.
        self._pos['frm'] = self.constrain_frm(self._pos['frm'])

    def constrain_frm(self, frm):
        """
        Return a frm position constrained in the current anim length.

        Result will be different depending on whether the loop mode is on or off.
        """
        if self.proj.config['play']['loop']:
            return frm % self.anim_len()
        if frm <= 0:
            return 0
        if frm >= self.anim_len():
            return self.anim_len() - 1
        return frm

    def get_anim(self, anim=None):
        """
        Return the current anim or the specified anim
        """
        anim = anim or self.get_pos('anim')
        return self.proj.anims[anim]

    def get_layer(self, anim=None, layer=None):
        """
        Return the current layer or the specified layer in the specified anim
        """
        layer = layer if layer is not None else self.get_pos('layer')
        return self.get_anim(anim).layers[layer]

    def get_element_pos(self, anim=None, layer=None, frm=None):
        """
        Return a tuple with the index of the element in the layer, the
        element object and the position of the cursor inside the element
        Return None if no element.
        """
        layer = self.get_layer(anim, layer)
        frm = frm if frm is not None else self.get_pos('frm') #2
        frm_ = 0#0 #1 #3
        for i, e in enumerate(layer.elements):
            length = self.element_len(e)
            frm_ += length
            if frm_ > frm:
                at = frm-frm_+length
                for tag in e.tags:
                    at = tags.calculate_inside_pos(
                        at, self.element_len(e, True), tag)
                return i, e, at


    def get_element(self, anim=None, layer=None, frm=None):
        """
        Return the current element or the element on the specified frm in the
        specified layer in the specified anim
        """
        return self.get_element_pos(anim, layer, frm)[1]

    def anim_len(self, anim=None):
        """
        Return the length of the current anim or specified anim
        """
        anim = anim if anim else self._pos['anim']
        layer_len = lambda layer : sum(map(self.element_len, layer.elements))
        return layer_len(max(self.get_anim(anim).layers, key=layer_len))

    def element_len(self, elmt, ignonre_tags=False):
        """
        Return the length of the given element
        """
        if isinstance(elmt, model.Cell):
            length =  1
        elif isinstance(elmt, model.AnimRef):
            length = self.anim_len(elmt.name)
        else:
            raise TypeError('Unknow element type')
        if ignonre_tags:
            return length
        for tag in elmt.tags:
            length = tags.calculate_len(length, tag)
        return length