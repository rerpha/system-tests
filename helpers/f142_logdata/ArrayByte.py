# automatically generated by the FlatBuffers compiler, do not modify

# namespace:

import flatbuffers


class ArrayByte(object):
    __slots__ = ["_tab"]

    @classmethod
    def GetRootAsArrayByte(cls, buf, offset):
        n = flatbuffers.encode.Get(flatbuffers.packer.uoffset, buf, offset)
        x = ArrayByte()
        x.Init(buf, n + offset)
        return x

    # ArrayByte
    def Init(self, buf, pos):
        self._tab = flatbuffers.table.Table(buf, pos)

    # ArrayByte
    def Value(self, j):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            a = self._tab.Vector(o)
            return self._tab.Get(
                flatbuffers.number_types.Int8Flags,
                a + flatbuffers.number_types.UOffsetTFlags.py_type(j * 1),
            )
        return 0

    # ArrayByte
    def ValueLength(self):
        o = flatbuffers.number_types.UOffsetTFlags.py_type(self._tab.Offset(4))
        if o != 0:
            return self._tab.VectorLen(o)
        return 0


def ArrayByteStart(builder):
    builder.StartObject(1)


def ArrayByteAddValue(builder, value):
    builder.PrependUOffsetTRelativeSlot(
        0, flatbuffers.number_types.UOffsetTFlags.py_type(value), 0
    )


def ArrayByteStartValueVector(builder, numElems):
    return builder.StartVector(1, numElems, 1)


def ArrayByteEnd(builder):
    return builder.EndObject()
