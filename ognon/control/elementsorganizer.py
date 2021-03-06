"""This module provide control functions to create, delete and move elements
into layers and layers into animation"""

import copy

from .. import model
from . import navigator
from . import change_project_state
from . import change_cursor_state

@change_project_state
@change_cursor_state
def add_element_after(cursor, element):
    """Add the passed element after the current frm."""
    i, _, _ = cursor.get_element_pos()
    cursor.get_layer().elements.insert(i+1, element)
    navigator.next_frm(cursor)

@change_project_state
def add_element_before(cursor, element):
    """Add the passed element before the current frm."""
    i, _, _ = cursor.get_element_pos()
    cursor.get_layer().elements.insert(i, element)

@change_project_state
@change_cursor_state
def add_cell_after(cursor):
    """Add a Cell after the current frm."""
    add_element_after(cursor, model.Cell())


@change_project_state
def add_cell_before(cursor):
    """Add a Cell before the current frm."""
    add_element_before(cursor, model.Cell())

@change_project_state
@change_cursor_state
def add_animref_after(cursor, name):
    """Add an AnimRef after the current frm."""
    add_element_after(cursor, model.AnimRef(name))

@change_project_state
def add_animref_before(cursor, name):
    """Add an AnimRef before the current frm."""
    add_element_before(cursor, model.AnimRef(name))

@change_project_state   
@change_cursor_state
def del_element(cursor):
    """Delete the current element."""
    i, _, _ = cursor.get_element_pos()
    cursor.get_layer().elements.pop(i)

@change_project_state
@change_cursor_state
def move_element_forward(cursor):
    """Move the current forward."""
    i, _, _ = cursor.get_element_pos()
    # TODO: cant a  `i, e, _ = ...` be better than _pop_element_at bellow ?
    if i < len(cursor.get_layer().elements)-1:
        cursor.get_layer().elements.insert(i+1, _pop_element_at(cursor, i))
        navigator.next_frm(cursor)

@change_project_state
@change_cursor_state
def move_element_backward(cursor):
    """Move the current backward."""
    i, _, _ = cursor.get_element_pos()
    if i>0:
        cursor.get_layer().elements.insert(i-1, _pop_element_at(cursor, i))
        navigator.prev_frm(cursor)

@change_project_state
@change_cursor_state
def copy_element(cursor):
    """Store a copy of the current element in the clipboard."""
    _, e, _ = cursor.get_element_pos()
    cursor.clipboard = copy.deepcopy(e)

@change_project_state
@change_cursor_state
def cut_element(cursor):
    """Pop the current element to the clipboard."""
    copy_element(cursor)
    del_element(cursor)

@change_project_state
@change_cursor_state
def paste_element(cursor):
    """Copy the content of the special clipboard."""
    if(cursor.clipboard):
        add_element_after(cursor, copy.deepcopy(cursor.clipboard))

@change_project_state
def duplicate_element(cursor):
    """Duplicate the current element."""
    _, e, _ = cursor.get_element_pos()
    add_element_after(cursor, copy.deepcopy(e))

    
def _pop_element_at(cursor, i):
    """Remove and return the element with the index i in the current layer."""
    return cursor.get_layer().elements.pop(i)
