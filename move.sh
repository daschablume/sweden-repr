#!/bin/bash

BASE_PATH="../data"
TXT_FILE=$BASE_PATH/$1
DEST_DIR=$BASE_PATH/$2


mkdir -p "$DEST_DIR"

while IFS= read -r line; do
    filename=$(echo "$line" | tr '/' '_')
    # Copy file with modified name
    cp "$BASE_PATH/$line" "$DEST_DIR/$filename"
done < "$TXT_FILE"
