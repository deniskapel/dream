from enum import Enum, auto


class State(Enum):
    USR_START = auto()
    #
    SYS_TELL_FACT = auto()
    USR_TELL_FACT = auto()
    #
    SYS_MORE_DETAILED = auto()
    USR_MORE_DETAILED = auto()
    #
    SYS_FACTOID_Q = auto()
    USR_FACTOID_Q = auto()
    #
    SYS_START_TALK = auto()
    USR_START_TALK = auto()
    #
    SYS_ERR = auto()
    USR_ERR = auto()