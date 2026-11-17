import pytest
from backend.frame_codec import pack_frames, unpack_frames


def test_round_trip():
    frames = [b'\xff\xd8one\xff\xd9', b'\xff\xd8two\xff\xd9']
    assert unpack_frames(pack_frames(frames), expected=2) == frames


def test_rejects_wrong_magic():
    with pytest.raises(ValueError, match='Bad payload header'):
        unpack_frames(b'NOPE' + b'\x01\x00' + b'\x01\x00\x00\x00x', expected=1)


def test_rejects_payload_length_mismatch():
    with pytest.raises(ValueError, match='Payload length mismatch'):
        unpack_frames(pack_frames([b'abc']) + b'extra', expected=1)
