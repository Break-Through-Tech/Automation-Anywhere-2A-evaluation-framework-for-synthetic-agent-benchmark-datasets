import hashlib
import io
from pathlib import Path
import tarfile
import tempfile
import unittest

from difficulty.reproduce_clarified_design import restore, ROOT_FILES


class ArchiveSafetyTests(unittest.TestCase):
    def archive(self, root, extra=None):
        p=root/'archive.tar.gz'
        with tarfile.open(p,'w:gz') as t:
            for name in sorted(ROOT_FILES) + ([extra] if extra else []):
                item=tarfile.TarInfo(name);item.size=2;t.addfile(item,io.BytesIO(b'{}'))
        return p,hashlib.sha256(p.read_bytes()).hexdigest()

    def test_archive_hash_mismatch_prevents_any_restore(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p,_=self.archive(root)
            with self.assertRaisesRegex(ValueError,'hash'):restore(p,root/'out','wrong')
            self.assertFalse((root/'out').exists())

    def test_traversal_and_unexpected_files_are_rejected_before_writing(self):
        for name in ('../outside.json','.env','raw/../../outside.json'):
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);p,h=self.archive(root,name)
                with self.assertRaisesRegex(ValueError,'Unsafe'):restore(p,root/'out',h)
                self.assertFalse((root/'out').exists())


if __name__=='__main__':unittest.main()
