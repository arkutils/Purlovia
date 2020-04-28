#define _GNU_SOURCE 1
#include <dlfcn.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>

static bool _symbol_loaded = 0;
static ssize_t (*_real_write)(int fd, const char *buf, size_t count) = NULL;

static const char *TEXT_TO_SEARCH_FOR = "ARK Version: ";
static const char *EXTRA_DISPLAYED = "xxx.xx";

ssize_t write(int fd, const char *buf, size_t count)
{
	if ( _symbol_loaded != 1 ) {
		_real_write = dlsym(RTLD_NEXT, "write");
	}
	
	/* Based on:
	     [2020.03.25-12.28.34:781][  0]Log file open, 03/25/20 13:28:34
	     [2020.03.25-12.28.34:781][  0]ARK Version: 307.6
	     [2020.03.25-12.28.34:781][  0]PID: 179890
        */

	/* Filtering */
	if ( count < 166 && count > 31 )
	{
		const char *found = strstr(buf, TEXT_TO_SEARCH_FOR);
		if (found != NULL) {
			// Print message to stdout and exit with code 0x50 ('P')
			_real_write(1, found, strlen(TEXT_TO_SEARCH_FOR) + strlen(EXTRA_DISPLAYED));
			_Exit(0x50);
		}
	}

	return _real_write(fd, buf, count);
}
