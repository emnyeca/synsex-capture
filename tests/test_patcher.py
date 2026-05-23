from pathlib import Path

import pytest

from digitone_syx_toolkit.errors import SyxFileError
from digitone_syx_toolkit.patcher import BytePatch, apply_byte_patches, load_patches_yaml


def test_apply_byte_patches_success():
    data = bytes([0xF0, 0x10, 0x20, 0xF7])
    patched = apply_byte_patches(data, [BytePatch(offset=2, value=0x33, before=0x20)])
    assert patched == bytes([0xF0, 0x10, 0x33, 0xF7])


def test_apply_byte_patches_before_check_failure():
    data = bytes([0xF0, 0x10, 0x20, 0xF7])
    with pytest.raises(SyxFileError):
        apply_byte_patches(data, [BytePatch(offset=2, value=0x33, before=0x21)], strict_before=True)


def test_load_patches_yaml(tmp_path: Path):
    yaml_path = tmp_path / "patches.yaml"
    yaml_path.write_text(
        "patches:\n"
        "  - offset: 2\n"
        "    before: 0x20\n"
        "    value: 0x33\n",
        encoding="utf-8",
    )

    patches = load_patches_yaml(yaml_path)
    assert len(patches) == 1
    assert patches[0].offset == 2
    assert patches[0].before == 0x20
    assert patches[0].value == 0x33
