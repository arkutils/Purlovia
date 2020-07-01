/**
 * Hook to intercept log writes within ShooterGameServer and exit once it outputs a version string.
 *
 * To compile:
 * gcc utils/shootergameserver_fwrite_hook.c -o utils/shootergameserver_fwrite_hook.so -fPIC -shared -ldl
 *
 * To run:
 * LD_PRELOAD=/app/utils/shootergameserver_fwrite_hook.so livedata/game/ShooterGame/Binaries/Linux/ShooterGameServer
 *
 * Based on:
 *    [2020.03.25-12.28.34:781][  0]Log file open, 03/25/20 13:28:34
 *    [2020.03.25-12.28.34:781][  0]ARK Version: 307.6
 *    [2020.03.25-12.28.34:781][  0]PID: 179890
 */

#define _GNU_SOURCE 1
#include <dlfcn.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <signal.h>


static int _write_count = 0;
static bool _symbol_loaded_write = 0;
static bool _symbol_loaded_open = 0;
static ssize_t (*_real_write)(int fd, const char *buf, size_t count) = NULL;
static int (*_real_open)(const char *pathname, int mode) = NULL;

static bool _filter_writes = 0;
static const int WRITE_LIMIT = 30;
static const char *TEXT_TO_SEARCH_FOR = "ARK Version: ";
static const char *PATH_TO_INTERRUPT_ON = "game/ShooterGame/Content/PrimalEarth/CoreBlueprints/PrimalGlobalsBlueprint.uasset";


char *strnstr(const char *s1, const char *s2, size_t len)
{
    size_t l2;

    l2 = strlen(s2);
    if (!l2)
        return (char *)s1;
    while (len >= l2) {
        len--;
        if (!memcmp(s1, s2, l2))
            return (char *)s1;
        s1++;
    }
    return NULL;
}


ssize_t write(int fd, const char *buf, size_t count)
{
    if ( _symbol_loaded_write != 1 ) {
        _real_write = dlsym(RTLD_NEXT, "write");
        _symbol_loaded_write = 1;
    }

    /* Search for matching text */
    if (_filter_writes && count > 135 && count < 166)
    {
        const char *start = strnstr(buf, TEXT_TO_SEARCH_FOR, 166);
        if (start != NULL) {
            const char* end = strnstr(start, "\n", 32);
            if (end != NULL) {
                /* Print version to stdout */
                _real_write(1, start, end - start + 1);

                /* Exit with code 0x50 ('P') to signify successful capture to Purlovia */
                _Exit(0x50);
            }
        }
    }

    _write_count += 1;
    if (_write_count > WRITE_LIMIT) {
        /* Exit with 255 to indicate failure to Purlovia */
        _Exit(0xFF);
    }

    /* Skip the output for everything else */
    return count;
}


int open(const char *pathname, int mode)
{
    if ( _symbol_loaded_open != 1 ) {
        _real_open = dlsym(RTLD_NEXT, "open");
        _symbol_loaded_open = 1;
    }
    
    /* Search for matching text */
	const char *start = strnstr(pathname, PATH_TO_INTERRUPT_ON, 162);
	if (start != NULL) {
	    /* Send a keyboard interrupt signal to self, so UE can flush the log buffer */
	    _filter_writes = true;
	    kill(getpid(), SIGINT);
	}
	
	/* Continue as normal */
	return _real_open(pathname, mode);
}
