LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '(%(levelname)s) | %(name)s | [%(asctime)s]: '
                      'File %(pathname)s:%(lineno)s" - %(funcName)s() | %(message)s'
        },
        'additional_verbose': {
            'format': '\n\033[1;34m(%(levelname)s) | %(name)s | [%(asctime)s]:\n'
                      'File \033[3;38;5;226m"%(pathname)s:%(lineno)s"\033[23;38;5;87m - %(funcName)s()\n'
                      '\033[1;34mMessage \033[3;38;5;198m"%(message)s"\n\033[23;0;0m',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'additional_verbose',
        },
    },
    'loggers': {
        'aioagi': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'py.warnings': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'asyncio': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
    }
}
