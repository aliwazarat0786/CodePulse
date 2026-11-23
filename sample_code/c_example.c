#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void read_input() {
    char buffer[64];
    // Insecure gets allows buffer overflow
    gets(buffer);
    
    char dest[32];
    strcpy(dest, buffer);
    
    int* leak = (int*)malloc(sizeof(int) * 100);
    // Missing free(leak)
}

int main() {
    read_input();
    return 0;
}
