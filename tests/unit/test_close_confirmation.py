import re
import unittest


def _load_confirm_close(fake_offer_save_before_discarding):
    import importlib.util
    spec= importlib.util.find_spec("graphenegui.logic.functionalities")
    with open(spec.origin) as f:
        src= f.read()
    start= src.index("def confirm_close")
    next_def= re.search(r"\ndef ", src[start+1:])
    end= start+1+next_def.start() if next_def else len(src)
    ns= {"offer_save_before_discarding": fake_offer_save_before_discarding}
    exec(src[start:end], ns)
    return ns["confirm_close"]


class FakeRecorder:
    def __init__(self, modified):
        self._modified= modified
    def is_modified(self):
        return self._modified


class FakeMainWindow:
    def __init__(self, modified):
        self.session_recorder= FakeRecorder(modified)


class TestConfirmClose(unittest.TestCase):
    def test_unmodified_session_closes_without_asking(self):
        calls= []
        confirm_close= _load_confirm_close(lambda mw: calls.append(mw) or True)
        mw= FakeMainWindow(modified=False)

        self.assertTrue(confirm_close(mw))
        self.assertEqual(calls, [], "no debería ni preguntar si no hay cambios sin guardar")

    def test_modified_session_delegates_to_offer_save(self):
        confirm_close= _load_confirm_close(lambda mw: True)
        mw= FakeMainWindow(modified=True)

        self.assertTrue(confirm_close(mw))

    def test_modified_session_cancel_aborts_close(self):
        confirm_close= _load_confirm_close(lambda mw: False)
        mw= FakeMainWindow(modified=True)

        self.assertFalse(confirm_close(mw))


if __name__ == "__main__":
    unittest.main()
