from lump.multithreading import MultiThread, multithreadedmethod


def test_multithreadedmethod():
    class A:
        @multithreadedmethod()
        def test(self, *args, **kwargs):
            pass

        def get_multithread(self):
            return self.test._multithread

    b = A()
    assert type(b.test._multithread) is MultiThread
    assert type(b.get_multithread()) is MultiThread
