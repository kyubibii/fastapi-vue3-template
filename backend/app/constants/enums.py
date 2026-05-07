import enum


class GenderEnum(enum.StrEnum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNDISCLOSED = "undisclosed"


class UserTagStatusEnum(int, enum.Enum):
    EXPIRED = -1
    PENDING = 0
    ACTIVE = 1
