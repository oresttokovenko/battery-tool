#ifndef SMC_WRAPPER_H
#define SMC_WRAPPER_H

int SmcReadKey(const char *key, char *value, int value_size);
int SmcWriteKey(const char *key, const char *value);

#endif
