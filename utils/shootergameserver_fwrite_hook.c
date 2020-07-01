/**
 * Hook to intercept log writes within ShooterGameServer and exit once it outputs a version string.
 *
 * To compile:
 * gcc utils/shootergameserver_fwrite_hook.c -o utils/shootergameserver_fwrite_hook.so -fPIC -shared -ldl -Wall
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
#include <string.h>
#include <signal.h>
#include <sys/types.h>


#define WRITE_LIMIT 30
#define TEXT_TO_SEARCH_FOR "ARK Version: "
#define PATH_TO_INTERRUPT_ON "game/ShooterGame/Content/PrimalEarth/CoreBlueprints/PrimalGlobalsBlueprint.uasset"

static int (*__purlovia__real_open)(const char *pathname, int mode) = NULL;
static ssize_t (*__purlovia__real_write)(int fd, const char *buf, size_t count) = NULL;

static int __purlovia__write_count = 0;
static bool __purlovia__symbols_loaded = 0;
static bool __purlovia__monitor_writes = 0;

/* Avoid including unistd.h as it overlaps with our hook definitions */
extern pid_t getpid(void);


void __purlovia__ensure_symbols()
{
    if (!__purlovia__symbols_loaded)
    {
        __purlovia__real_open = dlsym(RTLD_NEXT, "open");
        __purlovia__real_write = dlsym(RTLD_NEXT, "write");

        __purlovia__symbols_loaded = 1;
    }
}


char *__purlovia__strnstr(const char *s1, const char *s2, size_t len)
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
    __purlovia__ensure_symbols();

    /* Search for matching text */
    if (__purlovia__monitor_writes)
    {
        if (count > 135 && count < 166)
        {
            const char *start = __purlovia__strnstr(buf, TEXT_TO_SEARCH_FOR, 166);
            if (start != NULL) {
                const char* end = __purlovia__strnstr(start, "\n", 32);
                if (end != NULL) {
                    /* Print version to stdout */
                    __purlovia__real_write(1, start, end - start + 1);

                    /* Exit with code 0x50 ('P') to signify successful capture to Purlovia */
                    _Exit(0x50);
                }
            }
        }

        /* Bail after a fixed number of monitored writes without match */
        __purlovia__write_count += 1;
        if (__purlovia__write_count > WRITE_LIMIT) {
            /* Exit with 255 to indicate failure to Purlovia */
            _Exit(0xFF);
        }
    }

    /* Skip the output for everything else */
    return count;
}


int open(const char *pathname, int mode)
{
    __purlovia__ensure_symbols();

    /* Search for matching text */
	const char *start = __purlovia__strnstr(pathname, PATH_TO_INTERRUPT_ON, 162);
	if (start != NULL) {
	    /* Send a keyboard interrupt signal to self, so UE can flush the log buffer */
	    __purlovia__monitor_writes = true;
	    kill(getpid(), SIGINT);
	}

	/* Continue as normal */
	return __purlovia__real_open(pathname, mode);
}
