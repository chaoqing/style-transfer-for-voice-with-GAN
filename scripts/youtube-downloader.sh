#!/bin/bash

export https_proxy=http://localhost:8123 
OUTPUT=../data/youtube-video-info.json
touch ${OUTPUT}

while [ $(wc -l ${OUTPUT}|cut -d ' ' -f 1 ) -lt 600 ]; do
	now_pages=$(wc -l ${OUTPUT}|cut -d ' ' -f 1 )
	echo we got ${now_pages} pages already.
	youtube-dl -j --playlist-start  $((${now_pages}+1)) \
		'https://www.youtube.com/playlist?list=PL0eGJygpmOH5xQuy8fpaOvKrenoCsWrKh' >> ${OUTPUT}
	echo >> ${OUTPUT} # error happens, just skip this page
	sleep 10s
done
