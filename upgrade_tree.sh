#! /bin/sh

find $1 -maxdepth 3  -mindepth 3 -type f -print0 | while IFS= read -r -d '' f; do
    md5sum "$f" | cut -d ' ' -f 1 >> "$f.md5";
done