CC = gcc
CFLAGS = -Wall -Wextra -O2 -I libAeon
LIBS = -lm

all: aeon_demo

aeon_demo: libAeon/demo.c libAeon/libAeon.c
	$(CC) $(CFLAGS) -o aeon_demo libAeon/demo.c libAeon/libAeon.c $(LIBS)

test:
	$(CC) $(CFLAGS) -o test_core tests/test_core.c libAeon/libAeon.c $(LIBS)
	./test_core

clean:
	rm -f aeon_demo test_core
