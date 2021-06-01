#!/bin/bash

find ./ -name "*.flac" | while read f; do
    ffmpeg -i "$f" -acodec alac -vn "${f[@]/%flac/m4a}" < /dev/null;
    rm "${f}"
done
