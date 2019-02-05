from .. import view
import json

def test_get_path(cursor):
	import os
	path = view.get_path(cursor)
	assert path
	assert view.get_path(cursor, 'foo').startswith(path)

	# test jsonability
	json.dumps(view.get_path(cursor))

def test_get_projects_tree(cursor):
	# WARNING: weak test
	
	# test jsonability
	json.dumps(view.get_projects_tree(cursor))

def test_get_anims(cursor):	
	for a in view.get_anims(cursor):
		assert a in cursor.proj.anims
		
	# test jsonability
	json.dumps(view.get_anims(cursor))

def test_get_playing(cursor):
	assert isinstance(view.get_playing(cursor), bool)
	# test jsonability
	json.dumps(view.get_playing(cursor))

def test_get_timeline(cursor):
	
	assert 'len' in view.get_timeline(cursor)
	assert len(view.get_timeline(cursor)['layers']) == len(cursor.get_anim().layers)

	# test jsonability
	json.dumps(view.get_timeline(cursor))

def test_get_cursor_infos(cursor):
	
	for key in ('project_name', 'playing', 'loop', 'anim', 'frm', 'layer'):
		assert key in view.get_cursor_infos(cursor)	
	# test jsonability
	json.dumps(view.get_cursor_infos(cursor))

def test_get_lines(cursor):
	from ..control import drawer
	line = [0,0,10,10,0,10]
	drawer.draw(cursor, line)
	assert line in view.get_lines(cursor)

	cursor.set_pos(anim='testing-anim-with-animref',frm=5)
	view.get_lines(cursor)
	
	# test jsonability
	json.dumps(view.get_lines(cursor))

def test_get_onion_skin(cursor):
	from ..control import drawer
	drawer.draw(cursor, [1,2,3,4])
	assert 1 in view.get_onion_skin(cursor, onion_range=(-1,0,1))
	assert -2 in view.get_onion_skin(cursor, onion_range=(-2,-1,0,1,2))
	assert view.get_onion_skin(cursor, onion_range=(0,))[0] == view.get_lines(cursor)
	# test jsonability
	json.dumps(view.get_onion_skin(cursor))
