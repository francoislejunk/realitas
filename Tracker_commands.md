LLM Context Generation: tracker.get_context_for_llm() provides historical context
Resume Capability: Load any previous session with tracker.load_session()


 File "C:\Users\darre\OneDrive\Desktop\Realitas Neo\main.py", line 828, in <module>
    'original_value': original_status,

  File "C:\Users\darre\OneDrive\Desktop\Realitas Neo\main.py", line 448, in main
    final_narrative=final_narrative,
    ^^^^^^^^^^^^^
  File "C:\Users\darre\OneDrive\Desktop\Realitas Neo\agents\tracker_agent.py", line 167, in end_session
    self._save_session_data()
    ~~~~~~~~~~~~~~~~~~~~~~~^^
  File "C:\Users\darre\OneDrive\Desktop\Realitas Neo\agents\tracker_agent.py", line 557, in _save_session_data
    json.dump(self.session_data, f, indent=2, ensure_ascii=False)
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\darre\AppData\Local\Programs\Python\Python313\Lib\json\__init__.py", line 179, in dump
    for chunk in iterable:
                 ^^^^^^^^
  File "C:\Users\darre\AppData\Local\Programs\Python\Python313\Lib\json\encoder.py", line 432, in _iterencode
    yield from _iterencode_dict(o, _current_indent_level)
  File "C:\Users\darre\AppData\Local\Programs\Python\Python313\Lib\json\encoder.py", line 406, in _iterencode_dict
    yield from chunks
  File "C:\Users\darre\AppData\Local\Programs\Python\Python313\Lib\json\encoder.py", line 406, in _iterencode_dict
    yield from chunks
  File "C:\Users\darre\AppData\Local\Programs\Python\Python313\Lib\json\encoder.py", line 326, in _iterencode_list
    yield from chunks
  File "C:\Users\darre\AppData\Local\Programs\Python\Python313\Lib\json\encoder.py", line 406, in _iterencode_dict
    yield from chunks
  File "C:\Users\darre\AppData\Local\Programs\Python\Python313\Lib\json\encoder.py", line 406, in _iterencode_dict
    yield from chunks
  File "C:\Users\darre\AppData\Local\Programs\Python\Python313\Lib\json\encoder.py", line 406, in _iterencode_dict
    yield from chunks
  File "C:\Users\darre\AppData\Local\Programs\Python\Python313\Lib\json\encoder.py", line 439, in _iterencode
    o = _default(o)
  File "C:\Users\darre\AppData\Local\Programs\Python\Python313\Lib\json\encoder.py", line 180, in default
    raise TypeError(f'Object of type {o.__class__.__name__} '
                    f'is not JSON serializable')
TypeError: Object of type SFactors is not JSON serializable

I got this after doing ctrl+c to end the simulation