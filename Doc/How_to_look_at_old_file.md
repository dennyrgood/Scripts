## Backup an Old Version of `dms_summarize.py` from Git

```sh
cd /Users/dennishmathes/Documents/MyWebsiteGIT/Scripts && \
git show 5976f81:dms_summarize.py > dms_summarize.py.backup.from-commit-5976f81 && \
ls -lh dms_summarize.py* && \
echo "✓ Backed up old version as dms_summarize.py.backup.from-commit-5976f81"

