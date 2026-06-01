#!/bin/bash
# Creates the extension zip for Twitch upload
# Max size: 5MB uncompressed, all files must be relative paths

OUTPUT="extension-build.zip"
rm -f "$OUTPUT"

zip -r "$OUTPUT" \
  panel/ \
  obs/ \
  shared/ \
  data/ \
  assets/ \
  extension/ \
  --exclude "*.DS_Store" \
  --exclude "*/.gitkeep"

echo "Created $OUTPUT ($(du -sh $OUTPUT | cut -f1))"
